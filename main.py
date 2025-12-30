import asyncio
from supervisorio.core.buffer import Buffer
from supervisorio.infrastructure.database.repositories import PesagemRepository, EventRepository
from supervisorio.infrastructure.database.connection import get_pool, close_pool
from supervisorio.services.worker import worker
from supervisorio.infrastructure.CW import CheckWeigher
from supervisorio.core.logger import get_logger
from supervisorio.core.config import settings
from supervisorio.core.types.ModbusReadPayload import ModbusReadPayload


logger = get_logger(__name__)


async def shutdown(loop):
    """Fecha as tarefas e conexões de forma limpa."""

    logger.info("Iniciando processo de shutdown...")

    # 1. Captura todas as tarefas, exceto a atual (que é o próprio shutdown)
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    if tasks:
        logger.info(f"Cancelando {len(tasks)} tarefas pendentes...")
        for task in tasks:
            task.cancel()

        # 2. Aguarda o cancelamento de todas as tarefas
        # return_exceptions=True evita que o shutdown quebre se uma task demorar a cancelar
        await asyncio.gather(*tasks, return_exceptions=True)

    # 3. Fecha conexões críticas
    logger.info("Fechando pool de conexões com o banco...")
    await close_pool()

    # NOTA: Removido o loop.stop() para não conflitar com o asyncio.run()
    logger.info("Shutdown finalizado com sucesso.")


async def main():
    logger = get_logger("collector", 'collector.log')
    logger.info("Iniciando aplicação de pesagem...")

    # 1. Inicializa o Buffer (Fila em memória)
    # Recomendado maxsize para evitar estouro de memória se o banco cair
    buffer_pesagens = Buffer[ModbusReadPayload](maxsize=10_000)
    buffer_eventos = Buffer(maxsize=10_000)

    # 2. Inicializa o Pool de Conexões e o Banco de Dados
    await get_pool()
    await PesagemRepository.initialize()
    await EventRepository.initialize()

    # 3. Cria as Tarefas (Tasks)
    # Task do Worker: Consome do Buffer -> Banco
    worker_pesagem_task = asyncio.create_task(
        worker(buffer=buffer_pesagens,
               repository=PesagemRepository,
               worker_name='pesagens'
               ),
        name="Worker-pesagem-task"
    )
    worker_event_task = asyncio.create_task(
        worker(buffer=buffer_eventos,
               repository=EventRepository,
               worker_name='Eventos'
               ),
        name='Worker-eventos-task'
    )

    # Instanciação e atribuição dos eventos
    cws = [cw
           .on(CheckWeigher.eventTypes.WEIGHT_READ, buffer_pesagens.put)
           .on(CheckWeigher.eventTypes.EVENT_CHANGED,  buffer_eventos.put)
           .on(CheckWeigher.eventTypes.ERROR, logger.error)
           for cw in settings.cws if cw.enabled]

    # Cria tarefas async que monitoram os equipamentos
    tasks = [asyncio.create_task(
        cw.listener(), name=f"{cw.name} listener") for cw in cws]

    # 4. Monitoramento e Graceful Shutdown
    loop = asyncio.get_running_loop()

    try:
        # Mantém o main vivo enquanto as tasks rodam
        await asyncio.gather(worker_pesagem_task, worker_event_task, * tasks)
    except asyncio.CancelledError:
        logger.info("Aplicação encerrada.")

    except Exception as e:
        logger.exception(e)

    finally:
        await shutdown(loop)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
