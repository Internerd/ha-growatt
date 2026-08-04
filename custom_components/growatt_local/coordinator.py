"""Data update coordinator for a single Growatt inverter."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, PROFILE_MIC, PROFILE_SPH_TL3
from .modbus_client import GrowattModbusClient
from .profiles.mic import (
    MIC_HOLDING_BLOCKS,
    MIC_HOLDING_REGISTERS,
    MIC_INPUT_BLOCKS,
    MIC_INPUT_REGISTERS,
)
from .profiles.sph_tl3 import (
    SPH_TL3_HOLDING_BLOCKS,
    SPH_TL3_HOLDING_REGISTERS,
    SPH_TL3_INPUT_BLOCKS,
    SPH_TL3_INPUT_REGISTERS,
    SPH_TL3_TIME_WINDOWS,
)

_LOGGER = logging.getLogger(__name__)

PROFILE_REGISTER_MAPS = {
    PROFILE_SPH_TL3: {
        "input_registers": SPH_TL3_INPUT_REGISTERS,
        "input_blocks": SPH_TL3_INPUT_BLOCKS,
        "holding_registers": SPH_TL3_HOLDING_REGISTERS,
        "holding_blocks": SPH_TL3_HOLDING_BLOCKS,
        "time_windows": SPH_TL3_TIME_WINDOWS,
    },
    PROFILE_MIC: {
        "input_registers": MIC_INPUT_REGISTERS,
        "input_blocks": MIC_INPUT_BLOCKS,
        "holding_registers": MIC_HOLDING_REGISTERS,
        "holding_blocks": MIC_HOLDING_BLOCKS,
        "time_windows": [],
    },
}


def _decode_block(register_map: dict, start_address: int, raw_values: list[int]) -> dict[str, Any]:
    """Decode one contiguous block of raw register values into named values.

    Handles both plain 16-bit registers and 32-bit high/low pairs (the
    latter identified by a "pair" key; the "low" half additionally carries
    "combined_scale" and is where the combined value is produced).
    """
    addr_to_value = {start_address + i: v for i, v in enumerate(raw_values)}
    decoded: dict[str, Any] = {}

    for addr, meta in register_map.items():
        if addr not in addr_to_value:
            continue
        name = meta["name"]

        if "pair" in meta:
            if "combined_scale" not in meta:
                continue  # "high" half; the "low" half does the decoding.
            pair_addr = meta["pair"]
            if pair_addr not in addr_to_value:
                continue
            high_val = addr_to_value[pair_addr]
            low_val = addr_to_value[addr]
            combined = (high_val << 16) | low_val
            if meta.get("signed") and combined >= 0x8000_0000:
                combined -= 0x1_0000_0000
            base_name = name[:-4] if name.endswith("_low") else name
            decoded[base_name] = round(combined * meta["combined_scale"], 3)
            continue

        raw = addr_to_value[addr]
        if meta.get("signed") and raw >= 0x8000:
            raw -= 0x10000
        scale = meta.get("scale", 1)
        decoded[name] = round(raw * scale, 3) if scale != 1 else raw

    return decoded


def pack_time(hour: int, minute: int) -> int:
    """Growatt TOU registers pack a time-of-day as hour*256 + minute."""
    return hour * 256 + minute


def unpack_time(raw: int) -> tuple[int, int]:
    return raw // 256, raw % 256


class GrowattLocalCoordinator(DataUpdateCoordinator):
    """Polls one inverter over Modbus TCP and decodes its registers."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        device_name: str,
        profile: str,
        host: str,
        port: int,
        slave_id: int,
        scan_interval: int,
        timeout: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_name}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.device_name = device_name
        self.profile = profile
        self.client = GrowattModbusClient(host, port, slave_id, timeout)
        self.is_online = False
        self.last_successful_update: datetime | None = None

        maps = PROFILE_REGISTER_MAPS[profile]
        self._input_registers = maps["input_registers"]
        self._input_blocks = maps["input_blocks"]
        self._holding_registers = maps["holding_registers"]
        self._holding_blocks = maps["holding_blocks"]
        self.time_windows = maps["time_windows"]

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.hass.async_add_executor_job(self._poll)
        except Exception as err:  # pylint: disable=broad-except
            self.is_online = False
            raise UpdateFailed(f"Error polling {self.device_name}: {err}") from err

        if data is None:
            self.is_online = False
            raise UpdateFailed(f"No response from {self.device_name}")

        self.is_online = True
        self.last_successful_update = datetime.now()
        return data

    def _poll(self) -> dict[str, Any] | None:
        """Blocking poll, executed in the HA executor thread pool."""
        result: dict[str, Any] = {}
        got_any = False

        for start, count in self._input_blocks:
            raw = self.client.read_input_registers(start, count)
            if raw is None:
                continue
            got_any = True
            result.update(_decode_block(self._input_registers, start, raw))

        holding_values: dict[int, int] = {}
        for start, count in self._holding_blocks:
            raw = self.client.read_holding_registers(start, count)
            if raw is None:
                continue
            got_any = True
            for i, v in enumerate(raw):
                holding_values[start + i] = v
            result.update(_decode_block(self._holding_registers, start, raw))

        # Raw (unscaled) values for the two-register time-of-use windows,
        # keyed by suffix so time.py can look them up without re-reading.
        for _label, suffix, start_reg, end_reg, _enable_reg, _default in self.time_windows:
            if start_reg in holding_values:
                result[f"{suffix}_start_raw"] = holding_values[start_reg]
            if end_reg in holding_values:
                result[f"{suffix}_end_raw"] = holding_values[end_reg]

        if not got_any:
            return None
        return result

    def _find_holding(self, name: str) -> tuple[int, dict] | None:
        for addr, meta in self._holding_registers.items():
            if meta["name"] == name:
                return addr, meta
        return None

    async def async_write_scaled(self, name: str, value: float) -> bool:
        """Write a scaled (e.g. percentage) holding register, then refresh."""
        found = self._find_holding(name)
        if found is None:
            _LOGGER.error("Unknown writable register %s", name)
            return False
        addr, meta = found
        raw_value = int(round(value / meta.get("scale", 1)))
        return await self._write_and_refresh(addr, raw_value)

    async def async_write_switch(self, name: str, value: bool) -> bool:
        """Write a boolean holding register (as 1/0), then refresh."""
        found = self._find_holding(name)
        if found is None:
            _LOGGER.error("Unknown writable register %s", name)
            return False
        addr, _meta = found
        return await self._write_and_refresh(addr, 1 if value else 0)

    async def async_write_time_register(self, address: int, hour: int, minute: int) -> bool:
        """Write one half (start or end) of a time-of-use window."""
        return await self._write_and_refresh(address, pack_time(hour, minute))

    async def _write_and_refresh(self, address: int, raw_value: int) -> bool:
        ok = await self.hass.async_add_executor_job(self.client.write_register, address, raw_value)
        if ok:
            await self.async_request_refresh()
        return ok

    def get_device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self.device_name)},
            "name": self.device_name,
            "manufacturer": "Growatt",
            "model": self.profile,
        }

    async def async_shutdown_client(self) -> None:
        await self.hass.async_add_executor_job(self.client.close)
