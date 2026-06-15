# Understanding the Result

The `/triage` and `/triage/fast` endpoints return a policy-aware triage object.

## Main response fields

| Field | Meaning |
|---|---|
| `redacted_input` | Input after obvious secrets, IPs, emails, and keys are masked |
| `deterministic_signals` | Rule-based cyber signals found in the event |
| `policy_context` | Retrieved policy chunks from internal policy, GDPR, EU AI Act, and GPAI guidance |
| `fast_classification` | Model-produced severity/category JSON |
| `gdpr_assessment` | Data-protection assessment for the event |
| `eu_ai_act_assessment` | AI-governance and human-oversight assessment |
| `analyst_report` | Human-readable defensive triage explanation |
| `safe_next_actions` | Read-only and human-reviewed next steps |
| `blocked_actions_policy` | Explanation of blocked autonomous actions |
| `audit_id` | UUID of the JSON audit evidence record |

## Example result summary

For the SSH failed-login example, the system produced:

```text
redacted IP: yes
redacted password: yes
redacted token: yes
detected SSH failed login: yes
detected possible personal data: yes
detected secret/token exposure: yes
retrieved policy families: INTERNAL_POLICY, GDPR, EU_AI_ACT, EU_AI_ACT_GPAI_GUIDANCE
classification: medium / Authentication Attempt
autonomous action allowed: false
human oversight required: true
audit record written: yes
```

## Why medium severity?

A failed SSH login from an external IP is suspicious and may indicate brute-force activity or reconnaissance. It is not automatically critical because the example does not show successful compromise, privilege escalation, malware execution, or lateral movement.

## Why GDPR appears

Security logs may include personal data such as IP addresses, usernames, device identifiers, and authentication records. The workflow redacts identifiers before model reasoning where possible and stores only redacted information in audit records.

## Why EU AI Act appears

The workflow is AI-assisted decision support. It explicitly distinguishes recommendation from execution, logs decisions, and requires human oversight before impactful security actions.

## Audit evidence

Audit JSON files are written locally under:

```text
audit_logs/
```

They are not committed to GitHub. A typical audit record includes:

```text
audit_id
created_at
event_type
environment
redacted_input
deterministic_signals
policy_context
fast_classification
gdpr_assessment
eu_ai_act_assessment
analyst_report
safe_next_actions
blocked_actions_policy
```
