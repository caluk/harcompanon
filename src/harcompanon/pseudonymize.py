"""Pseudonymize domain PII in a HAR — replace it with consistent, format-preserving synthetic data.

Distinct from ``redact`` (which masks *secrets* to ``<REDACTED>``). Pseudonymization keeps the
evidence **usable**: a real VIN becomes a fake VIN (17 chars, real WMI prefix kept), a UUID stays
UUID-shaped, an IMEI stays 15 digits — and the **same** real value always maps to the **same**
synthetic one, so a companion can still reason about structure and cross-references ("the same
vehicle appears in N calls", "a UUID in every URL path — is it guessable?"). Only the real
identifiers change; **numbers are left untouched** (scrambling an odometer would destroy the real
monotonic history and manufacture a false "impossible mileage" finding).

Two passes:
- **key-based** — *string* values of configured PII keys inside JSON bodies (``vin``,
  ``licensePlate``, ``deviceId``, ``mobileNo``, ``address``, ``city`` …) are replaced.
- **pattern-based** — UUIDs and (letter-bearing) VINs are replaced wherever they appear (URL
  paths, ``_initiator.url``, the ``:path`` header, bodies).

Heuristic, like ``redact``: it can't *guarantee* it caught every PII field in an arbitrary API —
review the change report before sending or publishing.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

#: JSON body keys (lower-cased) whose values are treated as PII and synthesized. Configurable.
DEFAULT_PII_KEYS: frozenset[str] = frozenset(
    {
        "vin",
        "licenseplate",
        "registrationnumber",
        "deviceid",
        "imei",
        "mobileno",
        "phone",
        "phonenumber",
        "telephone",
        "email",
        "emailaddress",
        "address",
        "addressline",
        "addressline1",
        "addressline2",
        "street",
        "city",
        "postalcode",
        "zip",
        "zipcode",
        "stateorprovince",
        "latitude",
        "longitude",
        "lat",
        "lon",
        "lng",
        "name",
        "firstname",
        "lastname",
        "fullname",
        "givenname",
        "familyname",
        "dob",
        "dateofbirth",
        "birthdate",
        "mileage",
        "displayedmileage",
        "odometer",
        "repairername",
        "dealername",
        "devicedetails",
    }
)

_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
# A real VIN is 17 chars *and contains letters* (the WMI is alphabetic). The letter lookahead is
# essential: without it the pattern also matches 17-digit telematics readings (sensor values,
# counters) that are not identifiers, scrambling legitimate structure. See tests.
_VIN = re.compile(r"\b(?=[A-HJ-NPR-Z0-9]*[A-HJ-NPR-Z])[A-HJ-NPR-Z0-9]{17}\b")
_IMEI = re.compile(r"\b\d{15}\b")
_VIN_ALPHABET = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"  # standard VIN excludes I, O, Q

#: City keys map to one fixed, real-looking city rather than a format-preserving scramble —
#: a plausible name ("Berlin") reads as real data instead of the gibberish ("Bhtilv") that tips a
#: companion off that the capture was anonymized. All real cities collapse to the same value.
CITY_KEYS: frozenset[str] = frozenset({"city"})
CITY_REPLACEMENT = "Berlin"


class Pseudonymizer:
    """Builds a consistent real→synthetic mapping and applies it (format-preserving)."""

    def __init__(self, pii_keys: frozenset[str] = DEFAULT_PII_KEYS) -> None:
        self.pii_keys = {k.lower() for k in pii_keys}
        self._map: dict[str, str] = {}
        self._synth_values: set[str] = set()  # outputs we produced — never re-map them
        self.counts: Counter[str] = Counter()

    # --- format-preserving generators (deterministic per real value) ---
    @staticmethod
    def _digest(salt: str, real: str) -> bytes:
        return hashlib.sha256(f"{salt}:{real}".encode()).digest()

    def _fake_uuid(self, real: str) -> str:
        h = hashlib.sha256(f"uuid:{real}".encode()).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    def _seeded(self, salt: str, real: str, alphabet: str, length: int) -> str:
        h = self._digest(salt, real)
        return "".join(alphabet[h[i % len(h)] % len(alphabet)] for i in range(length))

    def _fake_generic(self, real: str) -> str:
        """Class-preserving scramble: digit→digit, upper→upper, lower→lower, keep the rest."""
        h = self._digest("gen", real)
        out: list[str] = []
        for i, ch in enumerate(real):
            seed = h[i % len(h)]
            if ch.isdigit():
                out.append("0123456789"[seed % 10])
            elif ch.isupper():
                out.append(chr(ord("A") + seed % 26))
            elif ch.islower():
                out.append(chr(ord("a") + seed % 26))
            else:
                out.append(ch)
        return "".join(out)

    def _synth(self, real: str, category: str) -> str:
        if real in self._map:
            return self._map[real]
        if real in self._synth_values:
            return real  # idempotent: a value we already produced is left as-is on re-passes
        if category == "city":
            synth = CITY_REPLACEMENT
        elif category == "uuid":
            synth = self._fake_uuid(real)
        elif category == "vin":
            # Keep the 3-char WMI (manufacturer/region — "it's a Lexus", not individual-identifying)
            # and scramble only the vehicle-specific remainder. A slight, plausibly-real change.
            synth = real[:3] + self._seeded("vin", real, _VIN_ALPHABET, max(len(real) - 3, 0))
        elif category == "imei":
            synth = self._seeded("imei", real, "0123456789", 15)
        else:
            synth = self._fake_generic(real)
        self._map[real] = synth
        self._synth_values.add(synth)
        self.counts[category] += 1
        return synth

    def _classify(self, value: str) -> str:
        if _UUID.fullmatch(value):
            return "uuid"
        if _VIN.fullmatch(value):
            return "vin"
        if _IMEI.fullmatch(value):
            return "imei"
        return "key"

    def replace_patterns(self, text: str) -> str:
        """Replace UUIDs and (letter-bearing) VINs wherever they appear in ``text``.

        IMEIs are handled *key-based only* (``deviceId``/``imei``/``mobileNo`` …): a bare 15-digit
        run in free text is far more often a telematics reading than a device id, so matching it by
        pattern would corrupt real structure. Under a known key the class is unambiguous.
        """
        text = _UUID.sub(lambda m: self._synth(m.group(0), "uuid"), text)
        return _VIN.sub(lambda m: self._synth(m.group(0), "vin"), text)

    def _walk(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            result: dict[str, Any] = {}
            for key, value in obj.items():
                key_l = key.lower()
                if key_l in CITY_KEYS and isinstance(value, str) and value:
                    result[key] = self._synth(value, "city")
                elif key_l in self.pii_keys and isinstance(value, str) and value:
                    result[key] = self._synth(value, self._classify(value))
                else:
                    # Numbers (odometer/mileage, coordinates) are left as-is: scrambling them
                    # destroys real structure (e.g. monotonic mileage) and manufactures findings.
                    result[key] = self._walk(value)
            return result
        if isinstance(obj, list):
            return [self._walk(item) for item in obj]
        if isinstance(obj, str):
            return self.replace_patterns(obj)
        return obj

    def apply_patterns_deep(self, obj: Any) -> Any:
        """Run the pattern pass over *every* string in ``obj`` (any nesting).

        HAR scatters URLs across many free-text fields — ``request.url``, ``_initiator.url``,
        ``response.redirectURL``, the HTTP/2 ``:path`` header — so a targeted field list keeps
        missing one. Walking everything is only safe because ``_synth`` is idempotent: re-touching
        an already-synthesized value (e.g. a body text already key-processed) is a no-op.
        """
        if isinstance(obj, dict):
            return {k: self.apply_patterns_deep(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.apply_patterns_deep(item) for item in obj]
        if isinstance(obj, str):
            return self.replace_patterns(obj)
        return obj

    def process_body(self, text: str) -> str:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return self.replace_patterns(text)
        return json.dumps(self._walk(parsed), ensure_ascii=False)


def pseudonymize_file(
    path: Path, output: Path, pii_keys: frozenset[str] = DEFAULT_PII_KEYS
) -> Counter[str]:
    """Write a pseudonymized copy of ``path`` to ``output``; return per-category counts."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} is not a valid HAR file (expected a top-level JSON object).")

    p = Pseudonymizer(pii_keys)
    log = raw.get("log")
    raw_entries = log.get("entries") if isinstance(log, dict) else None
    entries: list[Any] = raw_entries if isinstance(raw_entries, list) else []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        # Key-based body synthesis first (plates, mileage, addresses inside JSON bodies)…
        request = entry.get("request")
        response = entry.get("response")
        if isinstance(request, dict):
            post = request.get("postData")
            if isinstance(post, dict) and isinstance(post.get("text"), str):
                post["text"] = p.process_body(post["text"])
        if isinstance(response, dict):
            content = response.get("content")
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                content["text"] = p.process_body(content["text"])
        # …then a blanket pattern pass over every remaining string in the entry (URLs wherever
        # they hide). Idempotent, so it harmlessly re-touches the bodies just processed.
        entries[index] = p.apply_patterns_deep(entry)

    output.write_text(json.dumps(raw, ensure_ascii=False) + "\n", encoding="utf-8")
    return p.counts
