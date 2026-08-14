# Security Policy

AEP AI accepts vulnerability reports through this repository's private GitHub
**Security → Report a vulnerability** form. Do not open a public issue or
include real credentials, private keys, signed payloads, personal data, or
production infrastructure details.

The current `main` branch and latest Developer Preview release are supported.
Reports should include the affected version, reproduction steps, and impact.
Testing must not target hosted production systems, disrupt service, or access
third-party data. See [aepai.org](https://aepai.org) for official project
info…5022 tokens truncated… r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b([A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD|PRIVATE_KEY)"
    r"\s*=\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
)


def _is_sensitive_key(key: str) -> bool:
    if _SENSITIVE_KEY.search(key):
        return True
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key)
    words = re.sub(r"[^A-Za-z0-9]+", " ", words).casefold().split()
    return any(
        item in words
        for item in (
            "authorization",
            "bearer",
            "cookie",
            "credential",
            "password",
            "secret",
            "seed",
            "signature",
            "token",
        )
    ) or any(
        left in ("api", "private") and right == "key" for left, right in pairwise(words)
    )


class SecretValue:
    """Non-public, redacted credential storage with explicit transport access."""

    __slots__ = ("__value",)

    def __init__(self, value: str) -> None:
        normalized = value.strip()
        if not normalized:
            raise ValueError("AEP API key is required")
        self.__value = normalized

    def _reveal_for_transport(self) -> str:
        return self.__value

    def __repr__(self) -> str:
        return f"SecretValue({MASKED_CREDENTIAL!r})"

    def __str__(self) -> str:
        return MASKED_CREDENTIAL

    def __getstate__(self) -> dict[str, str]:
        return {"value": MASKED_CREDENTIAL}

    def __deepcopy__(self, memo: dict[int, Any]) -> "SecretValue":
        del memo
        return SecretValue(MASKED_CREDENTIAL)


def redact_text(value: str, *, known_secrets: Sequence[str] = ()) -> str:
    redacted = value
    for secret in sorted(
        {item for item in known_secrets if item}, key=len, reverse=True
    ):
        redacted = redacted.replace(secret, MASKED_CREDENTIAL)
    redacted = _PRIVATE_KEY.sub(MASKED_CREDENTIAL, redacted)
    redacted = _AUTHORIZATION.sub(rf"\1{MASKED_CREDENTIAL}", redacted)
    redacted = _AUTH_SCHEME.sub(rf"\1{MASKED_CREDENTIAL}", redacted)
    redacted = _AEP_KEY.sub(MASKED_CREDENTIAL, redacted)
    return _SECRET_ASSIGNMENT.sub(rf"\1{MASKED_CREDENTIAL}", redacted)


def redact_value(
    value: Any,
    *,
    key: str = "",
    known_secrets: Sequence[str] = (),
    _depth: int = 0,
) -> Any:
    if key and _is_sensitive_key(key):
        return MASKED_CREDENTIAL
    if _depth >= 8:
        return "[TRUNCATED]"
    if isinstance(value, Mapping):
        return {
            str(item_key): redact_value(
                item_value,
                key=str(item_key),
                known_secrets=known_secrets,
                _depth=_depth + 1,
            )
            for item_key, item_value in list(value.items())[:100]
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [
            redact_value(item, known_secrets=known_secrets, _depth=_depth + 1)
            for item in value[:100]
        ]
    if isinstance(value, str):
        return redact_text(value, known_secrets=known_secrets)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return redact_text(str(value), known_secrets=known_secrets)
