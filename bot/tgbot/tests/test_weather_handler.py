import pytest
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio

from aiogram.filters import CommandObject

from tgbot.handlers.weather import weather_command


async def test_weather_command_requires_city_argument() -> None:
    message = AsyncMock()
    command = CommandObject(prefix="/", command="weather", args=None)

    await weather_command(message, command)

    message.reply.assert_awaited_once_with(
        "❓ Please provide a city name.\nExample: /weather London"
    )


async def test_weather_command_rejects_more_than_one_city_token() -> None:
    message = AsyncMock()
    command = CommandObject(prefix="/", command="weather", args="New York")

    await weather_command(message, command)

    message.reply.assert_awaited_once_with(
        "❓ Please provide a city name.\nExample: /weather London"
    )


async def test_weather_command_fetches_weather_for_single_city(monkeypatch) -> None:
    message = AsyncMock()
    command = CommandObject(prefix="/", command="weather", args="London")
    weather_service_mock = AsyncMock(return_value="Sunny and 20°C")

    monkeypatch.setattr(
        "tgbot.handlers.weather.weather_service.get_current_weather", weather_service_mock
    )

    await weather_command(message, command)

    weather_service_mock.assert_awaited_once_with("London")
    message.answer.assert_awaited_once_with("Sunny and 20°C")
