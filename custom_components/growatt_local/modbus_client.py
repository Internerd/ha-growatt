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

    def _read(self, is_holding: bool, address: int, count: int) -> list[int] | None:
        if not self.connect():
            _LOGGER.debug("Not connected, cannot read %s @ %d", "holding" if is_holding else "input", address)
            return None
        fn = self._client.read_holding_registers if is_holding else self._client.read_input_registers
        for attempt_kwargs in (
            {"slave": self._slave_id},
            {"unit": self._slave_id},
            {},
        ):
            try:
                response = fn(address=address, count=count, **attempt_kwargs)
                break
            except TypeError:
                continue
        else:
            return None

        if response is None or response.isError():
            _LOGGER.debug("Modbus read error @ %d (count=%d): %s", address, count, response)
            return None
        return list(response.registers)

    def write_register(self, address: int, value: int) -> bool:
        if not self.connect():
            return False
        for attempt_kwargs in (
            {"slave": self._slave_id},
            {"unit": self._slave_id},
            {},
        ):
            try:
                response = self._client.write_register(address=address, value=value, **attempt_kwargs)
                break
            except TypeError:
                continue
        else:
            return False

        if response is None or response.isError():
            _LOGGER.error("Modbus write error @ %d = %d: %s", address, value, response)
            return False
        return True
