"""Pseudonymize domain PII in a HAR — replace it with consistent, format-preserving synthetic data.

Distinct from ``redact`` (which masks *secrets* to ``<REDACTED>``). Pseudonymization keeps the
evidence **usable**: a real VIN becomes a fake VIN (17 chars, real WMI prefix kept), a UUID stays
UUID-shaped, an IMEI stays 15 digits — and the **same** real value always maps to the **same**
synthetic one, so a companion can still reason about structure and cross-references ("the same
vehicle appears in N calls", "a UUID in every URL path — is it guessable?"). Only the real
identifiers change; **numbers are left untouched** (scrambling an odometer would destroy the real
monotonic history and manufacture a false "impossible mileage" finding).

Two passes:
- **key-based** — *string* values of configured PII keys inside JSON bodies are replaced. Some
  key classes collapse to one fixed, real-looking label instead of a gibberish scramble:
  ``city`` → ``Berlin``, person names (``display_name`` …) → a synthetic English/German name,
  service/dealer names → ``Lexus Service``. IP-valued keys become a valid-looking IPv4.
- **pattern-based** — UUIDs and (letter-bearing) VINs are replaced wherever they appear (URL
  paths, ``_initiator.url``, the ``:path`` header, bodies). IPs and names learned from a key are
  additionally replaced *literally* wherever they recur (e.g. a client IP in a geoip URL path).

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
        # NB: bare "name"/"lat"/"lng" are deliberately NOT here — in map/POI APIs they hold
        # legitimate place names and coordinates (komoot has 1064 POI lat/lng, 75 place names).
        # Person names go through NAME_KEYS; numeric coords are left untouched anyway.
        "firstname",
        "lastname",
        "givenname",
        "familyname",
        "dob",
        "dateofbirth",
        "birthdate",
        "mileage",
        "displayedmileage",
        "odometer",
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

#: Some key classes map to ONE fixed, real-looking label rather than a format-preserving scramble
#: — a plausible value reads as real data instead of the gibberish ("Bhtilv", "VPVVWO") that tips a
#: companion off that the capture was anonymized. All real values in a class collapse to the label.
CITY_KEYS: frozenset[str] = frozenset({"city"})
CITY_REPLACEMENT = "Berlin"
#: Person full-name keys (NOT bare "name" — that is a place/POI name in map APIs).
NAME_KEYS: frozenset[str] = frozenset({"display_name", "displayname", "fullname", "full_name"})
#: Person names become a synthetic but plausible English/German name — deterministic per real
#: value (same real name → same fake), distinct per person (so the count of distinct people
#: survives), and never a fixed label (a repeated name would read as scrubbed). Unlike an IP, a
#: name is NOT replaced literally everywhere: that smears it into unrelated prose (Wikipedia text,
#: photo attributions). Names are replaced only where they sit under a name *key* — including
#: inside a JSON body inlined as an escaped string in an HTML document (see _replace_keyed_in_text).
_FIRST_NAMES: tuple[str, ...] = (
    "James",
    "Emma",
    "Thomas",
    "Anna",
    "Michael",
    "Laura",
    "David",
    "Julia",
    "Daniel",
    "Sophie",
    "Andreas",
    "Marie",
    "Peter",
    "Sarah",
    "Stefan",
    "Lena",
    "Markus",
    "Katrin",
    "Oliver",
    "Hannah",
    "Felix",
    "Nina",
    "Lucas",
    "Emily",
    "Jonas",
    "Clara",
    "Paul",
    "Lisa",
    "Max",
    "Nora",
    "Simon",
    "Greta",
    "Tobias",
    "Mia",
    "Florian",
    "Ella",
    "Sebastian",
    "Ida",
    "Benjamin",
    "Charlotte",
)
_LAST_NAMES: tuple[str, ...] = (
    "Smith",
    "Müller",
    "Jones",
    "Schmidt",
    "Brown",
    "Fischer",
    "Wilson",
    "Weber",
    "Taylor",
    "Meyer",
    "Wagner",
    "Becker",
    "Davies",
    "Schulz",
    "Hoffmann",
    "Koch",
    "Bauer",
    "Richter",
    "Klein",
    "Wolf",
    "Neumann",
    "Schwarz",
    "Zimmermann",
    "Braun",
    "Krüger",
    "Hartmann",
    "Lange",
    "Werner",
    "Krause",
    "Lehmann",
    "Walker",
    "Roberts",
    "Evans",
    "Thompson",
    "Baker",
    "Turner",
    "Vogel",
    "Frank",
    "Berg",
)
#: Service / dealer names (e.g. a car dealer's workshop).
SERVICE_KEYS: frozenset[str] = frozenset(
    {"repairername", "dealername", "repairer_name", "dealer_name"}
)
SERVICE_REPLACEMENT = "Lexus Service"
#: Keys whose value is an IP address — synthesized to a valid-looking IPv4 and, because the same
#: IP also shows up in URL paths (e.g. a geoip lookup), replaced literally everywhere it appears.
IP_KEYS: frozenset[str] = frozenset({"ip", "ipaddress", "ip_address", "client_ip", "remote_addr"})
#: Strict IPv4 (each octet 0-255) so version strings like Chrome/149.0.0.0 don't match.
_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
_IPV4 = re.compile(rf"{_OCTET}(?:\.{_OCTET}){{3}}")

#: A ``"key": "value"`` pair in raw text — quotes optionally backslash-escaped, for a JSON body
#: inlined as a string inside an HTML document. Group 1 = the ``"key":"`` prefix (kept verbatim),
#: group 2 = the bare key, group 3 = the value. Used to scrub PII by key even where it never parses.
_KEYED_FIELD = re.compile(r'(\\?"([A-Za-z0-9_]+)\\?"\s*:\s*\\?")([^"\\]{1,})')


class Pseudonymizer:
    """Builds a consistent real→synthetic mapping and applies it (format-preserving)."""

    def __init__(
        self, pii_keys: frozenset[str] = DEFAULT_PII_KEYS, exclude: frozenset[str] = frozenset()
    ) -> None:
        self.pii_keys = {k.lower() for k in pii_keys}
        #: Keys to leave untouched even if they'd otherwise be synthesized — e.g. skip a geoip
        #: ``city`` so it isn't remapped to "Berlin" while the sibling coordinates stay, which
        #: would manufacture a false location contradiction the companion then "finds".
        self.exclude = {k.lower() for k in exclude}
        self._map: dict[str, str] = {}
        self._synth_values: set[str] = set()  # outputs we produced — never re-map them
        #: real→synth for values that must ALSO be replaced literally wherever they appear
        #: (an IP or name learned from a body key but also embedded in a URL path / free text).
        self._literals: dict[str, str] = {}
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

    def _fake_name(self, real: str) -> str:
        """A plausible English/German full name, deterministic and distinct per real name."""
        first = _FIRST_NAMES[self._digest("first", real)[0] % len(_FIRST_NAMES)]
        last = _LAST_NAMES[self._digest("last", real)[1] % len(_LAST_NAMES)]
        return f"{first} {last}"

    def _fake_ip(self, real: str) -> str:
        """A valid-looking IPv4 (octets 1-254), deterministic per real address."""
        octets = real.split(".")
        if len(octets) != 4:
            return self._fake_generic(real)
        return ".".join(str(1 + self._digest(f"ip{i}", real)[0] % 254) for i in range(4))

    def _synth(self, real: str, category: str) -> str:
        if real in self._map:
            return self._map[real]
        if real in self._synth_values:
            return real  # idempotent: a value we already produced is left as-is on re-passes
        if category == "city":
            synth = CITY_REPLACEMENT
        elif category == "name":
            synth = self._fake_name(real)
        elif category == "service":
            synth = SERVICE_REPLACEMENT
        elif category == "ip":
            synth = self._fake_ip(real)
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
        # An IP also appears outside JSON keys (a geoip URL path) but never inside prose, so it is
        # safe to replace literally everywhere. Names are deliberately NOT literal-replaced (that
        # smears them into unrelated prose) — they are handled key-based, including in text.
        if category == "ip":
            self._literals[real] = synth
        self.counts[category] += 1
        return synth

    def _key_category(self, key_l: str, value: Any) -> str | None:
        """Which synthesis category applies to this key/value, or None to leave it untouched."""
        if not isinstance(value, str) or not value or key_l in self.exclude:
            return None
        if key_l in NAME_KEYS:
            return "name"
        if key_l in SERVICE_KEYS:
            return "service"
        if key_l in IP_KEYS:
            return "ip" if _IPV4.fullmatch(value) else None
        if key_l in CITY_KEYS:
            return "city"
        if key_l in self.pii_keys:
            return self._classify(value)
        return None

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
                category = self._key_category(key.lower(), value)
                if category is not None and isinstance(value, str):
                    result[key] = self._synth(value, category)
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
            return self._replace_keyed_in_text(self._apply_literals(self.replace_patterns(obj)))
        return obj

    def _apply_literals(self, text: str) -> str:
        """Replace each known real IP literal wherever it appears (e.g. a geoip URL path).

        Boundary-guarded so an IP isn't matched inside a longer number (e.g. ``77.0.27.172`` must
        not fire inside ``77.0.27.1720``). Only exact learned values are touched — never a pattern
        — so there are no false positives.
        """
        for real, synth in self._literals.items():
            if real in text:
                text = re.sub(rf"(?<![\w.]){re.escape(real)}(?![\w.])", synth, text)
        return text

    def _replace_keyed_in_text(self, text: str) -> str:
        """Replace ``"<pii-key>": "<value>"`` values inside raw text — even escaped JSON in HTML.

        A page can inline its state as a JSON *string* (``\\"display_name\\":\\"…\\"``) that never
        parses as a body. This catches the value by its key, so a name is scrubbed there too — but,
        crucially, only where it sits under a key. A name appearing in prose (Wikipedia text, photo
        attributions) has no such key, so it is left untouched.
        """
        return _KEYED_FIELD.sub(self._keyed_sub, text)

    def _keyed_sub(self, match: re.Match[str]) -> str:
        category = self._key_category(match.group(2).lower(), match.group(3))
        if category is None:
            return match.group(0)
        return match.group(1) + self._synth(match.group(3), category)

    def process_body(self, text: str) -> str:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return self.replace_patterns(text)
        return json.dumps(self._walk(parsed), ensure_ascii=False)


def pseudonymize_file(
    path: Path,
    output: Path,
    pii_keys: frozenset[str] = DEFAULT_PII_KEYS,
    exclude: frozenset[str] = frozenset(),
) -> Counter[str]:
    """Write a pseudonymized copy of ``path`` to ``output``; return per-category counts."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} is not a valid HAR file (expected a top-level JSON object).")

    p = Pseudonymizer(pii_keys, exclude)
    log = raw.get("log")
    raw_entries = log.get("entries") if isinstance(log, dict) else None
    entries: list[Any] = raw_entries if isinstance(raw_entries, list) else []

    # Pass 1 — key-based body synthesis across *all* entries (plates, mileage, addresses; and
    # learn the IP/name literals). Done for every entry before any literal is applied, so a value
    # learned late (e.g. from a geoip JSON body) still reaches an earlier entry — like an HTML
    # document at entry 0 that inlines the same name/IP and is never JSON-parsed.
    for entry in entries:
        if not isinstance(entry, dict):
            continue
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

    # Pass 2 — blanket pattern + literal pass over every string in every entry (URLs and any body,
    # including non-JSON HTML). Idempotent, so re-touching the bodies from pass 1 is a no-op.
    for index, entry in enumerate(entries):
        if isinstance(entry, dict):
            entries[index] = p.apply_patterns_deep(entry)

    output.write_text(json.dumps(raw, ensure_ascii=False) + "\n", encoding="utf-8")
    return p.counts
