# Security Model

This is a lightweight security model for a personal demonstration project.

## Assets to protect

- API keys, tokens, and account credentials
- Local configuration and environment files
- Personal information
- Data subject to provider restrictions
- GitHub account and repository access

## Controls

- Store secrets in environment variables or a local secrets file excluded by `.gitignore`.
- Never commit passwords, tokens, cookies, or private keys.
- Use least-privilege, read-only access where a source supports it.
- Validate and normalise external data before analysis.
- Record source, timestamp, timezone, and transformation history.
- Treat downloaded files and external content as untrusted input.
- Review dependencies and keep them updated.
- Use pull requests or a separate branch before significant changes.
- Run tests before committing changes.

## Demo limitations

This document is not a production security assessment, compliance certification, or legal opinion. It does not replace provider terms, privacy obligations, secure deployment practices, or an independent review before real-world use.
