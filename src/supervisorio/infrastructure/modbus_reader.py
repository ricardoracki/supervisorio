import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar, Generic

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException, ConnectionException
from supervisorio.core.logger import get_logger
from supervisorio.core.types.metrics import Metrics

logger = get_logger(__name__, 'collector.log')
T = TypeVar("T")


class ModbusReader(ABC, Generic[T]):
    def __init__(self, name: str, ip_address: str, port: int = 502,
                 timeout: float = 2.0, pool_interval: float = 1.0, **kwargs) -> None:
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.pool_interval = pool_interval
        self.metrics = Metrics()
        self.__connect_lock = asyncio.Lock()
        self._client_modbus = AsyncModbusTcpClient(
            ip_address, port=port, timeout=timeout)

    async def connect(self) -> bool:
        """Tenta conectar silenciosamente."""
        async with self.__connect_lock:
            if self._client_modbus.connected:
                self.metrics.connected = True
                return True

            try:
                # Tentativa de conexão rápida
                connected = await self._client_modbus.connect()
                if connected:
                    logger.info(f'[{self.name}] Equipamento ficou online.')
                    self.metrics.connected = True
                    return True
            except Exception:
                pass  # Silencioso: equipamento offline é esperado

            self.metrics.connected = False
            return False

    async def read(self, first_address: int, len_address: int) -> list[int]:
        """Lê os registradores de forma assíncrona."""
        self.metrics.reads_total += 1
        start = datetime.now()

        response = await self._client_modbus.read_holding_registers(
            first_address, count=len_address
        )

        self.metrics.latency = (datetime.now() - start).total_seconds()

        if response.isError():
            # Erro de protocolo (máquina ligada mas respondeu errado)
            logger.debug(f"[{self.name}] Resposta inválida: {response}")
            return []

        self.metrics.reads_success += 1
        return response.registers

    async def safe_read(self, first_address: int, len_address: int) -> list[int]:
        """
        Leitura 'suave': se o equipamento estiver desligado, 
        apenas retorna uma lista vazia sem alardes.
        """
        try:
            # Se não conectar, apenas sai em silêncio
            if not await self.connect():
                return []

            # Executa a leitura com timeout
            return await asyncio.wait_for(
                self.read(first_address, len_address),
                timeout=self.timeout
            )

        except asyncio.TimeoutError:
            # Situação normal: equipamento pode ter sido desligado
            self.metrics.reads_timeout += 1
            self.metrics.connected = False
            logger.debug(f"[{self.name}] Equipamento indisponível (Timeout).")
            return []

        except (ModbusException, ConnectionException, OSError):
            # Perda física de conexão: limpa o estado e aguarda próxima tentativa
            self.metrics.connected = False
            self._client_modbus.close()
            return []

        except Exception as e:
            # Apenas erros realmente inesperados geram log de aviso
            logger.warning(
                f"[{self.name}] Evento inesperado na comunicação: {e}")
            return []

    async def disconnect(self):
        logger.info(f"[{self.name}] Desconectado")
        self.connected = False
        self.metrics.connected = False

    @abstractmethod
    def dumps(self) -> T:
        """
        Conversor de dados lidos do modbus em informação válida
        """
        ...

    @abstractmethod
    async def listener(self) -> None:
        """Executor cíclico de leituras"""
        ...
