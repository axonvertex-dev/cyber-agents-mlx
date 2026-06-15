import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.audit import audit_status, write_audit_record
from app.rag import policy_index_status, search_policy


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
FAST_MODEL = os.getenv("FAST_MODEL", "gemma4:e2b-mlx")
DEEP_MODEL = os.getenv("DEEP_MODEL", "gemma4:e4b-mlx")


api = FastAPI(
    title="Cyber Agents MLX",
    version="0.4.0",
    description="Local defensive cyber triage agents with policy RAG, GDPR, EU AI Act, and audit controls.",
)


class TriageRequest(BaseModel):
    text: str = Field(..., description="Security log, alert, or event text to triage")
    environment: Optional[str] = Field(default="", description="Local environment context")


class PolicySearchRequest(BaseModel):
    query: str
    top_k: int = 6
    balanced: bool = True


class TriageResponse(BaseModel):
    redacted_input: str
    deterministic_signals: List[str]
    policy_context: List[Dict[str, Any]]
    fast_classification: Dict[str, Any]
    gdpr_assessment: Dict[str, Any]
    eu_ai_act_assessment: Dict[str, Any]
    analyst_report: str
    safe_next_actions: List[str]
    blocked_actions_policy: str
    audit_id: str


def log_step(step: str, **data):
    payload = {
        "event": "triage_progress",
        "step": step,
        "ts": round(time.time(), 3),
        **data,
    }
    print(json.dumps(payload), flush=True)


def redact_sensitive(text: str) -> str:
    patterns = [
        (r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_ACCESS_KEY]"),
        (r"(?i)(password|passwd|pwd)\s*=\s*[^ \n\r\t]+", r"\1=[REDACTED]"),
        (r"(?i)(token|api[_-]?key|secret)\s*=\s*[^ \n\r\t]+", r"\1=[REDACTED]"),
        (r"(?i)authorization:\s*bearer\s+[a-z0-9._\-]+", "authorization: bearer [REDACTED]"),
        (r"(?i)bearer\s+[a-z0-9._\-]+", "bearer [REDACTED]"),
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]"),
        (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[REDACTED_IP]"),
        (
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            "[REDACTED_PRIVATE_KEY]",
        ),
    ]

    redacted = text
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted, flags=re.DOTALL)

    return redacted


def deterministic_signal_scan(text: str) -> List[str]:
    t = text.lower()
    signals: List[str] = []

    checks = [
        ("ssh_bruteforce_or_failed_login", ["failed password", "invalid user", "sshd"]),
        ("privilege_escalation_signal", ["sudo:", "authentication failure", "pam_unix"]),
        ("web_auth_failure", [" 401 ", " 403 ", "login failed", "unauthorized"]),
        ("sql_injection_pattern", ["' or 1=1", "union select", "sleep(", "information_schema", "--"]),
        ("path_traversal_pattern", ["../", "..\\", "%2e%2e", "/etc/passwd"]),
        ("xss_pattern", ["<script", "javascript:", "onerror=", "onload="]),
        ("log4shell_pattern", ["${jndi:", "ldap://", "rmi://"]),
        ("secret_or_token_exposure", ["password=", "token=", "api_key=", "secret=", "[redacted]"]),
        ("container_or_docker_signal", ["docker", "container", "kubernetes", "k8s", "pod"]),
        ("network_scan_signal", ["nmap", "masscan", "syn scan", "port scan"]),
        ("personal_data_possible", ["[redacted_ip]", "[redacted_email]", "user", "username", "login", "auth"]),
    ]

    for name, needles in checks:
        if any(needle in t for needle in needles):
            signals.append(name)

    return sorted(set(signals))


async def ollama_chat(model: str, system: str, user: str, temperature: float = 0.0) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    async with httpx.AsyncClient(timeout=240.0) as client:
        response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

    return data.get("message", {}).get("content", "").strip()


def parse_json_loose(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {
            "severity": "unknown",
            "category": "unknown",
            "confidence": 0.0,
            "reason": text[:500],
            "possible_false_positive": True,
        }

    try:
        return json.loads(match.group(0))
    except Exception:
        return {
            "severity": "unknown",
            "category": "unknown",
            "confidence": 0.0,
            "reason": text[:500],
            "possible_false_positive": True,
        }


def policy_filter_actions(actions: List[str]) -> List[str]:
    blocked_patterns = [
        "delete",
        "rm ",
        "wipe",
        "prune",
        "block ip",
        "iptables",
        "pfctl",
        "rotate credential",
        "restart service",
        "kill process",
        "disable account",
        "quarantine",
        "change firewall",
        "modify logs",
    ]

    safe: List[str] = []

    for action in actions:
        lower_action = action.lower()
        if any(pattern in lower_action for pattern in blocked_patterns):
            safe.append(f"Requires human approval before execution: {action}")
        else:
            safe.append(action)

    return safe


def default_safe_actions(signals: List[str], environment: str) -> List[str]:
    actions = [
        "Preserve the suspicious log or alert as evidence.",
        "Check timestamp, source, target service, and repeated patterns.",
        "Correlate with recent authentication, web, container, and system logs.",
        "Use read-only commands only during initial triage.",
        "Escalate to a human operator before containment or configuration changes.",
    ]

    if "ssh_bruteforce_or_failed_login" in signals:
        actions.append("Read-only check: review SSH/authentication logs around the timestamp.")

    if "web_auth_failure" in signals or "sql_injection_pattern" in signals:
        actions.append("Read-only check: review web access logs around the suspicious request.")

    if "secret_or_token_exposure" in signals:
        actions.append(
            "Treat exposed secrets as sensitive. Do not print or share raw values. Human approval is required before rotation."
        )

    if "container_or_docker_signal" in signals:
        actions.append("Read-only check: inspect container metadata and recent container logs.")

    if environment and "macos" in environment.lower():
        actions.append("Read-only macOS check: log show --last 1h --predicate 'eventMessage CONTAINS \"auth\"'")

    actions.append("Do not delete files, reset services, block IPs, or rotate credentials without approval.")

    return policy_filter_actions(actions)


def build_policy_query(redacted: str, signals: List[str], environment: str) -> str:
    return "\n".join([
        "Policy retrieval query for defensive cyber triage.",
        f"Environment: {environment}",
        f"Signals: {', '.join(signals)}",
        "Need: GDPR personal data handling, data minimisation, confidentiality, security logging, accountability, EU AI Act human oversight, transparency, high-risk AI controls, and cybersecurity robustness.",
        f"Redacted event: {redacted[:1200]}",
    ])


def gdpr_assess(
    redacted: str,
    signals: List[str],
    policy_context: List[Dict[str, Any]],
) -> Dict[str, Any]:
    personal_data_involved = (
        "personal_data_possible" in signals
        or "[REDACTED_IP]" in redacted
        or "[REDACTED_EMAIL]" in redacted
    )

    return {
        "personal_data_involved": personal_data_involved,
        "lawful_purpose": "defensive cybersecurity triage and incident response support",
        "data_minimisation": "raw identifiers are redacted before model reasoning where possible",
        "confidentiality": "secrets, tokens, passwords, IP addresses, emails, and private keys are redacted by policy",
        "storage_limitation": "audit records should contain redacted event data and policy references only",
        "accountability": "an audit_id is generated for this triage decision",
        "legal_certification": "not_claimed",
        "policy_sources_used": sorted({p.get("policy_family", "UNKNOWN") for p in policy_context}),
    }


def eu_ai_act_assess(
    signals: List[str],
    policy_context: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "system_role": "AI-assisted defensive cybersecurity decision support",
        "autonomous_action_allowed": False,
        "human_oversight_required": True,
        "prohibited_use_detected": False,
        "transparency_note": "The output is an AI-assisted triage recommendation, not an autonomous enforcement action.",
        "logging_required": True,
        "legal_certification": "not_claimed",
        "policy_sources_used": sorted({p.get("policy_family", "UNKNOWN") for p in policy_context}),
    }


@api.get("/health")
async def health():
    ollama_reachable = False
    models = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            ollama_reachable = response.status_code == 200

            if ollama_reachable:
                models = [m.get("name") for m in response.json().get("models", [])]
    except Exception:
        ollama_reachable = False

    return {
        "service": "cyber-agents-mlx",
        "version": "0.4.0",
        "ollama_base_url": OLLAMA_BASE_URL,
        "ollama_reachable": ollama_reachable,
        "available_models": models,
        "fast_model": FAST_MODEL,
        "deep_model": DEEP_MODEL,
        "policy_index": policy_index_status(),
        "audit": audit_status(),
    }


@api.get("/policy/status")
async def policy_status():
    return policy_index_status()


@api.post("/policy/search")
async def policy_search(req: PolicySearchRequest):
    return {
        "query": req.query,
        "top_k": req.top_k,
        "balanced": req.balanced,
        "results": await search_policy(req.query, req.top_k, req.balanced),
    }


@api.get("/audit/status")
async def get_audit_status():
    return audit_status()


@api.get("/agents")
async def agents():
    return {
        "agents": [
            "redaction_agent",
            "signal_scanner_agent",
            "policy_retrieval_agent",
            "fast_classifier_agent",
            "gdpr_policy_agent",
            "eu_ai_act_policy_agent",
            "cyber_triage_agent",
            "compliance_guard_agent",
        ]
    }


@api.post("/triage", response_model=TriageResponse)
async def triage(req: TriageRequest):
    log_step("triage_started", environment=req.environment or "")
    redacted = redact_sensitive(req.text)
    log_step("redaction_done", redacted_chars=len(redacted))
    signals = deterministic_signal_scan(redacted)
    log_step("signal_scan_done", signals=signals)

    policy_query = build_policy_query(redacted, signals, req.environment or "")
    policy_context = await search_policy(policy_query, top_k=6, balanced=True)
    log_step("policy_search_done", policy_chunks=len(policy_context), families=sorted({p.get("policy_family", "UNKNOWN") for p in policy_context}))

    classifier_system = """You are a defensive cybersecurity classifier.
Return compact JSON only.
Allowed severity values: low, medium, high, critical.
Do not recommend destructive actions.
Do not provide offensive exploitation instructions.
"""

    classifier_user = f"""
Environment:
{req.environment}

Redacted event:
{redacted}

Deterministic signals:
{signals}

Retrieved policy context:
{json.dumps(policy_context[:4], indent=2)}

Return JSON only:
{{
  "severity": "low|medium|high|critical",
  "category": "short category",
  "confidence": 0.0,
  "reason": "brief reason",
  "possible_false_positive": true
}}
"""

    raw_classification = await ollama_chat(
        model=FAST_MODEL,
        system=classifier_system,
        user=classifier_user,
        temperature=0.0,
    )

    classification = parse_json_loose(raw_classification)
    log_step("fast_classifier_done", severity=classification.get("severity"), category=classification.get("category"))

    gdpr = gdpr_assess(redacted, signals, policy_context)
    eu_ai = eu_ai_act_assess(signals, policy_context)

    analyst_system = """You are a defensive cyber triage analyst.
Follow the provided internal policy, GDPR-aligned controls, and EU AI Act-aligned controls.
Do not provide exploit instructions.
Do not recommend deletion, blocking, credential rotation, service restart, or containment without human approval.
Focus on read-only triage, evidence preservation, privacy, and auditability.
"""

    analyst_user = f"""
Environment:
{req.environment}

Redacted event:
{redacted}

Signals:
{signals}

Fast classification:
{json.dumps(classification, indent=2)}

Retrieved policy context:
{json.dumps(policy_context, indent=2)}

GDPR assessment:
{json.dumps(gdpr, indent=2)}

EU AI Act assessment:
{json.dumps(eu_ai, indent=2)}

Write a concise analyst report with:
1. likely incident meaning
2. why the severity is appropriate
3. GDPR/data handling note
4. EU AI Act/human oversight note
5. safe read-only next steps
"""

    log_step("deep_analyst_started", model=DEEP_MODEL)
    analyst_report = await ollama_chat(
        model=DEEP_MODEL,
        system=analyst_system,
        user=analyst_user,
        temperature=0.1,
    )

    safe_actions = default_safe_actions(signals, req.environment or "")

    blocked_policy = (
        "Autonomous destructive, exploitative, credential-stealing, privacy-invasive, or non-approved "
        "modification actions are blocked. Read-only triage is allowed. Human approval is required before "
        "containment, deletion, blocking, credential rotation, service restart, account disablement, "
        "quarantine, log modification, firewall changes, or infrastructure modification."
    )

    log_step("audit_write_started")
    audit_id = write_audit_record({
        "event_type": "policy_aware_triage",
        "environment": req.environment,
        "redacted_input": redacted,
        "deterministic_signals": signals,
        "policy_context": policy_context,
        "fast_classification": classification,
        "gdpr_assessment": gdpr,
        "eu_ai_act_assessment": eu_ai,
        "analyst_report": analyst_report,
        "safe_next_actions": safe_actions,
        "blocked_actions_policy": blocked_policy,
    })

    log_step("triage_complete", audit_id=audit_id)

    return TriageResponse(
        redacted_input=redacted,
        deterministic_signals=signals,
        policy_context=policy_context,
        fast_classification=classification,
        gdpr_assessment=gdpr,
        eu_ai_act_assessment=eu_ai,
        analyst_report=analyst_report,
        safe_next_actions=safe_actions,
        blocked_actions_policy=blocked_policy,
        audit_id=audit_id,
    )


@api.post("/triage/fast", response_model=TriageResponse)
async def triage_fast(req: TriageRequest):
    """
    Fast demo endpoint.

    Uses deterministic controls, policy RAG, and the fast classifier model only.
    It avoids the deeper analyst model, so it is better for live workshops.
    """
    log_step("triage_fast_started", environment=req.environment or "")
    redacted = redact_sensitive(req.text)
    log_step("redaction_done", redacted_chars=len(redacted))
    signals = deterministic_signal_scan(redacted)
    log_step("signal_scan_done", signals=signals)

    policy_query = build_policy_query(redacted, signals, req.environment or "")
    policy_context = await search_policy(policy_query, top_k=6, balanced=True)
    log_step(
        "policy_search_done",
        policy_chunks=len(policy_context),
        families=sorted({p.get("policy_family", "UNKNOWN") for p in policy_context}),
    )

    classifier_system = """You are a defensive cybersecurity classifier.
Return compact JSON only.
Allowed severity values: low, medium, high, critical.
Do not recommend destructive actions.
Do not provide offensive exploitation instructions.
"""

    classifier_user = f"""
Environment:
{req.environment}

Redacted event:
{redacted}

Deterministic signals:
{signals}

Retrieved policy context:
{json.dumps(policy_context[:4], indent=2)}

Return JSON only:
{{
  "severity": "low|medium|high|critical",
  "category": "short category",
  "confidence": 0.0,
  "reason": "brief reason",
  "possible_false_positive": true
}}
"""

    raw_classification = await ollama_chat(
        model=FAST_MODEL,
        system=classifier_system,
        user=classifier_user,
        temperature=0.0,
    )

    classification = parse_json_loose(raw_classification)
    log_step("fast_classifier_done", severity=classification.get("severity"), category=classification.get("category"))

    gdpr = gdpr_assess(redacted, signals, policy_context)
    eu_ai = eu_ai_act_assess(signals, policy_context)
    safe_actions = default_safe_actions(signals, req.environment or "")

    blocked_policy = (
        "Autonomous destructive, exploitative, credential-stealing, privacy-invasive, or non-approved "
        "modification actions are blocked. Read-only triage is allowed. Human approval is required before "
        "containment, deletion, blocking, credential rotation, service restart, account disablement, "
        "quarantine, log modification, firewall changes, or infrastructure modification."
    )

    analyst_report = "\n".join([
        "## Fast Defensive Triage Report",
        "",
        f"Severity: {classification.get('severity', 'unknown')}",
        f"Category: {classification.get('category', 'unknown')}",
        f"Reason: {classification.get('reason', 'No model reason returned.')}",
        "",
        "GDPR/Data Handling: The event was redacted before model reasoning where possible. "
        "If identifiers or authentication records are present, treat them as personal data and restrict access to audit evidence.",
        "",
        "EU AI Act/Human Oversight: This is AI-assisted decision support. Autonomous containment or infrastructure modification is not allowed.",
        "",
        "Safe next steps are restricted to read-only triage and human-approved escalation.",
    ])

    log_step("audit_write_started")
    audit_id = write_audit_record({
        "event_type": "policy_aware_triage_fast",
        "environment": req.environment,
        "redacted_input": redacted,
        "deterministic_signals": signals,
        "policy_context": policy_context,
        "fast_classification": classification,
        "gdpr_assessment": gdpr,
        "eu_ai_act_assessment": eu_ai,
        "analyst_report": analyst_report,
        "safe_next_actions": safe_actions,
        "blocked_actions_policy": blocked_policy,
    })

    log_step("triage_fast_complete", audit_id=audit_id)

    return TriageResponse(
        redacted_input=redacted,
        deterministic_signals=signals,
        policy_context=policy_context,
        fast_classification=classification,
        gdpr_assessment=gdpr,
        eu_ai_act_assessment=eu_ai,
        analyst_report=analyst_report,
        safe_next_actions=safe_actions,
        blocked_actions_policy=blocked_policy,
        audit_id=audit_id,
    )
