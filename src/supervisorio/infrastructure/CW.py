import asyncio

from datetime import datetime

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from supervisorio.core.logger import get_logger
from supervisorio.core.types.metrics import Metrics
from supervisorio.utils.event_manager import EventManager
from supervisorio.core.types.event_types import EventTypes
from supervisorio.core.types.ModbusReadPayload import ModbusReadPayload
from supervisorio.core.types.MachineEventPayload import MachineStopEventPayload


GAP_ADDRESS = 30720
SIZE_READ = 11


class CheckWeigher(EventManager):
    eventTypes = EventTypes

    def __init__(self, name: str, ip_address: str, port: int, cw_id: str, **kwargs):
        super().__init__()
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.cw_id = cw_id

        self.enabled = kwargs.get('enabled', True)
        self.timeout = kwargs.get('timeout', 5.0)
        self.poll_interval = kwargs.get('poll_interval', 0.1)

        self.metrics = Metrics()
        self.connected = False
        self.payload: None | ModbusReadPayload = None
        self.event_payload: None | MachineStopEventPayload = None

        self.logger = get_logger(name, f'{name}.log')
        self.__modbusClient = ModbusTcpClient(ip_address, port=port)

        self.__last_operation_id = 0    # para controle de transação
        self.__last_operation_type = 0  # para controle de troca de estado
        self._connect_lock = asyncio.Lock()

    @property
    def realtime(self):
        """Retorna um payload contendo o último estado lido"""
        return self.payload

    async def read(self) -> list[int]:
        """
        Faz a leitura dos dados na rede modbus

        """
        self.logger.debug(f"[{self.name}] - Leitura na rede modbus iniciada")
        response = self.__modbusClient.read_holding_registers(
            address=GAP_ADDRESS, count=SIZE_READ)
        self.logger.debug(
            f"[{self.name}] - Leitura na rede modbus terminada - Latencia: {self.metrics.latency}")

        return response.registers

    def dumps(self, data) -> ModbusReadPayload:
        """
        Interpreta os dados lidos 

        """

        self.payload = ModbusReadPayload(
            cw_id=self.cw_id,
            operation_type=data[0],
            weight=data[1],
            classification=data[2],
            ppm=data[3],
            reason=data[7],
            operation_id=data[10],
            timestamp=datetime.now()
        )

        return self.payload

    async def listener(self):
        while self.enabled:
            try:
                start = datetime.now()
                self.metrics.reads_total += 1

                response = await self.safe_read()

                if not response:
                    raise ModbusException(
                        "Nenhuma resposta do equipamento")

                data = self.dumps(response)

                self.metrics.reads_success += 1
                self.metrics.connected = True

                self.metrics.latency = (datetime.now() - start).total_seconds()
                self.metrics.last_latency = self.metrics.latency

                if data.operation_id != self.__last_operation_id:  # Verifica se houve troca de transação
                    if data.operation_type == 1:
                        # resolve se for pesagem
                        await self.dispatch(EventTypes.WEIGHT_READ, data)

                    if self.__last_operation_type != data.operation_type:
                        await self.event_change(data)

                    # Sincroniza os parâmetros para avaliar alteração
                    self.__last_operation_type = data.operation_type
                    self.__last_operation_id = data.operation_id

            except (ModbusException, ConnectionError, OSError, asyncio.TimeoutError) as e:
                self.metrics.reads_timeout += 1
                await self.disconnect()
                await self.reconnect_with_backoff()
                self.logger.warning(f'{e}')

            except Exception as e:
                self.metrics.reads_error += 1
                await self.dispatch(EventTypes.ERROR, e)
                await self.disconnect()
                await self.reconnect_with_backoff()
                self.logger.warning(f'{e}')

            await asyncio.sleep(self.poll_interval)

    async def connect(self):
        async with self._connect_lock:
            if self.connected:
                return True
            self.logger.info(f"[{self.name}] Conectando...")

            if self.__modbusClient.connect():
                self.connected = True
                self.metrics.connected = True
                self.logger.info(f"[{self.name}] conectado")
                return True

    async def disconnect(self):
        self.logger.info(f"[{self.name}] Desconectado")
        self.connected = False
        self.metrics.connected = False

    async def safe_read(self):
        if not self.connected:
            await self.connect()
        else:
            return await asyncio.wait_for(self.read(), timeout=self.timeout)

    async def reconnect_with_backoff(self):
        delay = 1
        max_delay = 30

        while self.enabled and not self.connected:
            try:
                self.metrics.reconnects_total += 1
                await self.connect()
            except Exception as e:
                self.logger.exception(
                    f"[{self.name}] Falha ao reconectar, retry em {delay}s", e)
                await asyncio.sleep(delay)
                delay = min(delay * 2, max_delay)

    async def event_change(self, data: ModbusReadPayload):
        if self.event_payload is not None:
            self.event_payload.ended_at = datetime.now()
            self.event_payload.reason = data.reason
            y = self.event_payload.started_at or datetime.now()
            self.event_payload.timestamp = (self.event_payload.ended_at - (
                y))

            await self.dispatch(EventTypes.EVENT_CHANGED, self.event_payload)

        # Inicia/Reinicia evento para o próximo ciclo
        self.event_payload = MachineStopEventPayload(
            cw_id=self.cw_id,
            started_at=datetime.now(),
            event_type=EventTypes.RUN if data.operation_type == 1 else EventTypes.STOP,
            reason=data.reason,
            timestamp=None,
            ended_at=None)
