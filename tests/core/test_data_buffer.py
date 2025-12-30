import pytest

from supervisorio.core.buffer import Buffer


@pytest.mark.asyncio
async def test_get_batch_returns_items_in_fifo_order():
    buffer = Buffer()

    for i in range(5):
        await buffer.put(i)

    assert await buffer.get_batch(3) == [0, 1, 2], 'Should return the first 3 items'


@pytest.mark.asyncio
async def test_get_batch_removes_items_from_buffer():
    buffer = Buffer()

    for i in range(3):
        await buffer.put(i)

    await buffer.get_batch(2)

    remaining = await buffer.get_batch(10)

    assert remaining == [2]


@pytest.mark.asyncio
async def test_get_batch_when_batch_size_exceeds_buffer_size():
    buffer = Buffer()

    await buffer.put(1)
    await buffer.put(2)

    result = await buffer.get_batch(10)

    assert result == [1, 2]
