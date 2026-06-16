from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any, Optional

try:  # pragma: no cover - defensive import
    from .localization import (
        build_detailed_parts,
        localize_due_phrase,
        L,
    )
except Exception:  # noqa: BLE001
    build_detailed_parts = None  # type: ignore


def friendly_due_phrase(iso_dt: str) -> str:
    try:
        cleaned = iso_dt.rstrip("Z")
        dt = None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(cleaned, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            return iso_dt
        today = datetime.now().date()
        ddate = dt.date()
        delta_days = (ddate - today).days
        if delta_days == 0:
            return "today"
        if delta_days == 1:
            return "tomorrow"
        if delta_days < 0:
            return "overdue"
        if 2 <= delta_days < 365:
            return f"in {delta_days} days"
        years = delta_days // 365
        year_word = "year" if years == 1 else "years"
        return f"in {years} {year_word} ({delta_days} days)"
    except Exception:  # noqa: BLE001
        return iso_dt


def friendly_recurrence_phrase(recurrence_type: str, interval: int = 1) -> Optional[str]:
    if not recurrence_type or recurrence_type == "none":
        return None
    if interval == 1:
        return f"repeats {recurrence_type}"
    return f"repeats every {interval} {recurrence_type}"


def build_detailed_response(
    task_name: str,
    task_data: Dict[str, Any],
    projects: List[Dict[str, Any]] | None,
    tag_names: List[str],
    lang: str | None = None,
) -> str:
    project_name: Optional[str] = None
    try:
        project_id = task_data.get("project_id")
        if project_id:
            proj_lookup: Dict[int, str] = {
                p["id"]: p.get("name", "")
                for p in (projects or [])
                if isinstance(p, dict) and p.get("id") is not None
            }
            raw_name = proj_lookup.get(project_id, "")
            if raw_name and raw_name.lower() not in {"other", "misc", "general"}:
                project_name = raw_name
    except Exception:  # noqa: BLE001
        project_name = None

    tags_part: Optional[str] = None
    try:
        visible = [n for n in (tag_names or []) if n.lower() != "voice"]
        if visible:
            tags_part = ", ".join(visible)
    except Exception:  # noqa: BLE001
        tags_part = None

    due_phrase: Optional[str] = None
    due_date = task_data.get("due_date")
    if due_date:
        base_due = friendly_due_phrase(due_date)
        if lang and lang != "en" and build_detailed_parts:
            try:
                due_phrase = localize_due_phrase(base_due, lang)  # type: ignore
            except Exception:  # noqa: BLE001
                due_phrase = base_due
        else:
            due_phrase = base_due

    priority_word: Optional[str] = None
    try:
        priority = task_data.get("priority")
        if isinstance(priority, str) and priority in {"low", "medium", "high"}:
            priority_word = priority
    except Exception:  # noqa: BLE001
        priority_word = None

    repeat_phrase: Optional[str] = None
    try:
        recurrence_type = task_data.get("recurrence_type")
        recurrence_interval = task_data.get("recurrence_interval", 1)
        repeat_phrase = friendly_recurrence_phrase(recurrence_type, recurrence_interval)
    except Exception:  # noqa: BLE001
        repeat_phrase = None

    if lang and lang != "en" and build_detailed_parts:
        parts = build_detailed_parts(
            lang=lang,
            project_name=project_name,
            labels_part=tags_part,
            due_phrase=due_phrase,
            assignee=None,
            priority_word=priority_word,
            repeat_phrase=repeat_phrase,
        )
        suffix = " (" + "; ".join(parts) + ")" if parts else ""
        try:
            prefix = L("success_added", lang, title=task_name)  # type: ignore
            return f"{prefix}{suffix}"
        except Exception:  # noqa: BLE001
            pass
        return f"Successfully added task: {task_name}{suffix}"

    details_parts: List[str] = []
    if project_name:
        details_parts.append(f"project '{project_name}'")
    if tags_part:
        details_parts.append("tags: " + tags_part)
    if due_phrase:
        details_parts.append(f"due {due_phrase}")
    if priority_word:
        details_parts.append(f"priority {priority_word}")
    if repeat_phrase:
        details_parts.append(repeat_phrase)
    suffix = " (" + "; ".join(details_parts) + ")" if details_parts else ""
    return f"Successfully added task: {task_name}{suffix}"
