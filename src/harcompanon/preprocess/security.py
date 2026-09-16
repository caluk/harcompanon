"""Mechanical secrets/PII scanner for HAR files.

This is a *safety* guardrail, not evidence interpretation. It scans the RAW HAR — the thing
that would be committed — for likely secrets and PII (auth headers, keys, tokens,
credential fields, emails) and produces a SEPARATE, masked report. It never alters or
annotates the CleanedArtifact that preprocessing sends to the models, so the purity of the
evidence is untouched.

It is heuristic: matches are candidates to review, and a clean result is not a guarantee.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class Severity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


#: Callback used while scanning: (category, severity, where, location, raw_sample) -> None.
AddFinding = Callable[[str, Severity, str, str, str], None]


#: Request/response header names that carry credentials, with their severity.
SENSITIVE_HEADERS: dict[str, Severity] = {
    "cookie": Severity.HIGH,
    "set-cookie": Severity.HIGH,
    "authorization": Severity.HIGH,
    "proxy-authorization": Severity.HIGH,
    "x-api-key": Severity.HIGH,
    "x-auth-token": Severity.HIGH,
    "x-amz-security-token": Severity.HIGH,
    "api-key": Severity.HIGH,
    "x-csrf-token": Severity.MEDIUM,
}

#: URL query-parameter names that commonly carry secrets.
SENSITIVE_QUERY_KEYS: dict[str, Severity] = {
    "access_token": Severity.HIGH,
    "token": Severity.MEDIUM,
    "api_key": Severity.MEDIUM,
    "apikey": Severity.MEDIUM,
    "key": Severity.MEDIUM,
    "password": Severity.HIGH,
    "secret": Severity.HIGH,
    "sig": Severity.LOW,
    "signature": Severity.LOW,
}

#: (category, severity, compiled pattern) applied to URLs and body text.
_PATTERNS: list[tuple[str, Severity, re.Pattern[str]]] = [
    (
        "private_key",
        Severity.HIGH,
        re.compile(
            r"-----BEGIN (?P<key_type>(?:[A-Z ]+ )?PRIVATE KEY)-----"
            r"[\s\S]*?(?:-----END (?P=key_type)-----|$)"
        ),
    ),
    ("aws_access_key", Severity.HIGH, re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack_token", Severity.HIGH, re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("google_api_key", Severity.MEDIUM, re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    (
        "jwt",
        Severity.MEDIUM,
        re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{6,}"),
    ),
    ("bearer_token", Severity.MEDIUM, re.compile(r"[Bb]earer\s+[A-Za-z0-9._-]{8,}")),
    ("email", Severity.LOW, re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
]

#: Credential-bearing JSON/body fields: "<key>": "<value>". The key may carry a prefix
#: (``publicApiToken``, ``refreshToken``, ``clientSecret``) and — for a body serialized as a
#: JSON *string* inside another body — the quotes may be backslash-escaped (``\"key\":\"val\"``).
_CREDENTIAL_FIELD = re.compile(
    r'\\?"([A-Za-z0-9_]*'
    r"(?:password|passwd|pwd|client_secret|secret|api_?key|access_?token|token))\\?\""
    r'\s*:\s*\\?"([^"\\]{4,})',
    re.IGNORECASE,
)
_HIGH_CREDENTIAL_FIELDS = {"password", "passwd", "pwd", "secret", "client_secret"}


#: Placeholder written by `harcompanon redact` into the raw HAR; already-redacted, so the
#: scanner ignores it (a redacted file should scan clean).
REDACTED_MARKER = "<REDACTED>"


def mask(value: str) -> str:
    """Mask a candidate secret so the report never carries the full value."""
    value = value.strip()
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-2:]}"


class SecurityFinding(BaseModel):
    category: str
    severity: Severity
    where: str
    location: str
    masked_sample: str
    occurrences: int = 1


class SecurityReport(BaseModel):
    source_har: str
    findings: list[SecurityFinding]

    def counts(self) -> dict[Severity, int]:
        """Count *distinct* findings per severity (repeats collapse; occurrences live per row)."""
        result = {Severity.HIGH: 0, Severity.MEDIUM: 0, Severity.LOW: 0}
        for finding in self.findings:
            result[finding.severity] += 1
        return result

    def has_findings(self) -> bool:
        return bool(self.findings)

    def has_high(self) -> bool:
        return any(f.severity is Severity.HIGH for f in self.findings)

    def summary_line(self) -> str:
        counts = self.counts()
        if not self.has_findings():
            return (
                "security scan: no obvious secrets/PII detected in the raw HAR "
                "(heuristic — review before publishing)."
            )
        return (
            f"security scan: {counts[Severity.HIGH]} high, {counts[Severity.MEDIUM]} medium, "
            f"{counts[Severity.LOW]} low distinct secret/PII finding(s) in the RAW HAR "
            "(heuristic — review before publishing)."
        )

    def to_markdown(self) -> str:
        order = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
        rows = sorted(self.findings, key=lambda f: (order[f.severity], f.category))
        lines = [
            f"# Security scan — {self.source_har}",
            "",
            "Heuristic scan of the **raw** HAR for secrets/PII. Values are masked. A match is a",
            "candidate to review; a clean result is not a guarantee. This does not affect the",
            "cleaned evidence sent to models.",
            "",
            self.summary_line(),
            "",
            "| Severity | Category | Where | Sample (masked) | # | Location |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for f in rows:
            lines.append(
                f"| {f.severity.value} | {f.category} | {f.where} | `{f.masked_sample}` "
                f"| {f.occurrences} | {f.location} |"
            )
        return "\n".join(lines) + "\n"


class SecurityScanner(BaseModel):
    """Configurable, mechanical scanner. Findings are deduplicated and masked."""

    max_findings_per_category: int = 25

    def scan(self, raw: dict[str, Any], source_har: str = "") -> SecurityReport:
        log = raw.get("log")
        entries = log.get("entries") if isinstance(log, dict) else None
        entries = entries if isinstance(entries, list) else []

        # Deduplicate by (category, where, masked_sample); track first location + count.
        collected: dict[tuple[str, str, str], SecurityFinding] = {}
        per_category: dict[str, int] = {}

        def add(category: str, severity: Severity, where: str, location: str, sample: str) -> None:
            if sample == REDACTED_MARKER:
                return  # already redacted — not a secret
            masked = mask(sample)
            key = (category, where, masked)
            existing = collected.get(key)
            if existing is not None:
                existing.occurrences += 1
                return
            if per_category.get(category, 0) >= self.max_findings_per_category:
                return
            per_category[category] = per_category.get(category, 0) + 1
            collected[key] = SecurityFinding(
                category=category,
                severity=severity,
                where=where,
                location=location,
                masked_sample=masked,
            )

        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            req_obj = entry.get("request")
            request: dict[str, Any] = req_obj if isinstance(req_obj, dict) else {}
            resp_obj = entry.get("response")
            response: dict[str, Any] = resp_obj if isinstance(resp_obj, dict) else {}
            url = str(request.get("url", ""))
            # Paths, userinfo and fragments can carry secrets too; the index locates the call
            # without copying any unmasked part of its URL into the report.
            location = f"entry[{index}]"

            self._scan_headers(request.get("headers"), "request header", location, add)
            self._scan_headers(response.get("headers"), "response header", location, add)
            self._scan_query(url, location, add)

            for side, container in (("request", request), ("response", response)):
                body = _body_text(container)
                if body:
                    self._scan_text(body, f"{side} body", location, add)

        return SecurityReport(source_har=source_har, findings=list(collected.values()))

    @staticmethod
    def _scan_headers(headers: Any, where: str, location: str, add: AddFinding) -> None:
        if not isinstance(headers, list):
            return
        for header in headers:
            if not isinstance(header, dict):
                continue
            name = str(header.get("name", "")).lower().lstrip(":")
            severity = SENSITIVE_HEADERS.get(name)
            if severity is not None:
                add(f"header:{name}", severity, where, location, str(header.get("value", "")))

    @staticmethod
    def _scan_query(url: str, location: str, add: AddFinding) -> None:
        query = url.split("?", 1)[1] if "?" in url else ""
        for pair in query.split("&"):
            if "=" not in pair:
                continue
            raw_key, _, value = pair.partition("=")
            severity = SENSITIVE_QUERY_KEYS.get(raw_key.lower())
            if severity is not None and value:
                add(f"query:{raw_key.lower()}", severity, "url query", location, value)

    @staticmethod
    def _scan_text(text: str, where: str, location: str, add: AddFinding) -> None:
        for category, severity, pattern in _PATTERNS:
            for match in pattern.finditer(text):
                add(category, severity, where, location, match.group(0))
        for match in _CREDENTIAL_FIELD.finditer(text):
            field = match.group(1).lower()
            severity = Severity.HIGH if field in _HIGH_CREDENTIAL_FIELDS else Severity.MEDIUM
            add(f"field:{field}", severity, where, location, match.group(2))


def _body_text(container: dict[str, Any]) -> str | None:
    """Extract a request/response body's text (postData.text or content.text)."""
    post = container.get("postData")
    if isinstance(post, dict):
        post_text = post.get("text")
        if isinstance(post_text, str):
            return post_text
    content = container.get("content")
    if isinstance(content, dict):
        encoding = content.get("encoding")
        if isinstance(encoding, str) and encoding.lower() == "base64":
            return None
        content_text = content.get("text")
        if isinstance(content_text, str):
            return content_text
    return None


def collect_secrets(raw: dict[str, Any]) -> list[str]:
    """Return the raw (unmasked) secret VALUES the scanner detects — for redaction.

    Longest-first, so literally replacing one value never leaves a fragment of another.
    """
    log = raw.get("log")
    entries = log.get("entries") if isinstance(log, dict) else None
    entries = entries if isinstance(entries, list) else []

    values: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        req_obj = entry.get("request")
        request: dict[str, Any] = req_obj if isinstance(req_obj, dict) else {}
        resp_obj = entry.get("response")
        response: dict[str, Any] = resp_obj if isinstance(resp_obj, dict) else {}

        for container in (request, response):
            headers = container.get("headers")
            if not isinstance(headers, list):
                continue
            for header in headers:
                if not isinstance(header, dict):
                    continue
                name = str(header.get("name", "")).lower().lstrip(":")
                value = str(header.get("value", ""))
                if name in SENSITIVE_HEADERS and value:
                    values.add(value)

        query = str(request.get("url", "")).split("?", 1)
        if len(query) == 2:
            for pair in query[1].split("&"):
                key, sep, value = pair.partition("=")
                if sep and key.lower() in SENSITIVE_QUERY_KEYS and value:
                    values.add(value)

        for container in (request, response):
            body = _body_text(container)
            if not body:
                continue
            for _category, _severity, pattern in _PATTERNS:
                for match in pattern.finditer(body):
                    values.add(match.group(0))
            for match in _CREDENTIAL_FIELD.finditer(body):
                values.add(match.group(2))

    return sorted((v for v in values if v and v != REDACTED_MARKER), key=len, reverse=True)
