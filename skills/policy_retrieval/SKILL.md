# Skill: Policy Retrieval

## Purpose

Retrieve relevant governance, privacy, and internal safety policy context for cyber triage.

## Inputs

- redacted security event
- deterministic cyber signals
- environment label
- policy query

## Retrieval Method

- semantic embedding search
- BM25-style keyword score
- family balancing across internal policy, GDPR, EU AI Act, and GPAI guidance

## Output

Return a compact list of policy chunks with source, family, page, section title, scores, and excerpt.

## Safety Rules

- Retrieve policy context only.
- Do not execute tools.
- Do not retrieve or expose raw secrets.
- Prefer redacted event context.
