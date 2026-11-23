"""Small helpers shared by the Agents Registry's domain services."""

import re
from datetime import date, datetime
from typing import Optional

from openg2p_registry_core.errors import G2PRegistryErrorCodes, G2PRegistryException

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE = re.compile(r"^\+?[0-9 ]{7,20}$")


def invalid(message: str) -> None:
    raise G2PRegistryException(code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1], message=message)


def as_date(record: dict, key: str) -> Optional[date]:
    value = record.get(key)
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        invalid(f"{key} must be a date (YYYY-MM-DD)")


def as_int(record: dict, key: str) -> Optional[int]:
    value = record.get(key)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        invalid(f"{key} must be a whole number")


def joined(payload: dict, keys: list[str], extra: Optional[list] = None) -> str:
    parts = [str(value).strip() for value in (extra or []) if str(value).strip()]
    parts += [str(payload.get(key)).strip() for key in keys if str(payload.get(key) or "").strip()]
    return " ".join(parts).strip()
