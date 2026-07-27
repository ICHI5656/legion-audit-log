# Public Audit Log Sanitization Policy

This repository is public. Every committed file must be safe for unrestricted
public reading.

## Prohibited

Never commit:

- API keys, access tokens, passwords, passphrases, session secrets, or private
  keys;
- infrastructure addresses, host names, connection strings, internal URLs, or
  authentication material;
- customer data, personal information, email addresses, or raw business data;
- database credentials or project connection details;
- unpublished source code copied from a private repository;
- raw prompts, logs, screenshots, documents, or payloads that may contain any
  prohibited information.

Do not publish a sensitive value merely because it has already appeared in a
terminal, chat, issue, or private repository.

## Permitted

The intended public record is limited to:

- sanitized progress summaries;
- decisions and approval state;
- non-sensitive rationale and evidence descriptions;
- cryptographic digests that cannot reconstruct source content;
- escalation labels such as `auto_possible`, `human_required`,
  `blocked_external`, and `frozen_out_of_scope`.

Use an abstract reference name or digest when a decision depends on private
evidence.

## Fail-Closed Publication Rule

Run `python3 scripts/scan-public-content.py --all` before every push. The
repository pre-push hook enforces this scan after
`./scripts/install-hooks.sh` has been run.

If the scanner reports any finding:

1. do not push;
2. remove or replace the sensitive content at its source;
3. rerun the complete scan;
4. publish only after the scan exits successfully.

Scanner success is necessary but not sufficient. The author must still review
the diff because automated detection cannot prove that prose is safe.
