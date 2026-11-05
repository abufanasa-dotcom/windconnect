"""Loopback-only asynchronous Modbus server with explicit lifecycle."""

from functools import partial

from pymodbus.constants import ExcCodes
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer

from windconnect.registers import REGISTER_COUNT

HOST = "127.0.0.1"


class ReadOnlyDevice(ModbusDeviceContext):
    async def async_setValues(self, func_code, address, values):
        return ExcCodes.ILLEGAL_FUNCTION


class LocalModbusServer:
    def __init__(self, port: int = 15020):
        if not 0 <= port <= 65535:
            raise ValueError("Port außerhalb 0–65535")
        self.port = port
        # PyModbus 3.11 adds 1 to protocol addresses before datastore access.
        self.device = ReadOnlyDevice(hr=ModbusSequentialDataBlock(1, [0] * REGISTER_COUNT))
        self._server: ModbusTcpServer | None = None

    @property
    def running(self) -> bool:
        return self._server is not None

    def publish(self, registers: list[int]) -> None:
        if len(registers) != REGISTER_COUNT:
            raise ValueError("Vollständigen Registerblock veröffentlichen")
        self.device.setValues(3, 0, registers)

    async def start(self) -> None:
        if self.running:
            return
        server = ModbusTcpServer(
            ModbusServerContext(devices={1: self.device}, single=False),
            address=(HOST, self.port),
        )
        # Pinned 3.11 transport defaults to SO_REUSEADDR, which permits competing
        # Windows listeners. Disable it via its connection factory.
        server.call_create = partial(server.call_create, reuse_address=False)
        try:
            await server.serve_forever(background=True)
        except BaseException:
            await server.shutdown()
            raise
        self.port = server.transport.sockets[0].getsockname()[1]
        self._server = server

    async def stop(self) -> None:
        if self._server is not None:
            await self._server.shutdown()
            self._server = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *_args):
        await self.stop()
