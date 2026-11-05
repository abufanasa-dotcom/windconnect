"""Bounded polling: retries+1 attempts, each with a strict total timeout."""

import asyncio

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from windconnect.modbus_server import HOST
from windconnect.registers import REGISTER_COUNT, decode


class TransportError(ConnectionError):
    pass


class ModbusPoller:
    def __init__(self, port: int = 15020, timeout: float = 0.5, retries: int = 1):
        if not 1 <= port <= 65535 or timeout <= 0 or not 0 <= retries <= 5:
            raise ValueError("Ungültiger Port, Timeout oder Retry-Wert (0–5)")
        self.port, self.timeout, self.retries = port, timeout, retries

    async def read_registers(self) -> list[int]:
        error = "Unbekannter Verbindungsfehler"
        for _attempt in range(self.retries + 1):
            client = AsyncModbusTcpClient(
                HOST,
                port=self.port,
                timeout=self.timeout,
                retries=0,
                reconnect_delay=0,
            )
            try:
                async with asyncio.timeout(self.timeout):
                    if not await client.connect():
                        raise TransportError("TCP-Verbindung abgelehnt")
                    response = await client.read_holding_registers(
                        0,
                        count=REGISTER_COUNT,
                        device_id=1,
                    )
                    if response.isError():
                        raise TransportError(f"Modbus-Fehlerantwort: {response}")
                    return response.registers
            except (OSError, TimeoutError, ModbusException, TransportError) as exc:
                error = f"{type(exc).__name__}: {exc}"
            finally:
                client.close()
        raise TransportError(f"{self.retries + 1} Versuch(e) fehlgeschlagen: {error}")

    async def read(self):
        return decode(await self.read_registers())
