import asyncio
from datetime import UTC, datetime

import pytest
from pymodbus.client import AsyncModbusTcpClient

from windconnect.modbus_client import ModbusPoller, TransportError
from windconnect.modbus_server import LocalModbusServer
from windconnect.registers import encode
from windconnect.simulator import TurbineSimulator


def test_real_modbus_round_trip_and_restart():
    async def scenario():
        sample = TurbineSimulator().sample(datetime.now(UTC))
        server = LocalModbusServer(0)
        server.publish(encode(sample))
        try:
            await server.start()
            poller = ModbusPoller(server.port, timeout=0.5, retries=0)
            result = await poller.read()
            assert result.sequence_number == sample.sequence_number
            assert result.power_kw == sample.power_kw
            assert abs((result.timestamp_utc - sample.timestamp_utc).total_seconds()) < 0.001
            # A real FC6 write must be rejected and must not change the telemetry.
            client = AsyncModbusTcpClient("127.0.0.1", port=server.port, timeout=0.5)
            try:
                assert await client.connect()
                assert (await client.write_register(0, 0, device_id=1)).isError()
            finally:
                client.close()
            assert (await poller.read()).sequence_number == sample.sequence_number
            await server.stop()
            with pytest.raises(TransportError):
                await poller.read()
            await server.start()
            assert (await poller.read()).power_kw == sample.power_kw
        finally:
            await server.stop()
        # Immediate same-port restart proves listener cleanup.
        async with LocalModbusServer(server.port):
            pass

    asyncio.run(asyncio.wait_for(scenario(), timeout=8))


def test_port_collision_is_reported():
    async def scenario():
        async with LocalModbusServer(0) as server:
            with pytest.raises(RuntimeError):
                await LocalModbusServer(server.port).start()

    asyncio.run(asyncio.wait_for(scenario(), timeout=5))


def test_silent_tcp_peer_has_bounded_timeout():
    async def scenario():
        tasks = set()

        async def silent(reader, writer):
            task = asyncio.current_task()
            tasks.add(task)
            try:
                await reader.read()
            finally:
                writer.close()
                await writer.wait_closed()
                tasks.remove(task)

        server = await asyncio.start_server(silent, "127.0.0.1", 0)
        try:
            port = server.sockets[0].getsockname()[1]
            with pytest.raises(TransportError, match="2 Versuch"):
                await ModbusPoller(port, timeout=0.1, retries=1).read()
        finally:
            server.close()
            await server.wait_closed()
            if tasks:
                await asyncio.wait_for(asyncio.gather(*tasks), 1)

    asyncio.run(asyncio.wait_for(scenario(), timeout=3))
