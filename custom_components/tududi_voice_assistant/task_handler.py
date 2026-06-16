from __future__ import annotations

import asyncio
import logging

from .const import (
    DOMAIN,
    CONF_TUDUDI_URL,
    CONF_TUDUDI_API_KEY,
    CONF_AI_TASK_ENTITY,
    CONF_DUE_DATE,
    CONF_VOICE_CORRECTION,
    CONF_AUTO_VOICE_TAG,
    CONF_DETAILED_RESPONSE,
)
from .api.tududi_api import TududiAPI
from .api.homeassistant_llm_api import HomeAssistantLLMAPI
from .helpers.detailed_response_formatter import build_detailed_response
from .helpers.localization import get_language, L

_LOGGER = logging.getLogger(__name__)


async def process_task(hass, task_description: str):
    """Create a Tududi task from natural language description.

    Returns (success, message, task_name)
    """
    domain_config = hass.data.get(DOMAIN, {})
    tududi_url = domain_config.get(CONF_TUDUDI_URL)
    tududi_api_key = domain_config.get(CONF_TUDUDI_API_KEY)
    ai_task_entity = domain_config.get(CONF_AI_TASK_ENTITY, "")
    default_due_date = domain_config.get(CONF_DUE_DATE, "none")
    voice_correction = domain_config.get(CONF_VOICE_CORRECTION, True)
    auto_voice_tag = domain_config.get(CONF_AUTO_VOICE_TAG, True)
    detailed_response = domain_config.get(CONF_DETAILED_RESPONSE, True)
    lang = get_language(hass)

    if not all([tududi_url, tududi_api_key, ai_task_entity]):
        _LOGGER.error("Missing configuration for Tududi voice assistant")
        return False, L("config_error", lang), ""

    api = TududiAPI(tududi_url, tududi_api_key)
    projects, tags = await asyncio.gather(
        hass.async_add_executor_job(api.get_projects),
        hass.async_add_executor_job(api.get_tags),
    )

    llm_client = HomeAssistantLLMAPI(hass, ai_task_entity)
    llm_response = await llm_client.create_task_from_description(
        task_description,
        projects,
        tags,
        default_due_date,
        voice_correction,
    )

    if not llm_response:
        _LOGGER.error("Failed to process task with Home Assistant LLM")
        return False, L("llm_conn_error", lang), ""

    try:
        task_data = llm_response.get("task_data", {})
        if task_data is None:
            _LOGGER.error("LLM response task_data was None")
            return False, L("llm_process_error", lang), ""
        if not isinstance(task_data, dict):
            _LOGGER.error("LLM response task_data not a dict: %r", type(task_data))
            return False, L("llm_process_error", lang), ""
        if not task_data.get("name"):
            _LOGGER.error("Missing required 'name' field in task data")
            return False, L("llm_missing_title", lang), ""

        # Collect tag names the LLM selected (already validated against available tags)
        llm_tags = task_data.pop("tags", []) or []
        if not isinstance(llm_tags, list):
            llm_tags = []

        # Resolve to name strings for the payload
        tag_names = []
        available_tag_names = {
            str(t.get("name", "")).casefold()
            for t in (tags or [])
            if isinstance(t, dict)
        }
        for t in llm_tags:
            name = t.get("name") if isinstance(t, dict) else str(t)
            if name and str(name).casefold() in available_tag_names:
                tag_names.append(name)

        if auto_voice_tag:
            voice_name = "voice"
            if not any(n.casefold() == voice_name for n in tag_names):
                tag_names.append(voice_name)

        # Build final task payload with tags inline (Tududi auto-creates unknown tags)
        if tag_names:
            task_data["tags"] = [{"name": n} for n in tag_names]

        result = await hass.async_add_executor_job(lambda: api.add_task(task_data))

        if result:
            task_name = task_data.get("name", "")
            _LOGGER.info("Created Tududi task '%s'", task_name)

            if not detailed_response:
                return True, L("success_added", lang, title=task_name), task_name

            safe_task_name = task_name or ""
            try:
                detailed_message = build_detailed_response(
                    task_name=safe_task_name,
                    task_data=task_data,
                    projects=projects,
                    tag_names=tag_names,
                    lang=lang,
                )
            except Exception as format_err:  # noqa: BLE001
                _LOGGER.error("Error building detailed response: %s", format_err)
                return True, L("success_added", lang, title=safe_task_name), safe_task_name

            return True, detailed_message, safe_task_name

        _LOGGER.error("Failed to create task in Tududi")
        return False, L("tududi_add_error", lang), ""

    except Exception as err:  # noqa: BLE001
        _LOGGER.error("Unexpected error creating task: %s", err)
        return False, L("unexpected_error", lang), ""
