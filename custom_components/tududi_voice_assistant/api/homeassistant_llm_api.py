from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant

from ..helpers.prompt_builder import build_task_creation_messages

_LOGGER = logging.getLogger(__name__)


class HomeAssistantLLMAPI:
    """Interface to Home Assistant's AI task pipeline."""

    _DEFAULT_TASK_NAME = "Generate Tududi task"

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        self._hass = hass
        self._entity_id = entity_id.strip()

    async def create_task_from_description(
        self,
        task_description: str,
        projects: Optional[List[Dict[str, Any]]],
        tags: Optional[List[Dict[str, Any]]],
        default_due_date: str = "none",
        voice_correction: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Use HA's LLM pipeline to transform a natural language description into task data."""
        if not self._entity_id:
            _LOGGER.error("No AI Task entity configured for Tududi voice assistant")
            return None

        messages = build_task_creation_messages(
            task_description,
            projects,
            tags,
            default_due_date,
            voice_correction,
        )
        prompt = self._format_messages_to_prompt(messages)

        request_payload: Dict[str, Any] = {
            "entity_id": self._entity_id,
            "task_name": self._derive_task_name(task_description),
            "instructions": prompt,
        }

        try:
            response = await self._hass.services.async_call(
                "ai_task",
                "generate_data",
                request_payload,
                blocking=True,
                return_response=True,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("LLM service call failed: %s", err)
            return None

        if not response:
            _LOGGER.error("Empty response from Home Assistant LLM service")
            return None

        task_data = self._parse_llm_response(response)
        if task_data is None:
            _LOGGER.error("Failed to extract structured task data from LLM response")
            return None

        _LOGGER.info(
            "Successfully processed task via Home Assistant AI Task: '%s'",
            task_data.get("name", "Unknown"),
        )
        return {"task_data": task_data}

    def _parse_llm_response(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not response:
            return None

        response_block = response.get("response")
        data_block = response.get("data")

        if isinstance(data_block, dict):
            parsed = data_block.get("parsed")
            if isinstance(parsed, dict):
                return self._validate_task_data(parsed)

        candidates: List[str] = []

        if isinstance(response_block, dict):
            for field in ("markdown", "plain", "spoken"):
                value = response_block.get(field)
                if isinstance(value, str):
                    candidates.append(value)
        elif isinstance(response_block, str):
            candidates.append(response_block)

        if isinstance(data_block, dict):
            content = data_block.get("content")
            if isinstance(content, str):
                candidates.append(content)
        elif isinstance(data_block, str):
            candidates.append(data_block)

        for candidate in candidates:
            task_data = self._extract_json(candidate)
            if task_data is not None:
                return self._validate_task_data(task_data)

        return None

    def _validate_task_data(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(task_data, dict):
            return None
        if not task_data.get("name"):
            _LOGGER.error("LLM response missing required 'name' field")
            return None
        return task_data

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        if start_idx < 0 or end_idx <= start_idx:
            return None

        json_str = text[start_idx:end_idx]
        try:
            decoded = json.loads(json_str)
        except json.JSONDecodeError:
            _LOGGER.debug("Failed to decode JSON candidate from LLM output")
            return None

        if not isinstance(decoded, dict):
            return None
        return decoded

    def _derive_task_name(self, task_description: str) -> str:
        if not task_description:
            return self._DEFAULT_TASK_NAME
        collapsed = " ".join(task_description.split())
        return collapsed[:120] if collapsed else self._DEFAULT_TASK_NAME

    def _format_messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
        segments: List[str] = []
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            if not isinstance(content, str) or not content:
                continue
            prefix = {"system": "System", "assistant": "Assistant"}.get(role, "User")
            segments.append(f"{prefix}: {content}")
        return "\n\n".join(segments)
