import logging
from abc import ABC

import aiohttp
from aiohttp import ClientError, ClientTimeout

from tgbot.config import config


class BaseAPIService(ABC):
    """
    Abstract base class for all API services.

    Provides common HTTP methods and error handling.
    Services should inherit from this class and implement their business logic.
    """

    def __init__(self, base_url: str | None = None, timeout: int = 10):
        """
        Initialize the API service.

        Args:
            base_url: Base URL of the backend API. If not provided, uses config.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url or config.backend_base_url
        self.timeout = ClientTimeout(total=timeout)
        self.api_key = config.backend_api_key.get_secret_value()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_headers(self, custom_headers: dict | None = None) -> dict:
        """
        Build common headers for API requests.

        Args:
            custom_headers: Optional custom headers to merge with defaults.

        Returns:
            Dictionary of headers including API key authentication.
        """
        headers = {"X-API-Key": self.api_key}
        if custom_headers:
            headers.update(custom_headers)
        return headers

    async def _get(
        self,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> tuple[int, dict | None]:
        """
        Make a GET request to the backend API.

        Args:
            endpoint: API endpoint path (e.g., "/api/v1/weather/current").
            params: Query parameters.
            headers: Optional custom headers to include in the request.

        Returns:
            Tuple of (status_code, response_data).
            Returns (0, None) if connection fails.
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_headers(headers)

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url, params=params, headers=request_headers
                ) as response:
                    status = response.status

                    if response.content_type == "application/json":
                        data = await response.json()
                    else:
                        data = {"detail": await response.text()}

                    self.logger.debug(f"GET {url} - Status: {status}")
                    return status, data

        except ClientError as e:
            self.logger.error(f"Connection error to {url}: {e}")
            return 0, None
        except Exception as e:
            self.logger.error(f"Unexpected error during GET request to {url}: {e}")
            return 0, None

    async def _post(
        self,
        endpoint: str,
        json_data: dict | None = None,
        headers: dict | None = None,
    ) -> tuple[int, dict | None]:
        """
        Make a POST request to the backend API.

        Args:
            endpoint: API endpoint path.
            json_data: JSON payload.
            headers: Optional custom headers to include in the request.

        Returns:
            Tuple of (status_code, response_data).
            Returns (0, None) if connection fails.
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_headers(headers)

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    url, json=json_data, headers=request_headers
                ) as response:
                    status = response.status

                    if response.content_type == "application/json":
                        data = await response.json()
                    else:
                        data = {"detail": await response.text()}

                    self.logger.debug(f"POST {url} - Status: {status}")
                    return status, data

        except ClientError as e:
            self.logger.error(f"Connection error to {url}: {e}")
            return 0, None
        except Exception as e:
            self.logger.error(f"Unexpected error during POST request to {url}: {e}")
            return 0, None

    async def _put(
        self,
        endpoint: str,
        json_data: dict | None = None,
        headers: dict | None = None,
    ) -> tuple[int, dict | None]:
        """
        Make a PUT request to the backend API.

        Args:
            endpoint: API endpoint path.
            json_data: JSON payload.
            headers: Optional custom headers to include in the request.

        Returns:
            Tuple of (status_code, response_data).
            Returns (0, None) if connection fails.
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_headers(headers)

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.put(
                    url, json=json_data, headers=request_headers
                ) as response:
                    status = response.status

                    if response.content_type == "application/json":
                        data = await response.json()
                    else:
                        data = {"detail": await response.text()}

                    self.logger.debug(f"PUT {url} - Status: {status}")
                    return status, data

        except ClientError as e:
            self.logger.error(f"Connection error to {url}: {e}")
            return 0, None
        except Exception as e:
            self.logger.error(f"Unexpected error during PUT request to {url}: {e}")
            return 0, None

    async def _patch(
        self,
        endpoint: str,
        json_data: dict | None = None,
        headers: dict | None = None,
    ) -> tuple[int, dict | None]:
        """
        Make a PATCH request to the backend API.

        Args:
            endpoint: API endpoint path.
            json_data: JSON payload.
            headers: Optional custom headers to include in the request.

        Returns:
            Tuple of (status_code, response_data).
            Returns (0, None) if connection fails.
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_headers(headers)

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.patch(
                    url, json=json_data, headers=request_headers
                ) as response:
                    status = response.status

                    if response.content_type == "application/json":
                        data = await response.json()
                    else:
                        data = {"detail": await response.text()}

                    self.logger.debug(f"PATCH {url} - Status: {status}")
                    return status, data

        except ClientError as e:
            self.logger.error(f"Connection error to {url}: {e}")
            return 0, None
        except Exception as e:
            self.logger.error(f"Unexpected error during PATCH request to {url}: {e}")
            return 0, None

    async def _delete(
        self, endpoint: str, headers: dict | None = None
    ) -> tuple[int, dict | None]:
        """
        Make a DELETE request to the backend API.

        Args:
            endpoint: API endpoint path.
            headers: Optional custom headers to include in the request.

        Returns:
            Tuple of (status_code, response_data).
            Returns (0, None) if connection fails.
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_headers(headers)

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.delete(url, headers=request_headers) as response:
                    status = response.status

                    if response.content_type == "application/json":
                        data = await response.json()
                    else:
                        data = {"detail": await response.text()}

                    self.logger.debug(f"DELETE {url} - Status: {status}")
                    return status, data

        except ClientError as e:
            self.logger.error(f"Connection error to {url}: {e}")
            return 0, None
        except Exception as e:
            self.logger.error(f"Unexpected error during DELETE request to {url}: {e}")
            return 0, None

    def _handle_error_response(
        self, status: int, data: dict | None, context: str
    ) -> str:
        """
        Handle common error responses with user-friendly messages.

        Args:
            status: HTTP status code.
            data: Response data.
            context: Context for the error (e.g., "fetching weather").

        Returns:
            User-friendly error message.
        """
        if status == 0:
            return "❌ My brain is offline. Please try again later."
        elif status == 404:
            return "❌ Resource not found. Please check your input."
        elif status == 400:
            error_msg = (
                data.get("detail", "Invalid request") if data else "Invalid request"
            )
            self.logger.warning(f"Bad request while {context}: {error_msg}")
            return "❌ Invalid request. Please try again."
        elif status == 500:
            self.logger.error(f"Server error while {context}")
            return "❌ Server error. Please try again later."
        else:
            self.logger.error(f"Unexpected status {status} while {context}")
            return "❌ My brain is offline. Please try again later."
