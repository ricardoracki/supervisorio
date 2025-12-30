import asyncio
from typing import Generic, TypeVar, List

T = TypeVar('T')


class Buffer(Generic[T]):
    def __init__(self, maxsize: int = 10_000) -> None:
        # Usamos o Queue nativo do asyncio para evitar bloqueio do event loop
        self._queue: asyncio.Queue[T] = asyncio.Queue(maxsize=maxsize)

    async def put(self, item: T) -> None:
        """Adiciona um item ao buffer de forma assíncrona."""
        await self._queue.put(item)

    async def get_batch(self, batch_size: int = 500) -> List[T]:
        """
        Extrai um lote de itens de forma extremamente rápida.
        Se a fila estiver vazia, aguarda o primeiro item chegar.
        """
        result = []

        # Aguarda o primeiro item para não retornar uma lista vazia (bloqueio eficiente)
        first_item = await self._queue.get()
        result.append(first_item)

        # Tenta pegar o restante do batch de forma não-bloqueante (imediata)
        while len(result) < batch_size:
            try:
                # get_nowait() é muito mais rápido que get() dentro de um loop
                result.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        return result

    def qsize(self) -> int:
        return self._queue.qsize()


if __name__ == '__main__':
    async def run():
        b = Buffer()
        await b.put(1)
        await b.put(2)
        await b.put(3)
        await b.put(4)
        await b.put(5)
        print(await b.get_batch())

    asyncio.run(run())
