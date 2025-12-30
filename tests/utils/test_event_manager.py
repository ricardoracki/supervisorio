from supervisorio.utils.event_manager import EventManager
from unittest.mock import AsyncMock
import pytest


def test_event_manager_has():
    manager = EventManager()
    manager.on("event", lambda: None)
    assert manager.has("event"), 'Event should be registered'


@pytest.mark.asyncio
async def test_event_manager_dispatch_calls_registered_handler():
    manager = EventManager()
    handler = AsyncMock()

    manager.on("event", handler)

    await manager.dispatch("event")
    handler.assert_called_once()
