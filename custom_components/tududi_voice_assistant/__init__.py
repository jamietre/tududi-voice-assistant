import logging
import os
from homeassistant.helpers import config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    CONF_TUDUDI_API_KEY,
    CONF_AI_TASK_ENTITY,
    CONF_TUDUDI_URL,
    CONF_DUE_DATE,
    CONF_VOICE_CORRECTION,
    CONF_AUTO_VOICE_TAG,
    CONF_DETAILED_RESPONSE,
)
from .services import setup_services
from .intents import register_intents

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def copy_custom_sentences(hass: HomeAssistant) -> None:
    source_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "custom_sentences"
    )
    if not os.path.exists(source_dir):
        return
    target_root = os.path.join(hass.config.config_dir, "custom_sentences")
    os.makedirs(target_root, exist_ok=True)
    for lang in os.listdir(source_dir):
        src_lang = os.path.join(source_dir, lang)
        if not os.path.isdir(src_lang):
            continue
        dst_lang = os.path.join(target_root, lang)
        os.makedirs(dst_lang, exist_ok=True)
        for fname in os.listdir(src_lang):
            if not fname.endswith(".yaml"):
                continue
            src_file = os.path.join(src_lang, fname)
            dst_file = os.path.join(dst_lang, fname)
            if not os.path.exists(dst_file) or os.path.getmtime(
                src_file
            ) > os.path.getmtime(dst_file):
                with open(src_file, "r", encoding="utf-8") as src, open(
                    dst_file, "w", encoding="utf-8"
                ) as dst:
                    dst.write(src.read())


async def async_setup(hass: HomeAssistant, config):
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN] = {
        CONF_TUDUDI_URL: entry.data[CONF_TUDUDI_URL],
        CONF_TUDUDI_API_KEY: entry.data[CONF_TUDUDI_API_KEY],
        CONF_AI_TASK_ENTITY: entry.data[CONF_AI_TASK_ENTITY],
        CONF_DUE_DATE: entry.data[CONF_DUE_DATE],
        CONF_VOICE_CORRECTION: entry.data[CONF_VOICE_CORRECTION],
        CONF_AUTO_VOICE_TAG: entry.data.get(CONF_AUTO_VOICE_TAG, True),
        CONF_DETAILED_RESPONSE: entry.data.get(CONF_DETAILED_RESPONSE, True),
    }

    register_intents(hass)
    setup_services(hass)

    try:
        await hass.async_add_executor_job(copy_custom_sentences, hass)
    except Exception as sentence_err:  # noqa: BLE001
        _LOGGER.error("Failed to copy custom sentences: %s", sentence_err)

    await hass.services.async_call("conversation", "reload", {})
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return True
