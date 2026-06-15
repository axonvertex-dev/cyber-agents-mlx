# Skill: Defensive Cyber Analysis

## Purpose

Explain a security event and provide safe investigation steps.

## Required Structure

1. What this likely means
2. Why it matters
3. Immediate read-only checks
4. Containment decision criteria
5. Human approval required before

## Allowed Recommendations

- preserve logs
- inspect logs
- check timestamps
- correlate events
- review authentication history
- review Docker container status
- review web access logs
- escalate to human operator

## Blocked Recommendations

- delete logs
- wipe files
- disable security tooling
- exploit a target
- steal credentials
- run malware
- scan third-party infrastructure
- modify firewall rules without approval
