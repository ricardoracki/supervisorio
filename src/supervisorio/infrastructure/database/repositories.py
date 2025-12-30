from typing import TypeVar, Generic, List, Optional, Dict, Any
from datetime import date
from abc import ABC, abstractmethod
from asyncpg.exceptions import UniqueViolationError

from supervisorio.infrastructure.database.connection import get_pool
from supervisorio.core.logger import get_logger
from supervisorio.core.types.event_types import EventTypes
from supervisorio.core.types.ModbusReadPayload import ModbusReadPayload
from supervisorio.core.types.MachineEventPayload import MachineStopEventPayload

logger = get_logger(__name__)
T = TypeVar('T')


class RepositoryBase(ABC, Generic[T]):
    _pool: Optional[Any] = None

    @classmethod
    async def initialize_pool(cls):
        """Método único para garantir que o pool existe para todos."""
        if cls._pool is None:
            cls._pool = await get_pool()
            logger.debug("Pool de conexões global inicializado.")

    @classmethod
    @abstractmethod
    async def initialize(cls):
        """Cada repositório cria sua tabela."""
        pass

    @classmethod
    async def execute_query(cls, query: str, *args):
        """Helper para executar queries sem repetir try/except."""
        await cls.initialize_pool()

        try:
            async with cls._pool.acquire() as conn:  # type:ignore
                return await conn.execute(query, *args)
        except UniqueViolationError:
            logger.debug(
                "Objeto já existente no banco (concorrência ignorada).")
        except Exception as e:
            logger.error(f"Erro na execução SQL: {e}")
            raise


class PesagemRepository(RepositoryBase[ModbusReadPayload]):
    @classmethod
    async def initialize(cls):
        query = """
        CREATE TABLE IF NOT EXISTS pesagens (
            id SERIAL PRIMARY KEY,
            maquina_id TEXT NOT NULL,
            peso INTEGER NOT NULL,
            classificacao INTEGER NOT NULL DEFAULT 0,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_pesagens_timestamp ON pesagens (timestamp DESC);
        """
        await cls.execute_query(query)

    @classmethod
    async def insert_many(cls, batch: List[ModbusReadPayload]):
        if not batch:
            return
        await cls.initialize_pool()

        query = "INSERT INTO pesagens (maquina_id, peso, classificacao, timestamp) VALUES ($1, $2, $3, $4)"
        values = [(i.cw_id, i.weight, i.classification, i.timestamp)
                  for i in batch]

        async with cls._pool.acquire() as conn:  # type:ignore
            await conn.executemany(query, values)
            logger.info(f"Lote de ${len(batch)} pesagens armazenado.")

    @classmethod
    async def find(cls,
                   maquina_id: None | str = None,
                   classificacao: None | int = None,
                   timestamp: None | date = None,
                   periodo: None | tuple[date, date] = None,
                   limit: int = 20) -> List[Dict]:
        """
        BUsca dados com base em filtros estabelecidos
        """
        await cls.initialize_pool()
        query = "SELECT maquina_id, peso, classificacao, timestamp FROM pesagens WHERE 1=1"
        args = []

        def appendFilter(key: str, value: Any):
            nonlocal query
            nonlocal args
            args.append(value)
            query += f' AND {key} = ${len(args)}'

        if periodo is not None:
            args.append(periodo[0])
            args.append(periodo[1])
            query += f' timestamp::date BETWEEN ${len(args) - 1} AND ${len(args)}'
        elif timestamp is not None:
            appendFilter('timestamp::date', timestamp)

        if maquina_id is not None:
            appendFilter('maquina_id', maquina_id)

        if classificacao is not None:
            appendFilter('classificacao', classificacao)

        query += f" ORDER BY timestamp DESC LIMIT {limit}"

        async with cls._pool.acquire() as conn:  # type:ignore
            rows = await conn.fetch(query, *args)
            return [dict(r) for r in rows]


class EventRepository(RepositoryBase[MachineStopEventPayload]):
    @classmethod
    async def initialize(cls):
        query = """
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            maquina_id TEXT NOT NULL,
            evento INTEGER NOT NULL,
            reason INTEGER NOT NULL,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            duration INTERVAL, 
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        await cls.execute_query(query)

    @classmethod
    async def insert_many(cls, batch: List[MachineStopEventPayload]):
        if not batch:
            return
        await cls.initialize_pool()

        query = "INSERT INTO events (maquina_id, evento, reason, started_at, ended_at, duration) VALUES ($1, $2, $3, $4, $5, $6)"

        values = []
        for item in batch:
            # Lógica de conversão tratada antes do envio
            evt_type = 1 if item.event_type == EventTypes.RUN else 0
            duration = (
                item.ended_at - item.started_at) if (item.ended_at and item.started_at) else None
            values.append((item.cw_id, evt_type, item.reason,
                          item.started_at, item.ended_at, duration))

        async with cls._pool.acquire() as conn:  # type:ignore
            await conn.executemany(query, values)
            logger.info(f"Lote de ${len(batch)} eventos armazenado.")

    @classmethod
    async def find(cls,
                   maquina_id: None | str = None,
                   evento: None | int = None, reason: None | int = None,
                   periodo: None | tuple[date, date] = None,
                   limit: int = 20) -> List[Dict]:
        await cls.initialize_pool()
        # Query com o Cast de duration já embutido
        query = """
            SELECT id, maquina_id, evento, reason, started_at, ended_at, 
                   duration::time as duration, created_at 
            FROM events WHERE 1=1
        """
        args = []

        def appendFilter(key: str, value: Any):
            nonlocal query
            nonlocal args
            args.append(value)
            query += f'AND {key} = ${len(args)}'

        if maquina_id is not None:
            appendFilter('maquina_id', maquina_id)

        if evento is not None:
            appendFilter('evento', evento)

        if periodo is not None:
            args.append(periodo[0])
            args.append(periodo[1])
            query += f' AND created_at::date BETWEEN ${len(args) - 1} AND ${len(args)}'

        query += f" ORDER BY created_at DESC LIMIT {limit}"

        async with cls._pool.acquire() as conn:  # type:ignore
            rows = await conn.fetch(query, *args)
            return [dict(r) for r in rows]
