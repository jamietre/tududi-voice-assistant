import json
from datetime import datetime, timezone, timedelta


def build_task_creation_messages(
    task_description,
    projects,
    tags,
    default_due_date: str = "none",
    voice_correction: bool = False,
):
    """Build chat messages to extract a Tududi task from a natural language description.

    Returns a list of messages suitable for the OpenAI Chat Completions API.
    """
    project_list = [
        {"id": p.get("id"), "name": p.get("name")} for p in (projects or [])
    ]
    tag_list = [
        {"name": t.get("name")}
        for t in (tags or [])
        if isinstance(t, dict) and t.get("name")
    ]

    now = datetime.now(timezone.utc)
    current_timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    current_date = now.strftime("%Y-%m-%d")

    tomorrow = (
        (now + timedelta(days=1))
        .replace(hour=12, minute=0, second=0, microsecond=0)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    end_of_week = (
        (now + timedelta(days=7))
        .replace(hour=17, minute=0, second=0, microsecond=0)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    end_of_month = (
        (now + timedelta(days=30))
        .replace(hour=17, minute=0, second=0, microsecond=0)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    default_due_date_instructions = ""
    if default_due_date != "none":
        default_due_date_value = {
            "tomorrow": tomorrow,
            "end_of_week": end_of_week,
            "end_of_month": end_of_month,
        }.get(default_due_date, "")

        default_due_date_instructions = f"""
        IMPORTANT DEFAULT DUE DATE RULE:
        - ONLY apply the default due date ({default_due_date_value}) when BOTH conditions are met:
          1. The user does NOT mention any specific project name
          2. The user does NOT mention any specific due date or time
        - If the user mentions ANY project name from the available projects list → do NOT set any due date unless the user also explicitly mentions a date/time
        - If the user explicitly mentions a due date/time → always use that date instead of the default
        - For recurring tasks without an explicit due date AND without a project mentioned → set to {default_due_date_value}
        """

    voice_correction_instructions = ""
    if voice_correction:
        voice_correction_instructions = """
        SPEECH RECOGNITION CORRECTION:
        - Task came from a voice command - expect speech recognition errors
        - Correct misheard project names, tag names, dates, and common speech-to-text mistakes
        - Ensure the task name is logically consistent with the project and tags; if something doesn't make sense, find the most likely intended word/phrase from context
        """

    system_message = {
        "role": "system",
        "content": f"""
        You are an assistant that helps create tasks in Tududi.
        Given a task description, extract the task details and return a JSON payload for the Tududi API.

        Available projects: {json.dumps(project_list)}
        Available tags: {json.dumps(tag_list)}

        PROJECT SELECTION:
        - Always try to match the task to a project based on the description.
        - The user may explicitly name a project (e.g. "add to shopping", "for the work project", "in personal").
        - The user may also imply a project through context (e.g. "buy milk" likely belongs to a shopping project if one exists).
        - If the user explicitly names a project, that takes priority over contextual inference.
        - Use the project's id in the project_id field. If no project can be determined, use the first project's id.

        DEFAULT DUE DATE RULE:
        {default_due_date_instructions.strip() if default_due_date_instructions else "- No default due date configured"}

        {voice_correction_instructions.strip() if voice_correction_instructions else ""}

        CORE OUTPUT REQUIREMENTS:
        - Output ONLY valid JSON with these fields (only include optional fields when applicable):
            * name (string): Task name (REQUIRED, MUST NOT BE EMPTY)
            * note (string, optional): Only include if the user explicitly asks for additional notes/context.
            * project_id (number): Project ID (REQUIRED - always include, use first project's id if no match)
            * due_date (string, optional): Due date in YYYY-MM-DDTHH:MM:SSZ format
            * priority (string, optional): One of "low", "medium", "high" — only when explicitly mentioned
            * recurrence_type (string, optional): One of "daily", "weekly", "monthly" — only for recurring tasks
            * recurrence_interval (number, optional): How many days/weeks/months between recurrences (default 1)
            * tags (array, optional): Array of tag objects from available tags only, e.g. [{{"name": "grocery"}}]

        TASK FORMATTING:
        - Extract clear, concise task names.
        - Remove date/time info from name (use due_date field).
        - Remove tag references from name (handled via tags field).
        - Remove project name mentions from task name (handled via project_id).
        - Remove priority references from name (handled via priority field).
        - Remove unnecessary qualifiers (e.g. "task", "to do", "reminder", "add", "create").
        - Remove recurring task keywords from name (handled via recurrence_type).

        DATE HANDLING (Current: {current_timestamp}):
        - Calculate future dates based on current date: {current_date}
        - Use ISO format with 'Z' timezone: YYYY-MM-DDTHH:MM:SSZ
        - Default time: 12:00:00 (unless a specific time is mentioned)
        - NEVER set past dates - always use future dates for ambiguous references

        PRIORITY (only when explicitly mentioned):
        - "high": urgent, critical, emergency, ASAP, immediately, important
        - "medium": medium priority, when possible, moderately important, soon
        - "low": low priority, when you have time, not urgent, sometime, eventually

        RECURRING TASKS (only when explicitly mentioned):
        - recurrence_type "daily" + recurrence_interval 1: every day, daily
        - recurrence_type "weekly" + recurrence_interval 1: every week, weekly
        - recurrence_type "monthly" + recurrence_interval 1: every month, monthly
        - recurrence_type "weekly" + recurrence_interval 2: every two weeks, fortnightly
        - Keywords: daily, weekly, monthly, every day/week/month, recurring, repeat

        EXAMPLES:
        Input: "Reminder to pick up groceries tomorrow"
        (assuming project "Shopping" has id 3)
        Output: {{"name": "Pick up groceries", "project_id": 3, "due_date": "2024-06-09T12:00:00Z"}}

        Input: "Urgent: finish the report for work by Friday at 5pm"
        (assuming project "Work" has id 2)
        Output: {{"name": "Finish report", "project_id": 2, "due_date": "2024-06-07T17:00:00Z", "priority": "high"}}

        Input: "Take vitamins daily"
        Output: {{"name": "Take vitamins", "project_id": 1, "recurrence_type": "daily", "recurrence_interval": 1}}

        Input: "Buy milk tagged grocery for next week"
        (assuming tag "grocery" exists)
        Output: {{"name": "Buy milk", "project_id": 3, "tags": [{{"name": "grocery"}}], "due_date": "2024-06-16T12:00:00Z"}}

        Input: "Add buy milk to the shopping project"
        (user explicitly names project)
        Output: {{"name": "Buy milk", "project_id": 3}}

        Input: "Call dentist for work by Friday"
        (user names project AND due date)
        Output: {{"name": "Call dentist", "project_id": 2, "due_date": "2024-06-07T12:00:00Z"}}

        Input: "Schedule annual dentist appointment next March"
        Output: {{"name": "Schedule dentist appointment", "project_id": 1, "due_date": "2025-03-01T12:00:00Z"}}
        """,
    }

    user_message = {
        "role": "user",
        "content": f"Create task: {task_description}",
    }

    return [system_message, user_message]
