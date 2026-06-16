import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, CONF_TUDUDI_URL, CONF_TUDUDI_API_KEY
from .api.tududi_api import TududiAPI

_LOGGER = logging.getLogger(__name__)

CREATE_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("note"): cv.string,
        vol.Optional("project_id"): cv.positive_int,
        vol.Optional("due_date"): cv.string,
    }
)


def setup_services(hass: HomeAssistant):
    domain_config = hass.data.get(DOMAIN, {})
    tududi_url = domain_config.get(CONF_TUDUDI_URL)
    tududi_api_key = domain_config.get(CONF_TUDUDI_API_KEY)

    if not all([tududi_url, tududi_api_key]):
        _LOGGER.error("Missing configuration for Tududi voice assistant")
        return

    tududi_api = TududiAPI(tududi_url, tududi_api_key)

    async def create_task(call: ServiceCall):
        task_data = call.data.copy()
        result = await hass.async_add_executor_job(
            lambda: tududi_api.add_task(task_data)
        )
        if result:
            _LOGGER.info("Successfully created task via service: %s", task_data.get("name", "Unknown"))
        else:
            _LOGGER.error("Failed to create task via service: %s", task_data.get("name", "Unknown"))
            raise Exception("Failed to create task in Tududi")

    hass.services.async_register(DOMAIN, "create_task", create_task, schema=CREATE_TASK_SCHEMA)
