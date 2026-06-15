# Training Context

This project is one module in a larger hands-on training:

```text
Building, Securing, and Deploying AI Agent Swarms in a Trustless Decentralized Ecosystem
```

The broader training addresses how AppSec teams can use agentic workflows to triage vulnerability reports, incident tickets, logs, stack traces, and chat transcripts that may contain PII, secrets, and sensitive internal context.

## Risk framing

When RAG and autonomous tool use are added, the attack surface expands:

- prompt injection can trigger unsafe actions;
- sensitive data can leak through memory, RAG, or tool outputs;
- agents can be spoofed or tampered with;
- controls can be bypassed;
- auditability can be lost.

## This lab's scope

This repo implements the Apple Silicon local lab:

```text
Policy-governed, privacy-preserving AppSec triage agent
```

It focuses on:

- local open model serving through native Ollama/MLX;
- Dockerized API workflow;
- privacy-preserving redaction;
- policy RAG over GDPR and EU AI Act material;
- no autonomous destructive action;
- auditable evidence bundles.

## Future modules kept separate

- Ollama/MLX installation and serving guide.
- Cisco Foundation Sec 8B reasoning project.
- Cloudflare Zero Trust deployment.
- Colab prototype.
- Multi-node decentralized swarm orchestration.
- Remediation PR generation and sandboxed code changes.
