# GitHub Preparation

This repo is ready to publish after you choose the final GitHub repository name and license.

## Before pushing

Check the files that should not be committed:

```bash
git status --ignored
```

Confirm these are ignored:

```text
.env
audit_logs/*.json
policy_docs/index/*.json
policy_docs/index/*.jsonl
policy_docs/raw/*.pdf
```

## Recommended repository name

```text
cyber-agents-mlx
```

Alternative names:

```text
secure-appsec-triage-mlx
policy-aware-cyber-triage-mlx
apple-mlx-cyber-agents
```

## GitHub token note

For pushing from the terminal over HTTPS, use a GitHub Personal Access Token instead of your account password. Prefer a fine-grained token restricted to this repository with content read/write permission only.

Do not commit the token into `.env`, docs, scripts, shell history examples, or notebooks.

## Initial local git commands

```bash
git init
git add .
git status
git commit -m "Initial policy-aware cyber agents MLX lab"
```

After creating the empty GitHub repo:

```bash
git branch -M main
git remote add origin https://github.com/<YOUR_USER_OR_ORG>/cyber-agents-mlx.git
git push -u origin main
```

When prompted for credentials, use your GitHub username and the token as the password.
