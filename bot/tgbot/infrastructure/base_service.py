import asyncio
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

    API_PREFIX = "/api/v1"

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
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create a reusable aiohttp ClientSession.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

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

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
        backoff_factor: float = 1.5,
        initial_delay: float = 1.0,
    ) -> tuple[int, dict | None]:
        """
        Make an HTTP request with exponential backoff retries.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            endpoint: API endpoint path.
            params: Query parameters.
            json_data: JSON payload.
            headers: Optional custom headers.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries. Defaults to 5 for GET and 1 for others.
            backoff_factor: Multiplier for retry delay.
            initial_delay: Starting delay in seconds.

        Returns:
            Tuple of (status_code, response_data).
            Returns (0, None) if connection fails.
        """
        if max_retries is None:
            max_retries = 5 if method == "GET" else 1

        url = f"{self.base_url}{self.API_PREFIX}{endpoint}"
        request_headers = self._get_headers(headers)
        request_timeout = ClientTimeout(total=timeout) if timeout else self.timeout

        session = await self._get_session()
        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                    timeout=request_timeout,
                ) as response:
                    status = response.status

                    if response.content_type == "application/json":
                        data = await response.json()
                    else:
                        data = {"detail": await response.text()}

                    self.logger.debug(f"{method} {url} - Status: {status}")

                    # Retry on 5xx server errors
                    if status >= 500:
                        if attempt == max_retries:
                            self.logger.error(
                                f"Request {method} {url} failed with status {status} after {max_retries} attempts."
                            )
                            return status, data
                        self.logger.warning(
                            f"Attempt {attempt} for {method} {url} returned status {status}. Retrying in {delay}s..."
                        )
                    else:
                        return status, data

            except asyncio.TimeoutError:
                if attempt == max_retries:
                    self.logger.error(
                        f"Timeout error during {method} request to {url} after {max_retries} attempts."
                    )
                    return 0, None
                self.logger.warning(
                    f"Attempt {attempt} for {method} {url} timed out. Retrying in {delay}s..."
                )
            except ClientError as e:
                if attempt == max_retries:
                    self.logger.error(
                        f"Connection error to {url} after {max_retries} attempts: {e}"
                    )
                    return 0, None
                self.logger.warning(
                    f"Attempt {attempt} for {method} {url} failed with connection error: {e}. Retrying in {delay}s..."
                )
            except Exception as e:
                self.logger.error(
                    f"Unexpected error during {method} request to {url}: {e}"
                )
                return 0, None

            await asyncio.sleep(delay)
            delay *= backoff_factor

        return 0, None

    async def _get(
        self,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> tuple[int, dict | None]:
        """
        Make a GET request to the backend API with retries.
        """
        return await self._request(
            "GET",
            endpoint,
            params=params,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def _post(
        self,
        endpoint: str,
        json_data: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> tuple[int, dict | None]:
        """
        Make a POST request to the backend API with retries.
        """
        return await self._request(
            "POST",
            endpoint,
            json_data=json_data,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def _put(
        self,
        endpoint: str,
        json_data: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> tuple[int, dict | None]:
        """
        Make a PUT request to the backend API with retries.
        """
        return await self._request(
            "PUT",
            endpoint,
            json_data=json_data,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def _patch(
        self,
        endpoint: str,
        json_data: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> tuple[int, dict | None]:
        """
        Make a PATCH request to the backend API with retries.
        """
        return await self._request(
            "PATCH",
            endpoint,
            json_data=json_data,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def _delete(
        self,
        endpoint: str,
        headers: dict | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> tuple[int, dict | None]:
        """
        Make a DELETE request to the backend API with retries.
        """
        return await self._request(
            "DELETE",
            endpoint,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
        )

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
        elif status == 401:
            error_msg = data.get("detail", "Unauthorized") if data else "Unauthorized"
            self.logger.warning(f"Unauthorized while {context}: {error_msg}")
            return f"❌ Unauthorized: {error_msg}"
        elif status == 403:
            error_msg = data.get("detail", "Forbidden") if data else "Forbidden"
            self.logger.warning(f"Forbidden while {context}: {error_msg}")
            return f"❌ Forbidden: {error_msg}"
        elif status == 500:
            self.logger.error(f"Server error while {context}")
            return "❌ Server error. Please try again later."
        else:
            self.logger.error(f"Unexpected status {status} while {context}")
            return "❌ My brain is offline. Please try again later."
