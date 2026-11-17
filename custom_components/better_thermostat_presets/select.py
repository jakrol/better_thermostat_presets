import json
import re

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_EXCLUDED_PRESETS,
    DEFAULT_ENTITY_ID_SUFFIX,
    DEFAULT_NAME_MODE,
    DEFAULT_NAME_SUFFIX,
    DEFAULT_NAME_PATTERN,
    DEFAULT_NAME_REPLACEMENT,
    NAME_MODE_PREFIX,
    NAME_MODE_REGEX,
    CONF_EXCLUDED_PRESETS,
    CONF_ENTITY_EXCLUDED_PRESETS,
    CONF_ENTITY_ID_SUFFIX,
    CONF_NAME_SUFFIX,
    CONF_NAME_MODE,
    CONF_NAME_PATTERN,
    CONF_NAME_REPLACEMENT,
)


def slugify(value: str) -> str:
    """Convert a string into a valid entity ID component."""

    value = value.lower()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    return value.strip("_")


def build_friendly_name(
    source_name,
    name_suffix,
    name_pattern="",
    name_replacement="",
    name_mode=DEFAULT_NAME_MODE,
):
    """Build the selector display name from the thermostat's friendly name."""

    source_name = (source_name or "").strip()
    if not source_name:
        return (name_suffix or "").strip()

    if name_mode == NAME_MODE_REGEX and name_pattern:
        try:
            replacement = name_replacement or r"\g<0>"
            result = re.sub(name_pattern, replacement, source_name)
            if result.strip():
                return result.strip()
        except re.error:
            pass

    if name_suffix:
        return f"{source_name}: {name_suffix}"

    return source_name


def get_source_entities(hass):
    """Find climate entities provided by Better Thermostat."""

    registry = er.async_get(hass)

    return [
        entity
        for entity in registry.entities.values()
        if entity.platform == "better_thermostat"
        and entity.domain == "climate"
        and entity.disabled_by is None
    ]


class BetterThermostatPresetSelect(SelectEntity):
    """Represent a Better Thermostat preset selector."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:thermostat"

    def __init__(
        self,
        source_entity_id,
        source_unique_id,
        source_name,
        excluded_presets,
        entity_id_suffix,
        name_suffix,
        name_pattern="",
        name_replacement="",
        name_mode=DEFAULT_NAME_MODE,
        source_device_info=None,
    ):
        self.source_entity_id = source_entity_id
        self.excluded_presets = excluded_presets

        self._attr_unique_id = (
            f"{source_unique_id}_{slugify(entity_id_suffix)}"
        )
        self._attr_device_info = source_device_info

        self._attr_name = build_friendly_name(
            source_name,
            name_suffix,
            name_pattern,
            name_replacement,
            name_mode,
        )

    @property
    def available(self):
        """Return source availability."""

        state = self.hass.states.get(self.source_entity_id)

        return (
            state is not None
            and state.state not in ("unavailable", "unknown")
        )

    @property
    def current_option(self):
        """Return the currently selected preset."""

        state = self.hass.states.get(self.source_entity_id)

        if state is None:
            return None

        return state.attributes.get("preset_mode")

    @property
    def options(self):
        """Return available presets."""

        state = self.hass.states.get(self.source_entity_id)

        if state is None:
            return []

        presets = state.attributes.get("preset_modes", [])

        return [
            preset
            for preset in presets
            if preset.lower() not in self.excluded_presets
        ]

    async def async_select_option(self, option):
        """Set a Better Thermostat preset."""

        if option not in self.options:
            return

        await self.hass.services.async_call(
            "climate",
            "set_preset_mode",
            {
                "entity_id": self.source_entity_id,
                "preset_mode": option,
            },
            blocking=True,
        )

        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up Better Thermostat preset selectors."""

    settings = entry.data | getattr(entry, "options", {})
    excluded = {
        str(item).strip().lower()
        for item in settings.get(
            CONF_EXCLUDED_PRESETS,
            DEFAULT_EXCLUDED_PRESETS,
        )
        if str(item).strip()
    }

    entity_excluded = settings.get(CONF_ENTITY_EXCLUDED_PRESETS, {})
    if isinstance(entity_excluded, str):
        try:
            entity_excluded = json.loads(entity_excluded)
        except (TypeError, ValueError):
            entity_excluded = {}

    entity_suffix = settings.get(
        CONF_ENTITY_ID_SUFFIX,
        DEFAULT_ENTITY_ID_SUFFIX,
    )

    name_suffix = settings.get(
        CONF_NAME_SUFFIX,
        DEFAULT_NAME_SUFFIX,
    )

    name_mode = settings.get(
        CONF_NAME_MODE,
        DEFAULT_NAME_MODE,
    )

    name_pattern = settings.get(
        CONF_NAME_PATTERN,
        DEFAULT_NAME_PATTERN,
    )

    name_replacement = settings.get(
        CONF_NAME_REPLACEMENT,
        DEFAULT_NAME_REPLACEMENT,
    )

    sources = get_source_entities(hass)
    device_registry = dr.async_get(hass)

    entities = []

    for source in sources:
        source_excluded = set(excluded)
        if isinstance(entity_excluded, dict):
            for entity_id, presets in entity_excluded.items():
                if entity_id == source.entity_id:
                    if isinstance(presets, str):
                        source_excluded.update(
                            preset.strip().lower()
                            for preset in presets.split(",")
                            if preset.strip()
                        )
                    else:
                        source_excluded.update(
                            str(preset).strip().lower()
                            for preset in presets
                            if str(preset).strip()
                        )

        source_device = None
        if getattr(source, "device_id", None):
            source_device = device_registry.async_get(source.device_id)

        source_device_info = None
        if source_device is not None and getattr(source_device, "identifiers", None):
            source_device_info = {"identifiers": source_device.identifiers}

        entity = BetterThermostatPresetSelect(
            source.entity_id,
            source.unique_id,
            source.name or source.original_name or source.entity_id,
            source_excluded,
            entity_suffix,
            name_suffix,
            name_pattern,
            name_replacement,
            name_mode,
            source_device_info=source_device_info,
        )

        entities.append(entity)

    async_add_entities(entities)
