"""Constants for the Growatt Local integration."""
from homeassistant.const import Platform

DOMAIN = "growatt_local"

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER]

CONF_DEVICE_NAME = "device_name"
CONF_PROFILE = "profile"
CONF_SLAVE_ID = "slave_id"

PROFILE_SPH_TL3 = "sph_tl3"
PROFILE_MIC = "mic"

PROFILE_LABELS = {
    PROFILE_SPH_TL3: "SPH-TL3 (3-10kW, three-phase hybrid)",
    PROFILE_MIC: "MIC (0.6-3.3kW, single-phase)",
}

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_SCAN_INTERVAL = 10
DEFAULT_TIMEOUT = 10

MANUFACTURER = "Growatt"
