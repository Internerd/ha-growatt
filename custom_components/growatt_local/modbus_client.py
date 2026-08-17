"""Thin synchronous Modbus TCP client wrapper for Growatt inverters.

Runs on pymodbus's sync ModbusTcpClient; every call is executed in HA's
executor thread pool by the coordinator, never on the event loop.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

import logging

from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)


class GrowattModbusError(Exception):
    """Raised when a Modbus operation fails."""


class GrowattModbusClient:
    """Blocking Modbus TCP client for a single inverter."""

    def __init__(self, host: str, port: int, slave_id: int, timeout: int) -> None:
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._timeout = timeout
        self._client: ModbusTcpClient | None = None

    def connect(self) -> bool:
        """Open the TCP connection. Safe to call repeatedly."""
        if self._client is not None and self._client.connected:
            return True
        self._client = ModbusTcpClient(host=self._host, port=self._port, timeout=self._timeout)
        return self._client.connect()

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    def read_input_registers(self, address: int, count: int) -> list[int] | None:
        return self._read(is_holding=False, address=address, count=count)

    def read_holding_registers(self, address: int, count: int) -> list[int] | None:
        return self._read(is_holding=True, address=address, count=count)

    def _reconnect(self) -> bool:
        """Drop the socket and dial again."""
        self.close()
        self._client = None
        return self.connect()

    def _call(self, make_call):
        """Invoke a pymodbus call, tolerating the slave/unit kwarg rename.

        pymodbus renamed the slave-address keyword between 2.x, 3.0 and 3.7;
        rather than pin a version, try each spelling once and remember
        nothing - the successful one is found on the first register read and
        the loop costs nothing after that.
        """
        for attempt_kwargs in (
            {"slave": self._slave_id},
            {"unit": self._slave_id},
            {},
        ):
            try:
                return make_call(attempt_kwargs)
            except TypeError:
                continue
        return None

    def _read(self, is_holding: bool, address: int, count: int) -> list[int] | None:
        if not self.connect():
            _LOGGER.debug("Not connected, cannot read %s @ %d", "holding" if is_holding else "input", address)
            return None
        fn = self._client.read_holding_registers if is_holding else self._client.read_input_registers
        response = self._call(lambda kwargs: fn(address=address, count=count, **kwargs))

        if response is None or response.isError():
            _LOGGER.debug("Modbus read error @ %d (count=%d): %s", address, count, response)
            return None
        return list(response.registers)

    def write_register(self, address: int, value: int) -> bool:
        """Write one holding register, retrying once through a fresh socket.

        Gateways and dataloggers that close idle connections used to make
        the first write after a drop fail silently - the control moved in
        the UI and the inverter never heard about it, while reads recovered
        because the next poll simply reconnected. The retry gives writes the
        same second chance.
        """
        for attempt in (1, 2):
            if not self.connect():
                return False

            response = self._call(
                lambda kwargs: self._client.write_register(address=address, value=value, **kwargs)
            )
            if response is not None and not response.isError():
                return True

            if attempt == 1:
                _LOGGER.debug(
                    "Modbus write @ %d = %d failed (%s), reconnecting and retrying",
                    address, value, response,
                )
                if not self._reconnect():
                    _LOGGER.error("Modbus write @ %d = %d failed: reconnect unsuccessful", address, value)
                    return False
            else:
                _LOGGER.error("Modbus write error @ %d = %d: %s", address, value, response)

        return False
