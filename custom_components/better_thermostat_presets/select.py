import json
import re

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_added_domain,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DEFAULT_EXCLUDED_PRESETS,
    DEFAULT_ENTITY_ID_SUFFIX,
    DEFAULT_NAME_MODE,
    DEFAULT_NAME_SUFFIX,
    DEFAULT_NAME_PATTERN,
    DEFAULT_NAME_REPLACEMENT,
    DEFAULT_AUTOCREATE,
    NAME_MODE_REGEX,
    DOMAIN,
    CONF_EXCLUDED_PRESETS,
    CONF_ENTITY_EXCLUDED_PRESETS,
    CONF_ENTITY_ID_SUFFIX,
    CONF_AUTOCREATE,
    CONF_SELECTED_ENTITIES,
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


def get_source_friendly_name(hass, source):
    """Return the Better Thermostat friendly name without falling back to its ID."""

    state = hass.states.get(source.entity_id) if hasattr(hass, "states") else None
    if state is not None:
        if friendly_name := state.attributes.get("friendly_name"):
            return str(friendly_name).strip()

    for candidate in (source.name, source.original_name):
        if candidate and candidate != source.entity_id:
            return str(candidate).strip()

    return "Better Thermostat"


def get_entity_exclusion_store(hass):
    """Return shared per-thermostat exclusions for this integration."""

    if not hasattr(hass, "data"):
        return {}
    return hass.data.setdefault(DOMAIN, {}).setdefault(
        "entity_excluded_presets",
        {},
    )


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
        source_object_id = source_entity_id.removeprefix("climate.")
        self._suggested_object_id = slugify(
            f"{source_object_id}_{entity_id_suffix}"
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
    def suggested_object_id(self):
        """Return a slug for the selector without a source climate domain prefix."""

        return self._suggested_object_id

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
        excluded = set(self.excluded_presets)
        excluded.update(
            get_entity_exclusion_store(self.hass).get(self.source_entity_id, [])
        )

        return [
            preset
            for preset in presets
            if preset.lower() not in excluded
        ]

    async def async_added_to_hass(self):
        """Watch the per-entity exclusions text control."""

        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self.source_entity_id}_excluded_presets",
                self._async_exclusions_changed,
            )
        )

    @callback
    def _async_exclusions_changed(self):
        """Refresh options after the exclusions text changes."""

        self.async_write_ha_state()

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

    added_entity_ids = set()
    exclusion_store = get_entity_exclusion_store(hass)

    def create_select(source):
        """Build a selector for a source thermostat."""

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
        source_excluded.update(
            exclusion_store.get(source.entity_id, [])
        )

        source_device_info = {
            "identifiers": {(DOMAIN, source.unique_id)},
            "name": build_friendly_name(
                get_source_friendly_name(hass, source),
                name_suffix,
                name_pattern,
                name_replacement,
                name_mode,
            ),
        }
        if getattr(source, "device_id", None):
            source_device_info["via_device_id"] = source.device_id

        entity = BetterThermostatPresetSelect(
            source.entity_id,
            source.unique_id,
            get_source_friendly_name(hass, source),
            source_excluded,
            entity_suffix,
            name_suffix,
            name_pattern,
            name_replacement,
            name_mode,
            source_device_info=source_device_info,
        )

        registry = er.async_get(hass)
        if hasattr(registry, "async_get_entity_id"):
            existing_entity_id = registry.async_get_entity_id(
                "select",
                DOMAIN,
                entity.unique_id,
            )
            legacy_entity_id = f"select.climate_{entity.suggested_object_id}"
            if existing_entity_id == legacy_entity_id:
                registry.async_update_entity(
                    existing_entity_id,
                    new_entity_id=f"select.{entity.suggested_object_id}",
                )

        added_entity_ids.add(source.entity_id)
        return entity

    autocreate = settings.get(CONF_AUTOCREATE, DEFAULT_AUTOCREATE)
    selected_entity_ids = set(settings.get(CONF_SELECTED_ENTITIES, []))
    sources = get_source_entities(hass)
    async_add_entities([
        create_select(source)
        for source in sources
        if autocreate or source.entity_id in selected_entity_ids
    ])

    if not autocreate:
        return

    @callback
    def async_source_added(event):
        """Create a selector when a Better Thermostat is added later."""

        entity_id = event.data["entity_id"]
        if entity_id in added_entity_ids:
            return

        source = er.async_get(hass).async_get(entity_id)
        if (
            source is None
            or source.platform != "better_thermostat"
            or source.domain != "climate"
            or source.disabled_by is not None
        ):
            return

        async_add_entities([create_select(source)])

    entry.async_on_unload(
        async_track_state_added_domain(hass, "climate", async_source_added)
    )
