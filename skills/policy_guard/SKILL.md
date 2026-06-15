# Skill: Policy Guard

## Purpose

Filter unsafe cybersecurity actions from agent output.

## Allowed

- read-only commands
- log review
- evidence preservation
- human approval checkpoints
- local defensive triage

## Blocked

- rm -rf
- docker compose down -v
- docker system prune
- kubectl delete
- chmod 777
- chown -R
- curl | sh
- wget | bash
- nc -e
- exploit execution
- credential extraction
- offensive scanning against third-party systems

## Rule

When uncertain, downgrade to read-only investigation and require human approval.
