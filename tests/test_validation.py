from conftest import EXAMPLES

from proteinfunc_app.core.validation import ERROR, OK, WARNING, read_input_file, validate_text


def test_raw_sequence_is_single_query():
    report = validate_text("mkta yiak\nqr*", max_length=512)
    assert report.is_clean
    assert report.as_records() == [("query_1", "MKTAYIAKQR")]


def test_empty_input_is_global_error():
    report = validate_text("   \n ", 512)
    assert report.global_errors and not report.accepted


def test_reports_every_problem_not_only_the_first():
    report = validate_text(read_input_file(EXAMPLES / "con_errores.fasta"), 512)
    statuses = [(r.record_id, r.status) for r in report.records]
    assert statuses == [("valida_1", OK), ("vacia", ERROR), ("con_simbolos", ERROR),
                        ("valida_1", ERROR), ("", ERROR)]
    assert "duplicado" in report.records[3].messages[0]
    assert "'#'" in report.records[2].messages[0] and "11" in report.records[2].messages[0]
    assert "vacía" in report.records[4].messages[0].lower()
    assert report.as_records() == [("valida_1", report.records[0].sequence)]


def test_long_sequence_is_warning_and_keeps_full_sequence():
    seq = "A" * 600
    report = validate_text(f">largo\n{seq}\n", max_length=512)
    record = report.records[0]
    assert record.status == WARNING and record.accepted
    assert record.sequence == seq and "512" in record.messages[0]


def test_uniprot_ids_are_normalised_like_runtime():
    report = validate_text(">sp|P01308|INS_HUMAN Insulina\nMALW\n>tr|Q9XYZ1|X Y\nMKT\n", 512)
    assert [r.record_id for r in report.records] == ["P01308", "Q9XYZ1"]


def test_validation_agrees_with_runtime_parser():
    from proteinfunc_app.inference.protein_go import parse_input

    text = read_input_file(EXAMPLES / "muestra.fasta")
    assert validate_text(text, 512).as_records() == parse_input(text)


def test_reads_latin1_files(tmp_path):
    path = tmp_path / "acentos.fasta"
    path.write_bytes(">proteína_ñ\nMKT\n".encode("latin-1"))
    assert validate_text(read_input_file(path), 512).records[0].record_id == "proteína_ñ"


def test_text_before_first_header_is_clear_error():
    report = validate_text("MKTAYIAKQR\n>a\nMKT\n", 512)
    assert report.global_errors and "antes de la primera cabecera" in report.global_errors[0]


def test_low_complexity_is_warning_but_real_proteins_are_not():
    from proteinfunc_app.core.validation import complexity_warning

    report = validate_text(">poliG\n" + "G" * 50, 512)
    assert report.records[0].status == WARNING and report.records[0].accepted
    assert complexity_warning("X" * 30 + "MKTAYIAKQR") is not None
    for record in validate_text(read_input_file(EXAMPLES / "muestra.fasta"), None).records:
        assert complexity_warning(record.sequence) is None, record.record_id


def test_example_test_files_validate_as_documented():
    """Los FASTA de examples/pruebas mantienen el resultado descrito en su LEEME.md."""
    expected = {
        "01_proteinas_conocidas.fasta": "8 registros · 8 válidos",
        "02_secuencia_para_pegar.txt": "1 registro · 1 válido",
        "03_casos_limite.fasta": "6 registros · 6 válidos · 2 con aviso",
        "04_errores.fasta": "7 registros · 2 válidos · 5 con error",
        "05_lote_300_sinteticas.fasta": "300 registros · 300 válidos · 94 con aviso",
    }
    folder = EXAMPLES / "pruebas"
    for name, summary in expected.items():
        assert validate_text(read_input_file(folder / name), 512).summary() == summary, name
    report = validate_text(read_input_file(folder / "06_texto_antes_de_cabecera.fasta"), 512)
    assert "antes de la primera cabecera" in report.global_errors[0]
    report = validate_text(read_input_file(folder / "07_adn_en_vez_de_proteina.fasta"), 512)
    assert report.summary() == "3 registros · 1 válido · 2 con error"


def test_dna_and_rna_are_rejected_but_protein_extremes_are_not():
    from proteinfunc_app.core.validation import looks_like_nucleotides

    dna = "ATCAGCATCGACAGCTAGCATCAGCTAGCATCGACTAGCATCGACTAGCATCGATCAGCTAGCAC"
    report = validate_text(f">gen\n{dna}\n>arn\n{dna.replace('T', 'U')}\n", 512)
    assert [r.status for r in report.records] == [ERROR, ERROR]
    assert "ADN/ARN" in report.records[0].messages[0]
    assert validate_text(dna, 512).records[0].status == ERROR  # También pegada sin cabecera.
    assert not looks_like_nucleotides("G" * 50)            # Poliglicina: baja complejidad, no ADN.
    assert not looks_like_nucleotides("ACGTACGT")           # Demasiado corta para decidir.
    for record in validate_text(read_input_file(EXAMPLES / "pruebas" / "01_proteinas_conocidas.fasta"), 512).records:
        assert not looks_like_nucleotides(record.sequence), record.record_id


def test_low_complexity_message_explains_the_cause():
    from proteinfunc_app.core.validation import complexity_warning

    assert "ocupa el 100%" in complexity_warning("G" * 50)
    message = complexity_warning("ACDE" * 15)
    assert "4 aminoácidos distintos" in message and "bits" in message
