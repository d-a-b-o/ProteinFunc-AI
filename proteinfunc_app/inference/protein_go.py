"""Modelos y contrato de inferencia GO compartidos por Kaggle y escritorio."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWYXBZOUJ"
AA_TO_ID = {aa: i + 1 for i, aa in enumerate(AMINO_ACIDS)}
ASPECTS = {"molecular_function": "MF", "biological_process": "BP", "cellular_component": "CC"}
GO_ROOTS = {"GO:0003674", "GO:0008150", "GO:0005575"}


def normalize_sequence(sequence: str) -> str:
    sequence = re.sub(r"\s+", "", sequence).upper()
    if sequence.endswith("*"):
        sequence = sequence[:-1]
    if not sequence:
        raise ValueError("La secuencia está vacía.")
    invalid = sorted(set(sequence) - set(AMINO_ACIDS))
    if invalid:
        raise ValueError(f"Caracteres no válidos en la proteína: {invalid}")
    return sequence


def protein_id(header: str) -> str:
    first = header.split()[0]
    fields = first.split("|")
    return fields[1] if len(fields) >= 3 and fields[0] in {"sp", "tr"} else first


def iter_fasta(lines):
    """Lee FASTA en streaming; no carga el superset completo en memoria."""
    header, chunks = None, []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                yield protein_id(header), normalize_sequence("".join(chunks))
            header, chunks = line[1:].strip(), []
            if not header:
                raise ValueError("Cabecera FASTA vacía.")
        else:
            if header is None:
                raise ValueError("FASTA inválido: falta la cabecera >identificador.")
            chunks.append(line)
    if header is not None:
        yield protein_id(header), normalize_sequence("".join(chunks))


def parse_input(text: str):
    if not text.strip():
        raise ValueError("El input está vacío.")
    if text.lstrip().startswith(">"):
        records = list(iter_fasta(text.splitlines()))
    else:
        records = [("query_1", normalize_sequence(text))]
    ids = [x[0] for x in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Los identificadores FASTA deben ser únicos.")
    return records


def read_ontology(path):
    """Solo relaciones is_a y part_of de términos activos de GO."""
    terms, aliases, current = {}, {}, None

    def commit():
        if current and current.get("id") and not current.get("obsolete"):
            terms[current["id"]] = {
                "name": current.get("name", ""),
                "aspect": ASPECTS.get(current.get("namespace"), ""),
                "parents": current.get("parents", []),
            }
            for alt in current.get("alts", []):
                aliases[alt] = current["id"]

    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line.startswith("["):
                commit()
                current = {} if line == "[Term]" else None
            elif current is not None:
                if line.startswith("id: "):
                    current["id"] = line[4:]
                elif line.startswith("name: "):
                    current["name"] = line[6:]
                elif line.startswith("namespace: "):
                    current["namespace"] = line[11:]
                elif line.startswith("alt_id: "):
                    current.setdefault("alts", []).append(line[8:])
                elif line.startswith("is_a: "):
                    current.setdefault("parents", []).append(line[6:].split()[0])
                elif line.startswith("relationship: part_of "):
                    current.setdefault("parents", []).append(line.split()[2])
                elif line == "is_obsolete: true":
                    current["obsolete"] = True
    commit()
    if not terms:
        raise ValueError(f"No se encontraron términos GO en {path}")
    return terms, aliases


def ancestor_lookup(ontology):
    cache = {}

    def ancestors(term, visiting=None):
        if term in cache:
            return cache[term]
        visiting = set() if visiting is None else visiting
        if term in visiting:
            raise ValueError(f"Ciclo en la ontología: {term}")
        result = set()
        for parent in ontology.get(term, {}).get("parents", []):
            if parent in ontology:
                result.add(parent)
                result.update(ancestors(parent, visiting | {term}))
        cache[term] = result
        return result

    return ancestors


def make_label_metadata(classes, ontology):
    ancestors = ancestor_lookup(ontology)
    selected = set(classes)
    return {
        term: {"name": ontology[term]["name"], "aspect": ontology[term]["aspect"],
               "ancestors": sorted(ancestors(term) & selected)}
        for term in classes
    }


def propagate_scores(scores, classes, metadata):
    """Un ancestro seleccionado recibe al menos el puntaje de su descendiente."""
    result = np.array(scores, dtype=np.float32, copy=True)
    index = {term: i for i, term in enumerate(classes)}
    for j, term in enumerate(classes):
        for parent in metadata[term]["ancestors"]:
            i = index[parent]
            result[:, i] = np.maximum(result[:, i], scores[:, j])
    return result


def masked_pool(hidden, mask):
    mask = mask.bool()
    mean = (hidden * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True).clamp_min(1)
    maximum = hidden.masked_fill(~mask.unsqueeze(-1), torch.finfo(hidden.dtype).min).max(1).values
    return torch.cat([mean, maximum], dim=-1)


class ProtCNN(nn.Module):
    def __init__(self, n_labels, spec):
        super().__init__()
        dim, channels = spec.get("embedding_dim", 64), spec.get("channels", 64)
        self.embedding = nn.Embedding(len(AA_TO_ID) + 1, dim, padding_idx=0)
        self.convs = nn.ModuleList([nn.Conv1d(dim, channels, k, padding=k // 2) for k in (3, 5, 7)])
        self.head = nn.Sequential(nn.Dropout(0.3), nn.Linear(channels * 6, n_labels))

    def forward(self, input_ids, attention_mask, **kwargs):
        embedded = self.embedding(input_ids).transpose(1, 2)
        features = torch.cat([torch.relu(conv(embedded)) for conv in self.convs], dim=1)
        return self.head(masked_pool(features.transpose(1, 2), attention_mask))


class BiLSTMAttention(nn.Module):
    def __init__(self, n_labels, spec):
        super().__init__()
        dim, hidden = spec.get("embedding_dim", 64), spec.get("hidden_dim", 64)
        self.embedding = nn.Embedding(len(AA_TO_ID) + 1, dim, padding_idx=0)
        self.lstm = nn.LSTM(dim, hidden, batch_first=True, bidirectional=True)
        self.attention = nn.MultiheadAttention(hidden * 2, 4, dropout=0.1, batch_first=True)
        self.norm = nn.LayerNorm(hidden * 2)
        self.head = nn.Sequential(nn.Dropout(0.3), nn.Linear(hidden * 4, n_labels))

    def forward(self, input_ids, attention_mask, **kwargs):
        embedded = self.embedding(input_ids)
        packed = pack_padded_sequence(embedded, attention_mask.sum(1).cpu(), batch_first=True,
                                      enforce_sorted=False)
        hidden, _ = self.lstm(packed)
        hidden, _ = pad_packed_sequence(hidden, batch_first=True, total_length=input_ids.shape[1])
        attended, _ = self.attention(hidden, hidden, hidden,
                                     key_padding_mask=~attention_mask.bool(), need_weights=False)
        return self.head(masked_pool(self.norm(hidden + attended), attention_mask))


class FrozenProteinTransformer(nn.Module):
    def __init__(self, n_labels, spec, source=None, local_only=False):
        super().__init__()
        from transformers import AutoModel

        self.backbone = AutoModel.from_pretrained(source or spec["hf_model"],
                                                  local_files_only=local_only)
        self.backbone.requires_grad_(False)
        self.backbone.eval()
        self.head = nn.Sequential(nn.Dropout(0.3), nn.Linear(self.backbone.config.hidden_size, n_labels))

    def train(self, mode=True):
        super().train(mode)
        self.backbone.eval()
        return self

    def forward(self, input_ids, attention_mask, special_tokens_mask, **kwargs):
        with torch.no_grad():
            hidden = self.backbone(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        mask = attention_mask.bool() & ~special_tokens_mask.bool()
        pooled = (hidden * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True).clamp_min(1)
        return self.head(pooled)


def build_model(spec, n_labels, source=None, local_only=False):
    kind = spec["kind"]
    if kind == "cnn":
        return ProtCNN(n_labels, spec)
    if kind == "bilstm":
        return BiLSTMAttention(n_labels, spec)
    if kind in {"esm2", "protbert"}:
        return FrozenProteinTransformer(n_labels, spec, source, local_only)
    raise ValueError(f"Modelo desconocido: {kind}")


class SequenceCollator:
    def __init__(self, spec, max_length, tokenizer=None):
        self.spec, self.max_length, self.tokenizer = spec, max_length, tokenizer

    def __call__(self, sequences):
        sequences = [s[:self.max_length] for s in sequences]
        if not sequences or any(not s for s in sequences):
            raise ValueError("El lote debe contener secuencias no vacías.")
        if self.tokenizer is not None:
            if self.spec["kind"] == "protbert":
                texts = [" ".join(re.sub(r"[UZOBJ]", "X", s)) for s in sequences]
            else:
                texts = [s.replace("J", "X") for s in sequences]
            tokens = self.tokenizer(texts, padding=True, truncation=False, return_tensors="pt",
                                    return_special_tokens_mask=True)
            # Ambos modelos representan cada residuo mediante exactamente un token.
            residue_mask = tokens["attention_mask"].bool() & ~tokens["special_tokens_mask"].bool()
            lengths = residue_mask.sum(1).tolist()
            if lengths != [len(s) for s in sequences]:
                raise ValueError("El tokenizer no mantiene un token por aminoácido.")
            return {k: tokens[k] for k in ("input_ids", "attention_mask", "special_tokens_mask")}
        width = max(map(len, sequences))
        ids = torch.zeros((len(sequences), width), dtype=torch.long)
        for i, sequence in enumerate(sequences):
            ids[i, :len(sequence)] = torch.tensor([AA_TO_ID[aa] for aa in sequence])
        return {"input_ids": ids, "attention_mask": ids.ne(0).long()}


def load_tokenizer(spec, source=None, local_only=False):
    if spec["kind"] not in {"esm2", "protbert"}:
        return None
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(source or spec["hf_model"], do_lower_case=False,
                                          local_files_only=local_only)


@torch.inference_mode()
def predict_scores(model, collator, sequences, device="cpu", batch_size=32):
    if not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("batch_size debe ser un entero positivo.")
    if not sequences:
        raise ValueError("Se requiere al menos una secuencia para predecir puntajes.")
    model.eval()
    outputs = []
    for start in range(0, len(sequences), batch_size):
        batch = {k: v.to(device) for k, v in collator(sequences[start:start + batch_size]).items()}
        outputs.append(torch.sigmoid(model(**batch)).cpu().numpy())
    return np.concatenate(outputs, axis=0)


def save_bundle(path, model, tokenizer, manifest):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    if isinstance(model, FrozenProteinTransformer):
        model.backbone.save_pretrained(path / "backbone", safe_serialization=True)
        tokenizer.save_pretrained(path / "backbone")
        weights = model.head.state_dict()
    else:
        weights = model.state_dict()
    torch.save({k: v.detach().cpu() for k, v in weights.items()}, path / "weights.pt")
    (path / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


class ProteinGOPredictor:
    """Cargar una vez al iniciar la aplicación; predict acepta secuencia o FASTA."""
    def __init__(self, bundle_dir, device="cpu"):
        path = Path(bundle_dir)
        self.manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        if self.manifest.get("schema_version") != 1:
            raise ValueError("Versión del artefacto no soportada.")
        self.classes = self.manifest["classes"]
        self.metadata = self.manifest["label_metadata"]
        self.device = torch.device(device)
        spec = self.manifest["model_spec"]
        backbone = path / "backbone"
        self.model = build_model(spec, len(self.classes), source=str(backbone), local_only=True)
        weights = torch.load(path / "weights.pt", map_location="cpu", weights_only=True)
        target = self.model.head if isinstance(self.model, FrozenProteinTransformer) else self.model
        target.load_state_dict(weights, strict=True)
        self.model.to(self.device).eval()
        tokenizer = load_tokenizer(spec, source=str(backbone), local_only=True)
        self.collator = SequenceCollator(spec, self.manifest["max_length"], tokenizer)

    def predict_records(self, records, threshold=None, top_k=None, batch_size=16):
        if threshold is None:
            threshold = self.manifest["threshold"]
        if not 0 <= threshold <= 1:
            raise ValueError("El umbral debe estar entre 0 y 1.")
        if top_k is not None and (not isinstance(top_k, int) or top_k < 1):
            raise ValueError("top_k debe ser un entero positivo o None.")
        if not isinstance(batch_size, int) or batch_size < 1:
            raise ValueError("batch_size debe ser un entero positivo.")
        records = [(str(pid), normalize_sequence(seq)) for pid, seq in records]
        if not records:
            return []
        direct = predict_scores(self.model, self.collator, [seq for _, seq in records],
                                self.device, batch_size)
        scores = propagate_scores(direct, self.classes, self.metadata)
        results = []
        for (pid, sequence), row, raw in zip(records, scores, direct):
            indices = [int(j) for j in np.argsort(-row, kind="stable") if row[j] >= threshold]
            if top_k is not None:
                indices = indices[:top_k]
            # RF-07: "score" conserva el contrato original (puntaje tras propagar por la
            # jerarquía GO). Se añaden "direct_score" (salida sigmoid del modelo para ese
            # término) y "origin": "propagated" cuando el puntaje proviene de un descendiente.
            predictions = [{"go_term": self.classes[j], "name": self.metadata[self.classes[j]]["name"],
                            "aspect": self.metadata[self.classes[j]]["aspect"], "score": float(row[j]),
                            "direct_score": float(raw[j]),
                            "origin": "propagated" if row[j] > raw[j] else "direct"}
                           for j in indices]
            results.append({"id": pid, "sequence": sequence, "length": len(sequence),
                            "residues_used": min(len(sequence), self.manifest["max_length"]),
                            "truncated": len(sequence) > self.manifest["max_length"],
                            "threshold": float(threshold), "predictions": predictions,
                            "status": "ok" if predictions else "no_terms_above_threshold"})
        return results

    def predict(self, text, threshold=None, top_k=None, batch_size=16):
        results = self.predict_records(parse_input(text), threshold, top_k, batch_size)
        return {"schema_version": 1, "model": self.manifest["model_spec"]["kind"],
                "input": text, "results": results}


def export_tsv(predictor, fasta_path, output_path, batch_size=32, threshold=None, top_k=None):
    """Tripletas sin cabecera, calculadas por el modelo; memoria limitada por lote."""
    if not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("batch_size debe ser un entero positivo.")
    count, batch = 0, []
    with open(fasta_path, encoding="utf-8") as source, open(output_path, "w", encoding="utf-8", newline="") as target:
        def flush():
            nonlocal count
            for result in predictor.predict_records(batch, threshold, top_k, batch_size):
                for prediction in result["predictions"]:
                    target.write(f'{result["id"]}\t{prediction["go_term"]}\t{prediction["score"]:.6f}\n')
                    count += 1

        for record in iter_fasta(source):
            batch.append(record)
            if len(batch) == batch_size:
                flush()
                batch.clear()
        if batch:
            flush()
    return count


def main(input_path):
    """Predice con el modelo junto al script; solo requiere la ruta de entrada."""
    input_path = Path(input_path).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")
    script_dir = Path(__file__).resolve().parent
    candidates = [script_dir / "model", script_dir / "best_model"]
    bundle = next((p for p in candidates if (p / "manifest.json").is_file()), None)
    if bundle is None:
        raise FileNotFoundError("No se encontró model/ o best_model/ junto a protein_go.py. Extrae el ZIP completo del modelo.")
    predictor = ProteinGOPredictor(bundle, device="cpu")
    result = predictor.predict(input_path.read_text(encoding="utf-8-sig"))
    output = input_path.with_name(f"{input_path.stem}.predictions.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Predicciones guardadas en: {output}")
    return output


def _cli():
    parser = argparse.ArgumentParser(description="Predecir funciones GO con un modelo exportado.")
    parser.add_argument("path", nargs="?", type=Path, help="Archivo FASTA o TXT; modelo y salida automáticos")
    parser.add_argument("--model", help="Uso avanzado: directorio del modelo")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sequence")
    group.add_argument("--fasta", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=["json", "tsv"], default="json")
    parser.add_argument("--threshold", type=float)
    parser.add_argument("--top-k", type=int)
    args = parser.parse_args()
    if args.path is not None:
        if (args.model is not None or args.sequence is not None or args.fasta is not None
                or args.output is not None or args.format != "json"
                or args.threshold is not None or args.top_k is not None):
            parser.error("Usa solo la ruta para el modo automático; los argumentos opcionales son del modo avanzado.")
        main(args.path)
        return
    if args.model is None or args.output is None or (args.sequence is None and args.fasta is None):
        parser.error("Indica únicamente la ruta del archivo FASTA/TXT. Modo avanzado: --model, --output y --sequence o --fasta.")
    predictor = ProteinGOPredictor(args.model)
    if args.format == "tsv":
        if args.fasta is None:
            parser.error("TSV requiere --fasta")
        export_tsv(predictor, args.fasta, args.output, threshold=args.threshold, top_k=args.top_k)
    else:
        text = args.sequence if args.sequence is not None else args.fasta.read_text(encoding="utf-8")
        result = predictor.predict(text, threshold=args.threshold, top_k=args.top_k)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    _cli()
