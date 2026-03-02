# Threat Model

## Scope

PromptForge is a developer tool. The primary threat surface is:
1. Prompt injection via dataset inputs.
2. Sensitive data leakage via judge rationales.
3. Supply chain risks (dependencies).

## Threat 1: Prompt Injection in Judge

**Risk:** A malicious dataset case input could inject instructions into the judge prompt, corrupting scores.

**Mitigations:**
- Judge prompt wraps user input in explicit delimiters.
- Input length is capped before injection.
- Rationales are reviewed by humans before being trusted.

## Threat 2: PII in Rationales

**Risk:** Judge rationales may echo PII from input cases.

**Mitigations:**
- `utils/redaction.py` redacts common PII patterns before storage.
- Datasets should use synthetic or anonymised data (documented in `datasets.md`).

## Threat 3: API Key Exposure

**Risk:** API keys in `.env` or logs.

**Mitigations:**
- `.env` is in `.gitignore`.
- Keys are never logged or stored in SQLite.
- CI uses GitHub Secrets for API keys.

## Threat 4: Dependency Vulnerabilities

**Mitigations:**
- `pip audit` runs in CI.
- Dependencies are pinned in `pyproject.toml`.

## Out of Scope

- Multi-tenant deployments.
- Network-level attacks.
- Model-level adversarial attacks.