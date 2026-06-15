# Agents

This directory represents the logical agent registry for the training lab. In V1 the orchestration is implemented deterministically in `app/main.py`, while these directories document the intended agent boundaries.

Logical agents:

- `cyber_triage`
- `policy_retrieval`
- `policy_ingestion`
- `gdpr_policy`
- `eu_ai_act_policy`
- `compliance_guard`

The project intentionally uses a deterministic orchestrator instead of allowing a model to freely plan tool execution.
