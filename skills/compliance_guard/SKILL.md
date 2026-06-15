# Skill: Compliance Guard

## Purpose

Ensure the final triage output respects internal policy, GDPR-aligned privacy constraints, and EU AI Act-aligned human oversight controls.

## Inputs

- model classification
- analyst report
- proposed next actions
- policy context

## Allowed Output

- read-only investigation steps
- evidence preservation guidance
- escalation to human operator
- privacy-preserving handling notes
- audit references

## Blocked Output

- autonomous deletion
- log modification
- firewall rule changes
- IP blocking
- credential rotation
- account disablement
- system quarantine
- production restarts
- exploit chains
- malware or evasion guidance

## Rule

If an action can affect systems, evidence, accounts, credentials, network policy, or availability, it requires explicit human approval.
