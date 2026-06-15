import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


AUDIT_LOG_DIR = Path(os.getenv("AUDIT_LOG_DIR", "/app/audit_logs"))


def write_audit_record(record: Dict[str, Any]) -> str:
    """
    Write one immutable JSON audit record.

    The audit log stores redacted/security metadata only.
    It should not be used to store raw secrets, raw passwords, private keys,
    or unredacted source logs.
    """
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)

    audit_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    final_record = {
        "audit_id": audit_id,
        "created_at": created_at,
        **record,
    }

    path = AUDIT_LOG_DIR / f"{audit_id}.json"
    path.write_text(json.dumps(final_record, indent=2, ensure_ascii=False))

    return audit_id


def read_audit_record(audit_id: str) -> Dict[str, Any]:
    """
    Read one audit record by ID.

    Only UUID-style IDs are accepted to avoid path traversal.
    """
    try:
        uuid.UUID(audit_id)
    except ValueError:
        raise ValueError("Invalid audit_id")

    path = AUDIT_LOG_DIR / f"{audit_id}.json"

    if not path.exists():
        raise FileNotFoundError(f"Audit record not found: {audit_id}")

    return json.loads(path.read_text())


def audit_status() -> Dict[str, Any]:
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(AUDIT_LOG_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)

    return {
        "audit_log_dir": str(AUDIT_LOG_DIR),
        "exists": AUDIT_LOG_DIR.exists(),
        "record_count": len(files),
        "latest_records": [p.name for p in files[-5:]],
    }
