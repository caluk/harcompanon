"""Conventional software tests (pytest) for HAR pseudonymization.

Pseudonymization must be *consistent* (same real value → same synthetic one),
*format-preserving* (a UUID stays UUID-shaped, a VIN 17 chars, an IMEI 15 digits),
and must remove every real identifier while keeping non-PII structure intact.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.preprocess import preprocess_file
from harcompanon.pseudonymize import _IMEI, _UUID, _VIN, Pseudonymizer, pseudonymize_file

runner = CliRunner()

REAL_UUID = "bd9a9d27-88b6-46af-818e-cf17faafe3f0"
REAL_VIN = "JTJBARBZ8K2000028"  # 17 chars, no I/O/Q
REAL_IMEI = "357703000000007"  # 15 digits


def test_pattern_replacement_is_consistent_and_format_preserving() -> None:
    p = Pseudonymizer()
    # Consistency: same input → same output on repeat calls.
    assert p.replace_patterns(REAL_UUID) == p.replace_patterns(REAL_UUID)
    synth_uuid = p.replace_patterns(REAL_UUID)
    synth_vin = p.replace_patterns(REAL_VIN)
    # Changed, but shape preserved.
    assert synth_uuid != REAL_UUID and _UUID.fullmatch(synth_uuid)
    assert synth_vin != REAL_VIN and _VIN.fullmatch(synth_vin)


def test_pattern_pass_ignores_all_numeric_lookalikes() -> None:
    # 17-digit telematics reading and a bare 15-digit run are NOT identifiers → left untouched.
    p = Pseudonymizer()
    assert p.replace_patterns("04800001624971628") == "04800001624971628"  # not a VIN (no letter)
    assert p.replace_patterns(REAL_IMEI) == REAL_IMEI  # IMEI is key-based only


def test_imei_is_synthesized_under_a_pii_key() -> None:
    p = Pseudonymizer()
    synth = p._synth(REAL_IMEI, p._classify(REAL_IMEI))
    assert synth != REAL_IMEI and _IMEI.fullmatch(synth)


def test_generic_key_scramble_preserves_character_classes() -> None:
    p = Pseudonymizer()
    synth = p._synth("HH-XX 1234", "key")
    assert synth != "HH-XX 1234"
    assert len(synth) == len("HH-XX 1234")
    # Non-alphanumerics kept in place; classes preserved.
    assert synth[2] == "-" and synth[5] == " "
    assert synth[:2].isupper() and synth[6:].isdigit()


def test_vin_keeps_its_wmi_prefix() -> None:
    # The 3-char WMI (manufacturer) is kept; only the vehicle-specific remainder changes.
    p = Pseudonymizer()
    synth = p._synth(REAL_VIN, "vin")
    assert synth[:3] == REAL_VIN[:3] and synth != REAL_VIN and _VIN.fullmatch(synth)


def _sample_har() -> dict[str, object]:
    body = json.dumps(
        {
            "vin": REAL_VIN,
            "licensePlate": "HH-XX 1234",
            "deviceId": REAL_IMEI,
            "displayedMileage": 45210,
            "modelName": "RX 450h",  # not a PII key → kept
        }
    )
    return {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": f"https://api.example.com/vehicle/{REAL_VIN}/user/{REAL_UUID}",
                        # HTTP/2 :path pseudo-header duplicates the URL path (VIN + UUID hide here).
                        "headers": [
                            {"name": ":path", "value": f"/vehicle/{REAL_VIN}/user/{REAL_UUID}"}
                        ],
                    },
                    "response": {
                        "status": 200,
                        "headers": [],
                        "content": {"mimeType": "application/json", "text": body},
                    },
                }
            ]
        }
    }


def test_pseudonymize_file_removes_pii_and_keeps_structure(tmp_path: Path) -> None:
    src = tmp_path / "in.har"
    src.write_text(json.dumps(_sample_har()), encoding="utf-8")
    out = tmp_path / "out.har"

    counts = pseudonymize_file(src, out)
    text = out.read_text(encoding="utf-8")

    for real in (REAL_UUID, REAL_VIN, REAL_IMEI, "HH-XX 1234"):
        assert real not in text, f"real PII survived: {real}"
    assert "RX 450h" in text  # non-PII value untouched
    assert "45210" in text  # numbers (mileage) are left as-is — structure preserved

    assert counts["uuid"] >= 1 and counts["vin"] >= 1 and counts["imei"] >= 1
    assert "number" not in counts  # numbers are never synthesized

    # Still valid JSON and still preprocesses.
    artifact = preprocess_file(out)
    assert artifact.total_entries == 1


def test_cli_pseudonymize(tmp_path: Path) -> None:
    src = tmp_path / "in.har"
    src.write_text(json.dumps(_sample_har()), encoding="utf-8")
    out = tmp_path / "out.har"

    result = runner.invoke(app, ["pseudonymize", str(src), "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert "Pseudonymized" in result.output
    assert REAL_VIN not in out.read_text(encoding="utf-8")
