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

## API security

The application treats provider credentials as secrets and keeps them on the server-side/local development environment only.

- Store `ODDS_API_KEY` in `.env` or an environment-variable manager; do not place it in HTML, JavaScript, screenshots, notebooks, README files, or Git history.
- Confirm `.env` remains ignored before every push. If a secret is exposed, revoke or rotate it at the provider immediately; removing the file alone does not remove it from Git history.
- Never ask users to paste API keys, session tokens, cookies, passwords, or application keys into the dashboard or chat.
- Use HTTPS for provider requests and do not disable certificate verification.
- Use read-only credentials and delayed/development keys where the provider offers them. Do not request, store, or implement order-placement permissions for this project.
- Keep credentials out of logs, error messages, browser URLs, client-side source, and analytics payloads. Provider errors should be reduced to safe user-facing messages.
- Apply timeouts, caching, and provider rate/quota limits so refresh actions do not create uncontrolled request volume.
- Treat all API responses as untrusted input: validate required fields, prices, timestamps, team names, market types, and source identity before display or analysis.
- Keep provider data separate by event, market, outcome, source, and observation time. Do not compare incompatible markets or price directions.
- For the Betfair connector, use the delayed development key and restrict calls to market catalogue/book operations. Never add `placeOrders`, `updateOrders`, `cancelOrders`, or account-funds functionality to the demonstration.
- Use the minimum data retention necessary for the demonstration and follow the provider's terms for storage, attribution, and redistribution.

## Secret exposure response

If a credential is accidentally exposed: stop using it, revoke or rotate it at the provider, remove it from working files and Git history where appropriate, check recent repository commits, and record the incident without recording the secret itself. A repository being private or obscure is not a substitute for rotation.

## Demo limitations

This document is not a production security assessment, compliance certification, or legal opinion. It does not replace provider terms, privacy obligations, secure deployment practices, or an independent review before real-world use.
