from __future__ import annotations

import logging
from homeassistant.helpers import intent

from .task_handler import process_task
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TududiAddTaskIntentHandler(intent.IntentHandler):
    intent_type = "TududiAddTask"

    def __init__(self, hass):
        self.hass = hass

    async def async_handle(self, call: intent.Intent):  # type: ignore[override]
        slots = call.slots
        task_description = slots.get("task_description", {}).get("value", "")
        response = intent.IntentResponse(language=call.language)
        if not task_description.strip():
            response.async_set_speech(
                "I couldn't understand what task you wanted to add. Please try again."
            )
            return response
        success, message, _title = await process_task(self.hass, task_description)
        response.async_set_speech(message)
        return response


def register_intents(hass) -> None:
    try:
        intent.async_register(hass, TududiAddTaskIntentHandler(hass))
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("Failed to register intents for %s: %s", DOMAIN, err)
