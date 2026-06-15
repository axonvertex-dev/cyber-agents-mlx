# Skill: Classification

## Purpose

Classify defensive cybersecurity events.

## Categories

- ssh_bruteforce_or_failed_login
- privilege_escalation_signal
- web_auth_failure
- sql_injection_pattern
- path_traversal_pattern
- xss_pattern
- log4shell_pattern
- secret_or_token_exposure
- container_or_docker_signal
- network_scan_signal
- benign_or_noise
- unknown

## Severity

Use one of:

- benign
- low
- medium
- high
- critical

## Output Format

The fast classifier must return JSON:

{
  "severity": "medium",
  "category": "ssh_bruteforce_or_failed_login",
  "confidence": 0.8,
  "reason": "Short explanation",
  "possible_false_positive": false
}

## Safety Rules

- Defensive classification only.
- Do not provide exploit instructions.
- Do not suggest attacking systems.
