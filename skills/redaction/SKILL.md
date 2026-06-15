# Skill: Redaction

## Purpose

Remove sensitive information before sending text to the model.

## Inputs

- raw log line
- alert text
- terminal output
- incident note

## Redaction Targets

- passwords
- API keys
- bearer tokens
- AWS access keys
- private keys
- emails
- IP addresses
- obvious secrets

## Output

A redacted text block safe for model reasoning.

## Safety Rules

- Never reveal original secrets.
- Never reconstruct redacted secrets.
- Preserve enough context for security triage.
