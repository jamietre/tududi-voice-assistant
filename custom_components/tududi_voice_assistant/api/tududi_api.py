import logging
import requests

_LOGGER = logging.getLogger(__name__)


class TududiAPI:
    def __init__(self, url, api_key):
        self.url = url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def _log_error(self, err, context):
        _LOGGER.error("%s: %s", context, err)
        resp = getattr(err, "response", None)
        if resp is not None and hasattr(resp, "text"):
            _LOGGER.error("Response content: %s", resp.text)

    def test_connection(self):
        try:
            response = requests.get(
                f"{self.url}/projects", headers=self.headers, timeout=30
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as err:
            self._log_error(err, "Connection test failed")
            return False

    def get_projects(self):
        try:
            response = requests.get(
                f"{self.url}/projects", headers=self.headers, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []
        except requests.exceptions.RequestException as err:
            self._log_error(err, "Failed to get projects")
            return []

    def get_tags(self):
        try:
            response = requests.get(
                f"{self.url}/tags", headers=self.headers, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []
        except requests.exceptions.RequestException as err:
            self._log_error(err, "Failed to get tags")
            return []

    def add_task(self, task_data):
        """Create a new task. Requires 'name' field. Tags are passed inline and auto-created."""
        if not task_data.get("name"):
            _LOGGER.error("Cannot create task: missing 'name'")
            return None
        try:
            response = requests.post(
                f"{self.url}/task",
                headers=self.headers,
                json=task_data,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            self._log_error(err, "Failed to create task")
            return None
