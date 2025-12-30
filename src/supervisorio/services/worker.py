import asyncio
from supervisorio.core.buffer import Buffer
from supervisorio.infrastructure.database.repositories import PesagemRepository
from supervisorio.core.logger import get_logger
from supervisorio.infrastructure.database.repositories import RepositoryBase
from supervisorio.core.monitor import monitor

logger = get_logger(__name__)


async def worker(buffer: Buffer, repository: type[RepositoryBase], worker_name: str = 'Genérico'):
    """
    Monitora ciclicamente o buffer, e quando tem dados, envia ao repository pelo metodo insert_many

    :param buffer: Fila de dados a serem inseridos
    :type buffer: Buffer
    :param repository: Repositório que gerencia o banco de dados
    :type repository:  type[RepositoryBase]
    :param worker_name: Nome que será exibido em logs
    :type worker_name: str
    """

    logger.info(f"Worker {worker_name} iniciado")

    while True:
        try:
            monitor.update_heartbeat(
                f"worker_{worker_name.lower()}", buffer_size=buffer.qsize())
            batch = await buffer.get_batch(batch_size=500)
            if buffer.qsize() > 8_000:
                logger.critical(
                    f'Worker {worker_name}: buffer excedeu 80% da capacidade')

            if not batch:
                continue

            await asyncio.wait_for(repository.insert_many(batch), timeout=10)

            monitor.update_heartbeat(
                f"worker_{worker_name.lower()}", increment_processed=len(batch))
            logger.debug(
                f"Lote de {len(batch)} itens armazendos pelo worker {worker_name}.")
        except asyncio.CancelledError:
            logger.info(f'Worker {worker_name} sendo cancelado')

            # Flush final Garante que dados remanescentes não sejam perdidos
            while buffer.qsize() > 0:
                final_batch = await buffer.get_batch(batch_size=500)
                if final_batch:
                    try:
                        await asyncio.wait_for(repository.insert_many(final_batch), timeout=5)
                        logger.info(
                            f"Flush: {len(final_batch)} itens salvos antes do desligamento.")
                    except Exception as e:
                        logger.error(
                            f"Erro no flush final do worker {worker_name}: {e}")
            break
        except Exception as e:
            logger.error(f"Erro crítico no worker {worker_name}: {e}")
            monitor.report_error(f"worker_{worker_name.lower()}")
            await asyncio.sleep(1)
