# Skill: GDPR Assessment

## Purpose

Produce a GDPR-aligned data-handling assessment for defensive cyber triage.

## Inputs

- redacted event
- detected cyber signals
- retrieved policy context

## Required Assessment Points

- whether personal data may be involved
- lawful defensive-security purpose
- data minimisation
- confidentiality
- storage limitation
- accountability and audit evidence

## Output

Structured JSON assessment.

## Safety Rules

- Do not claim legal certification.
- Do not expose raw personal data.
- Treat IP addresses, usernames, emails, device identifiers, access logs, and authentication records as potentially personal data.
