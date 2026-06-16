<div align="center">
<img src="logo.png" alt="Tududi logo" width="120" />

# Tududi Voice Assistant for Home Assistant

A Home Assistant custom component that lets you create tasks in [Tududi](https://github.com/chrisvel/tududi) by voice.
</div>

Say **"add a task buy milk"** or **"create a task call dentist for the work project tomorrow"** — the task lands in Tududi instantly.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Features

- **Natural voice commands** — trigger with "add a task", "create a task", etc.
- **Project selection by voice** — say "for the work project" or "add to shopping" and the task goes to the right project
- **LLM-powered extraction** — due dates, priority, tags, and recurrence parsed from natural language
- **Auto voice tag** — optionally tags all voice-created tasks so you can filter them in Tududi
- **Default due date** — configurable fallback (tomorrow, end of week, end of month)
- **Speech correction** — LLM fixes common speech-to-text errors
- **Detailed spoken response** — confirms project, tags, due date, and priority back to you
- **11 languages** — see [VOICE_COMMANDS.md](VOICE_COMMANDS.md)

---

## Requirements

- [Home Assistant](https://www.home-assistant.io/) with a voice assistant configured
- [HACS](https://hacs.xyz/)
- A running [Tududi](https://github.com/chrisvel/tududi) instance
- A Tududi API token (Profile → API Keys in Tududi)
- A Home Assistant AI Task entity (`ai_task.generate_data` pipeline — e.g. via extended_openai_conversation pointing at a local Ollama model)

---

## Installation (HACS)

1. HACS → Custom repositories → add `jamietre/tududi-voice-assistant` as type **Integration**
2. Find "Tududi Voice Assistant" in HACS and install it
3. Restart Home Assistant
4. Settings → Devices & Services → Add Integration → search **Tududi Voice Assistant**
5. Fill in the setup form

### Configuration fields

| Field | Description |
|---|---|
| Tududi base URL | e.g. `https://tududi.example.com` |
| Tududi API Token | Generate in Tududi under Profile → API Keys |
| AI Task entity | Your `ai_task` entity (e.g. from extended_openai_conversation) |
| Speech correction | Fixes common speech-to-text errors via LLM (recommended) |
| Auto voice tag | Automatically adds a "voice" tag to all voice-created tasks |
| Default due date | Fallback if no date is mentioned and no project is named |
| Detailed response | Spoken response includes project, tags, due date, priority |

---

## Voice commands

Trigger phrase: action word + "task" + description.

```
"Add a task buy milk"
"Create a task call dentist tomorrow"
"Add a task finish report for the work project by Friday"
"Add an urgent task submit invoice for work"
"Create a task take vitamins daily"
"Add a task buy flowers to the shopping project"
```

The LLM handles project matching — you can name a project explicitly ("for the work project", "add to shopping") or let it infer from context.

See [VOICE_COMMANDS.md](VOICE_COMMANDS.md) for examples in all 11 supported languages.

---

## How it works

1. You say a voice command matching the trigger pattern
2. Home Assistant's intent system captures the task description
3. The description is sent to your configured AI Task entity (LLM)
4. The LLM extracts: task name, project, due date, priority, tags, recurrence
5. The task is created in Tududi via the REST API
6. HA speaks back a confirmation

---

## Tududi API notes

This integration uses the Tududi REST API at `/api/v1`. Task fields:

- `name` — task name
- `note` — optional description
- `project_id` — matched by LLM from available projects
- `due_date` — ISO 8601
- `priority` — `"low"`, `"medium"`, or `"high"`
- `recurrence_type` — `"daily"`, `"weekly"`, or `"monthly"`
- `tags` — inline array, auto-created by Tududi if they don't exist

---

## License

MIT
