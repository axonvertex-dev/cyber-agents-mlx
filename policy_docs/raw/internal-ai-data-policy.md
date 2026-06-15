# Internal AI and Data Policy for Cyber Agents MLX

## Scope

This policy applies to the Cyber Agents MLX local defensive cybersecurity agent system.

The system performs defensive security triage only. It must not perform offensive security, exploit execution, credential theft, destructive changes, or autonomous containment.

## Default Operating Mode

The default mode is read-only defensive triage.

The system may:
- inspect logs supplied by the user
- redact sensitive data
- classify security events
- retrieve policy context
- produce safe next actions
- create audit records
- recommend human approval before risky steps

The system must not:
- delete files
- delete logs
- wipe evidence
- modify firewall rules
- block IP addresses automatically
- rotate credentials automatically
- restart production services automatically
- change file ownership or permissions automatically
- execute exploit chains
- provide malware or evasion instructions

## GDPR-Aligned Controls

The system must follow these operational controls:
- data minimisation: only process data needed for triage
- purpose limitation: use security logs only for defensive security analysis
- confidentiality: redact secrets, tokens, passwords, IP addresses, emails, and private keys before model reasoning where possible
- accountability: create an audit record for every policy-aware triage decision
- storage limitation: store only redacted event summaries and policy references unless explicit retention is approved
- integrity: preserve original evidence outside the agent workflow and do not alter source logs

## Personal Data Handling

Security logs may contain personal data, including:
- IP addresses
- usernames
- email addresses
- device identifiers
- authentication records
- access logs

When personal data may be present, the agent must:
- redact obvious personal data from model prompts
- avoid unnecessary repetition of identifiers
- recommend restricted access to audit records
- preserve evidence without modifying source logs
- require human approval before sharing or exporting data

## EU AI Act-Aligned Controls

The system must maintain:
- human oversight for impactful security decisions
- logging of agent decisions
- transparency that this is an AI-assisted triage system
- clear separation between recommendation and execution
- no autonomous destructive action
- no prohibited AI use such as social scoring, biometric categorisation, or manipulative profiling

## Human Approval Required Before

Human approval is required before:
- blocking IP addresses
- deleting or modifying logs
- changing firewall rules
- changing SSH configuration
- rotating credentials
- disabling accounts
- quarantining machines
- restarting production services
- making irreversible infrastructure changes

## Output Requirements

Every policy-aware triage response must include:
- redacted input
- detected cyber signals
- retrieved policy context
- GDPR assessment
- EU AI Act assessment
- safe next actions
- blocked action policy
- audit ID
