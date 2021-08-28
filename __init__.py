"""Integration for Buffalo LinkStation NAS."""

import asyncio
from linkstation import LinkStation
import logging
import sys

"""
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_STARTED,
)
"""

DOMAIN = "linkstation"

_LOGGER = logging.getLogger(__name__)