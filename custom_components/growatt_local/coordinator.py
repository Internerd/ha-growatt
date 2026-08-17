"""Data update coordinator for a single Growatt inverter.

AI-generated (Claude/Anthropic via Claude Code) under human direction and
review; see /NOTICE.md at the repository root for details.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MANUFACTURER, PROFILE_LABELS, PROFILE_MIC, PROFILE_SPH_TL3
from .modbus_client import GrowattModbusClient
from .profiles.mic import (
    MIC_HOLDING_BLOCKS,
    MIC_HOLDING_REGISTERS,
    MIC_INPUT_BLOCKS,
    MIC_INPUT_REGISTERS,
    MIC_USE_MPPT_ENERGY_TODAY,
    MIC_V201_HOLDING_BLOCKS,
    MIC_V201_HOLDING_REGISTERS,
    MIC_V201_INPUT_BLOCKS,
    MIC_V201_INPUT_REGISTERS,
)
from .profiles.sph_tl3 import (
    SPH_TL3_HOLDING_BLOCKS,
    SPH_TL3_HOLDING_REGISTERS,
    SPH_TL3_INPUT_BLOCKS,
    SPH_TL3_INPUT_REGISTERS,
    SPH_TL3_TIME_WINDOWS,
    SPH_TL3_USE_MPPT_ENERGY_TODAY,
    SPH_TL3_V201_HOLDING_BLOCKS,
    SPH_TL3_V201_HOLDING_REGISTERS,
    SPH_TL3_V201_INPUT_BLOCKS,
    SPH_TL3_V201_INPUT_REGISTERS,
)

_LOGGER = logging.getLogger(__name__)

PROFILE_REGISTER_MAPS = {
    PROFILE_SPH_TL3: {
        "input_registers": SPH_TL3_INPUT_REGISTERS,
        "input_blocks": SPH_TL3_INPUT_BLOCKS,
        "holding_registers": SPH_TL3_HOLDING_REGISTERS,
        "holding_blocks": SPH_TL3_HOLDING_BLOCKS,
        "time_windows": SPH_TL3_TIME_WINDOWS,
        "use_mppt_energy_today": SPH_TL3_USE_MPPT_ENERGY_TODAY,
        "has_battery": True,
        "v201_input_registers": SPH_TL3_V201_INPUT_REGISTERS,
        "v201_input_blocks": SPH_TL3_V201_INPUT_BLOCKS,
        "v201_holding_registers": SPH_TL3_V201_HOLDING_REGISTERS,
        "v201_holding_blocks": SPH_TL3_V201_HOLDING_BLOCKS,
    },
    PROFILE_MIC: {
        "input_registers": MIC_INPUT_REGISTERS,
        "input_blocks": MIC_INPUT_BLOCKS,
        "holding_registers": MIC_HOLDING_REGISTERS,
        "holding_blocks": MIC_HOLDING_BLOCKS,
        "time_windows": [],
        "use_mppt_energy_today": MIC_USE_MPPT_ENERGY_TODAY,
        "has_battery": False,
        "v201_input_registers": MIC_V201_INPUT_REGISTERS,
        "v201_input_blocks": MIC_V201_INPUT_BLOCKS,
        "v201_holding_registers": MIC_V201_HOLDING_REGISTERS,
        "v201_holding_blocks": MIC_V201_HOLDING_BLOCKS,
    },
}


def register_map_for(profile: str, protocol_v201: bool) -> dict[str, Any]:
    """Effective register map for a profile, with the V2.01 overlay applied.

    The platforms use this to decide which entities exist, so it has to
    return the same merged view the coordinator polls.
    """
    maps = PROFILE_REGISTER_MAPS[profile]
    if not protocol_v201:
        return maps
    return {
        **maps,
        "input_registers": {**maps["input_registers"], **maps["v201_input_registers"]},
        "input_blocks": [*maps["input_blocks"], *maps["v201_input_blocks"]],
        "holding_registers": {**maps["holding_registers"], **maps["v201_holding_registers"]},
        "holding_blocks": [*maps["holding_blocks"], *maps["v201_holding_blocks"]],
    }


def _decode_block(register_map: dict, start_address: int, raw_values: list[int]) -> dict[str, Any]:
    """Decode one contiguous block of raw register values into named values.

    Handles both plain 16-bit registers and 32-bit high/low pairs (the
    latter identified by a "pair" key; the "low" half additionally carries
    "combined_scale" and is where the combined value is produced).

    A register carrying "maps_to" writes its value under that name instead
    of its own - that is how the V2.01 overlay replaces a legacy value
    (e.g. the VPP battery SOH register taking over "bms_soh").
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
            # The pair's target name lives on the "high" half when it
            # carries maps_to (that is where upstream puts it), otherwise
            # derive it from this register's own name.
            high_meta = register_map.get(pair_addr, {})
            base_name = (
                high_meta.get("maps_to")
                or meta.get("maps_to")
                or (name[:-4] if name.endswith("_low") else name)
            )
            decoded[base_name] = round(combined * meta["combined_scale"], 3)
            continue

        raw = addr_to_value[addr]
        if meta.get("signed") and raw >= 0x8000:
            raw -= 0x10000
        scale = meta.get("scale", 1)
        value = round(raw * scale, 3) if scale != 1 else raw
        decoded[meta.get("maps_to", name)] = value

    return decoded


def _chunk_block(start: int, count: int, max_size: int) -> list[tuple[int, int]]:
    """Split one register block into requests of at most `max_size` registers."""
    if max_size <= 0 or count <= max_size:
        return [(start, count)]
    return [
        (start + offset, min(max_size, count - offset))
        for offset in range(0, count, max_size)
    ]


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
        offline_scan_interval: int,
        timeout: int,
        invert_grid_power: bool = False,
        invert_battery_power: bool = False,
        protocol_v201: bool = False,
        block_size: int = 0,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_name}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.device_name = device_name
        self.profile = profile
        self.protocol_v201 = protocol_v201
        self.client = GrowattModbusClient(host, port, slave_id, timeout)
        self.is_online = False
        self.last_successful_update: datetime | None = None

        self._online_interval = timedelta(seconds=scan_interval)
        self._offline_interval = timedelta(seconds=offline_scan_interval)
        self._invert_grid_power = invert_grid_power
        self._invert_battery_power = invert_battery_power
        self._block_size = block_size

        maps = register_map_for(profile, protocol_v201)
        self._input_registers = maps["input_registers"]
        self._input_blocks = maps["input_blocks"]
        self._holding_registers = maps["holding_registers"]
        self._holding_blocks = maps["holding_blocks"]
        self._use_mppt_energy_today = maps["use_mppt_energy_today"]
        self.has_battery = maps["has_battery"]
        self.time_windows = maps["time_windows"]

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.hass.async_add_executor_job(self._poll)
        except Exception as err:  # pylint: disable=broad-except
            self._set_online(False)
            raise UpdateFailed(f"Error polling {self.device_name}: {err}") from err

        if data is None:
            self._set_online(False)
            raise UpdateFailed(f"No response from {self.device_name}")

        self._set_online(True)
        self.last_successful_update = datetime.now(timezone.utc)
        data["last_update"] = self.last_successful_update
        return data

    def _set_online(self, online: bool) -> None:
        """Track reachability and switch polling cadence accordingly.

        Slows down to `offline_scan_interval` while unreachable (avoids
        hammering a device that's off/unreachable) and back to the normal
        `scan_interval` once it responds again.
        """
        self.is_online = online
        self.update_interval = self._online_interval if online else self._offline_interval

    def _poll(self) -> dict[str, Any] | None:
        """Blocking poll, executed in the HA executor thread pool."""
        result: dict[str, Any] = {}
        got_any = False

        for start, count in self._input_blocks:
            for chunk_start, chunk_count in _chunk_block(start, count, self._block_size):
                raw = self.client.read_input_registers(chunk_start, chunk_count)
                if raw is None:
                    continue
                got_any = True
                result.update(_decode_block(self._input_registers, chunk_start, raw))

        holding_values: dict[int, int] = {}
        for start, count in self._holding_blocks:
            for chunk_start, chunk_count in _chunk_block(start, count, self._block_size):
                raw = self.client.read_holding_registers(chunk_start, chunk_count)
                if raw is None:
                    continue
                got_any = True
                for i, v in enumerate(raw):
                    holding_values[chunk_start + i] = v
                result.update(_decode_block(self._holding_registers, chunk_start, raw))

        # Raw (unscaled) values for the two-register time-of-use windows,
        # keyed by suffix so time.py can look them up without re-reading.
        for _label, suffix, start_reg, end_reg, _enable_reg, _default in self.time_windows:
            if start_reg in holding_values:
                result[f"{suffix}_start_raw"] = holding_values[start_reg]
            if end_reg in holding_values:
                result[f"{suffix}_end_raw"] = holding_values[end_reg]

        if not got_any:
            return None

        # Manual override for inverters/firmware that report grid or
        # battery power flow with the opposite sign convention than
        # expected (see the "Invert Grid/Battery Power" options - these
        # mirror the same-named settings in the original integration).
        if self._invert_battery_power:
            charge = result.get("battery_charge_power")
            discharge = result.get("battery_discharge_power")
            if charge is not None and discharge is not None:
                result["battery_charge_power"], result["battery_discharge_power"] = discharge, charge

        self._add_derived_values(result)
        return result

    # ------------------------------------------------------------------
    # Derived values
    #
    # Everything below reproduces a value the upstream integration exposes
    # as its own entity but computes rather than reads: the grid power
    # trio, house/self consumption, signed battery power, and the net grid
    # energy counters. Keeping the arithmetic in one place means the sensor
    # platform stays a plain register-to-entity mapping.
    # ------------------------------------------------------------------

    def _add_derived_values(self, result: dict[str, Any]) -> None:
        get = lambda key: result.get(key) or 0  # noqa: E731

        solar = get("pv_total_power")
        export = get("power_to_grid")
        # Growatt documents grid import at two addresses and firmware
        # differs on which it fills. 1021/1022 ("PactouserTotal") is the
        # newer one and wins whenever the read succeeded - including when
        # it reports a legitimate zero, which on a hybrid covering its own
        # load is a normal state rather than a missing value. The older
        # 1015/1016 pair is only consulted where the newer one is absent.
        if "power_to_user" not in result and "power_to_user_legacy" in result:
            result["power_to_user"] = result["power_to_user_legacy"]
        import_power = get("power_to_user")
        load = get("power_to_load")
        charge = get("battery_charge_power")
        discharge = get("battery_discharge_power")

        # Signed grid power, positive = exporting. The directional
        # registers win when either is non-zero; the energy balance is only
        # a fallback for firmware that leaves both at 0.
        if export > 0:
            grid_power = export
        elif import_power > 0:
            grid_power = -import_power
        else:
            grid_power = (solar + discharge) - (load + charge)

        # invert_grid_power corrects a backwards CT clamp. It applies to
        # the signed sensor only - the always-positive import/export pair
        # is derived from the directional registers, whose meaning does not
        # depend on the sign convention.
        result["grid_power"] = round(-grid_power if self._invert_grid_power else grid_power, 1)
        result["grid_export_power"] = round(max(0, grid_power), 1)
        result["grid_import_power"] = round(max(0, -grid_power), 1)

        # Self consumption: solar that did not leave the building.
        if export > 0:
            self_consumption = solar - export
        elif load > 0:
            self_consumption = min(solar, load)
        else:
            self_consumption = solar
        result["self_consumption"] = round(max(0, self_consumption), 1)
        result["self_consumption_percentage"] = (
            round(max(0, self_consumption) / solar * 100, 1) if solar else 0
        )

        # House consumption: the load register when the inverter provides
        # one, otherwise the full energy balance. Note that "power to load"
        # on this hardware omits grid import, so the fallback has to add it
        # back rather than reuse self_consumption.
        if load == 0 and (charge or discharge or export or import_power):
            load = solar + discharge - charge + import_power - export
        result["house_consumption"] = round(max(0, load), 1)

        if self.has_battery:
            # Positive = charging, negative = discharging.
            if charge > 0:
                result["battery_power"] = round(charge, 1)
            elif discharge > 0:
                result["battery_power"] = round(-discharge, 1)
            else:
                result["battery_power"] = 0
            # The V2.01 overlay reads a signed battery power register
            # directly; when present it is authoritative.
            if "battery_power_vpp" in result:
                result["battery_power"] = result["battery_power_vpp"]

        # Net grid energy (export - import), positive = net export today.
        for period in ("today", "total"):
            export_energy = result.get(f"energy_to_grid_{period}")
            import_energy = result.get(f"energy_to_user_{period}")
            if export_energy is None or import_energy is None:
                continue
            net = export_energy - import_energy
            result[f"grid_energy_{period}"] = round(-net if self._invert_grid_power else net, 2)

        # Energy Today from the per-MPPT DC counters.
        #
        # On these hybrids register 53/54 counts everything the inverter put
        # onto AC, battery discharge included - so it climbs overnight while
        # the house runs off the battery, and the Energy Dashboard records
        # stored energy a second time as fresh production. The per-string DC
        # counters track solar input only.
        if self._use_mppt_energy_today:
            strings = [result.get(f"pv{n}_energy_today") for n in (1, 2, 3)]
            if any(v is not None for v in strings):
                mppt_sum = round(sum(v for v in strings if v is not None), 2)
                # Guard against a corrupt read (an unresponsive register
                # block reads back as 0xFFFF and decodes to ~6.5 M kWh).
                if mppt_sum < 1000:
                    result["energy_today"] = mppt_sum
                else:
                    _LOGGER.warning(
                        "%s: per-MPPT energy today of %s kWh is implausible, "
                        "falling back to the AC output register",
                        self.device_name,
                        mppt_sum,
                    )

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

    async def async_write_raw(self, name: str, raw_value: int) -> bool:
        """Write an unscaled holding register value (select options), then refresh."""
        found = self._find_holding(name)
        if found is None:
            _LOGGER.error("Unknown writable register %s", name)
            return False
        addr, _meta = found
        return await self._write_and_refresh(addr, raw_value)

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
            "manufacturer": MANUFACTURER,
            "model": PROFILE_LABELS.get(self.profile, self.profile),
        }

    async def async_shutdown_client(self) -> None:
        await self.hass.async_add_executor_job(self.client.close)
