# Secrets Management

## Rules

- Do not commit `.env` or any file containing live API keys, tokens, or passwords.
- Commit only templates such as `.env.example`.
- Treat any exposed key as compromised, even if it was only shared internally.
- Rotate secrets immediately after exposure.

## Local Development

1. Copy the template:

```bash
cp .env.example .env
```

2. Fill in real values only in `.env`.

3. Keep `.env` local to your machine.

## Required Variables

- `DATABASE_URL`: PostgreSQL connection string for the backend.
- `GROQ_API_KEY`: required for the Q&A and draft endpoints.
- `OPENAI_API_KEY`: optional unless a specific workflow depends on it.

## If A Secret Is Exposed

1. Revoke the exposed key in the provider console.
2. Create a replacement key.
3. Update your local `.env`.
4. Check logs, screenshots, docs, and shell history for further leakage.
5. If the secret was ever committed, remove it from git history before sharing the repository further.

## Repository Hygiene

- `.env` must stay in `.gitignore`.
- Documentation and code samples must use placeholders, never real values.
- Review pull requests for copied terminal output, screenshots, or config snippets that may include secrets.
