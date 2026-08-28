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
from harcompanon.pseudonymize import (
    _FIRST_NAMES,
    _IMEI,
    _IPV4,
    _LAST_NAMES,
    _UUID,
    _VIN,
    Pseudonymizer,
    pseudonymize_file,
)

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


def test_exclude_leaves_a_key_untouched() -> None:
    # A geoip city would normally collapse to "Berlin", but excluding it keeps the real value so
    # it stays consistent with the sibling coordinates (no manufactured location contradiction).
    excluded = Pseudonymizer(exclude=frozenset({"city"}))
    assert excluded._key_category("city", "Hamburg") is None
    assert Pseudonymizer()._key_category("city", "Hamburg") == "city"  # default still remaps


def test_city_keys_collapse_to_one_real_looking_city() -> None:
    # Cities become a plausible fixed name (not gibberish), so a companion doesn't detect scrubbing.
    p = Pseudonymizer()
    assert p._synth("Bremen", "city") == "Berlin"
    assert p._synth("Munich", "city") == "Berlin"  # all cities collapse to the same value


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
            "city": "Bremen",
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
    assert "Bremen" not in text and "Berlin" in text  # city → fixed real-looking name
    assert "RX 450h" in text  # non-PII value untouched
    assert "45210" in text  # numbers (mileage) are left as-is — structure preserved

    assert counts["uuid"] >= 1 and counts["vin"] >= 1 and counts["imei"] >= 1
    assert "number" not in counts  # numbers are never synthesized

    # Still valid JSON and still preprocesses.
    artifact = preprocess_file(out)
    assert artifact.total_entries == 1


def test_names_services_and_ips_use_fixed_labels_and_literal_replacement(tmp_path: Path) -> None:
    real_ip = "77.0.27.172"
    body = json.dumps({"ip": real_ip, "city": "Hamburg", "country": "Germany"})
    profile = json.dumps({"display_name": "Jane Doe", "repairerName": "WELLER", "name": "Alster"})
    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": f"https://x/geoip/{real_ip}",
                        "headers": [],
                    },
                    "response": {
                        "status": 200,
                        "content": {"mimeType": "application/json", "text": body},
                    },
                },
                {
                    "request": {"method": "GET", "url": "https://x/me", "headers": []},
                    "response": {
                        "status": 200,
                        "content": {"mimeType": "application/json", "text": profile},
                    },
                },
            ]
        }
    }
    src = tmp_path / "in.har"
    src.write_text(json.dumps(har), encoding="utf-8")
    out = tmp_path / "out.har"
    pseudonymize_file(src, out)
    text = out.read_text(encoding="utf-8")

    assert "Jane Doe" not in text  # person name replaced…
    out_har = json.loads(text)
    prof = json.loads(out_har["log"]["entries"][1]["response"]["content"]["text"])
    first, _, last = prof["display_name"].partition(" ")
    assert first in _FIRST_NAMES and last in _LAST_NAMES  # …with a plausible synthetic name
    assert (
        "Lexus Service" in text and "WELLER" not in text
    )  # service name → fixed label (not gibberish)
    assert "Alster" in text  # a place name under bare "name" is NOT touched (map evidence)
    assert real_ip not in text  # the client IP is gone from BOTH the body key and the URL path
    # The URL-path IP got the SAME synthetic IP as the body key (literal, consistent).
    url = out_har["log"]["entries"][0]["request"]["url"]
    synth_ip = url.rsplit("/", 1)[1]
    assert _IPV4.fullmatch(synth_ip) and synth_ip != real_ip


def test_name_scrubbed_by_key_in_html_but_prose_is_left_alone(tmp_path: Path) -> None:
    # A page inlines its state as an escaped JSON string in an HTML document; the same real name
    # also appears in free-text prose (a photo attribution). The keyed occurrence must be scrubbed;
    # the prose occurrence must be left untouched (it isn't the user's PII to mangle).
    html = (
        '<!doctype html><script>window.__STATE__="'
        '{\\"display_name\\":\\"Andreas Steger\\"}";</script>'
        "<p>Photo by Andreas Steger, Hamburg.</p>"
    )
    har = {
        "log": {
            "entries": [
                {
                    "request": {"method": "GET", "url": "https://x/plan", "headers": []},
                    "response": {"status": 200, "content": {"mimeType": "text/html", "text": html}},
                }
            ]
        }
    }
    src = tmp_path / "in.har"
    src.write_text(json.dumps(har), encoding="utf-8")
    out = tmp_path / "out.har"
    pseudonymize_file(src, out)
    result = json.loads(out.read_text(encoding="utf-8"))
    body = result["log"]["entries"][0]["response"]["content"]["text"]
    assert '\\"display_name\\":\\"Andreas Steger\\"' not in body  # keyed name scrubbed in HTML
    assert "Photo by Andreas Steger, Hamburg." in body  # prose left untouched


def test_cli_pseudonymize(tmp_path: Path) -> None:
    src = tmp_path / "in.har"
    src.write_text(json.dumps(_sample_har()), encoding="utf-8")
    out = tmp_path / "out.har"

    result = runner.invoke(app, ["pseudonymize", str(src), "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert "Pseudonymized" in result.output
    assert REAL_VIN not in out.read_text(encoding="utf-8")
