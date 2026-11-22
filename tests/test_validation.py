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
