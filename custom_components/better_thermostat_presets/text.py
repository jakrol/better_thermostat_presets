"""Per-thermostat preset exclusion controls."""

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_added_domain
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_AUTOCREATE,
    CONF_ENTITY_EXCLUDED_PRESETS,
    CONF_SELECTED_ENTITIES,
    CONF_NAME_MODE,
    CONF_NAME_PATTERN,
    CONF_NAME_REPLACEMENT,
    CONF_NAME_SUFFIX,
    DOMAIN,
    DEFAULT_AUTOCREATE,
    DEFAULT_NAME_MODE,
    DEFAULT_NAME_PATTERN,
    DEFAULT_NAME_REPLACEMENT,
    DEFAULT_NAME_SUFFIX,
)
from .select import (
    build_friendly_name,
    get_entity_exclusion_store,
    get_source_entities,
    get_source_friendly_name,
    slugify,
)


class BetterThermostatExcludedPresetsText(RestoreEntity, TextEntity):
    """Editable exclusions for a Better Thermostat preset selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "excluded_presets"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 255

    def __init__(
        self,
        source_entity_id,
        source_unique_id,
        initial_value,
        source_device_info=None,
    ):
        """Initialize an exclusion text entity."""

        self.source_entity_id = source_entity_id
        self._attr_unique_id = f"{slugify(source_unique_id)}_excluded_presets"
        self._attr_device_info = source_device_info
        self._attr_native_value = initial_value

    async def async_added_to_hass(self):
        """Restore the user-configured exclusions after a restart."""

        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in ("unknown", "unavailable"):
                self._attr_native_value = last_state.state
        get_entity_exclusion_store(self.hass)[self.source_entity_id] = [
            preset.strip().lower()
            for preset in (self._attr_native_value or "").split(",")
            if preset.strip()
        ]

    async def async_set_value(self, value):
        """Update the exclusions shown for this thermostat."""

        self._attr_native_value = value[: self._attr_native_max]
        get_entity_exclusion_store(self.hass)[self.source_entity_id] = [
            preset.strip().lower()
            for preset in self._attr_native_value.split(",")
            if preset.strip()
        ]
        self.async_write_ha_state()
        async_dispatcher_send(
            self.hass,
            f"{DOMAIN}_{self.source_entity_id}_excluded_presets",
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up exclusion controls for Better Thermostat entities."""

    settings = entry.data | getattr(entry, "options", {})
    autocreate = settings.get(CONF_AUTOCREATE, DEFAULT_AUTOCREATE)
    selected_entity_ids = set(settings.get(CONF_SELECTED_ENTITIES, []))

    entity_excluded = settings.get(CONF_ENTITY_EXCLUDED_PRESETS, {})
    exclusion_store = get_entity_exclusion_store(hass)
    if isinstance(entity_excluded, dict):
        for entity_id, presets in entity_excluded.items():
            if isinstance(presets, str):
                presets = presets.split(",")
            exclusion_store[entity_id] = [
                str(preset).strip().lower()
                for preset in presets
                if str(preset).strip()
            ]

    def create_text_entity(source):
        """Create the exclusion control for one source entity."""

        device_info = {
            "identifiers": {(DOMAIN, source.unique_id)},
            "name": build_friendly_name(
                get_source_friendly_name(hass, source),
                settings.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX),
                settings.get(CONF_NAME_PATTERN, DEFAULT_NAME_PATTERN),
                settings.get(
                    CONF_NAME_REPLACEMENT,
                    DEFAULT_NAME_REPLACEMENT,
                ),
                settings.get(CONF_NAME_MODE, DEFAULT_NAME_MODE),
            ),
        }
        if getattr(source, "device_id", None):
            device_info["via_device_id"] = source.device_id

        value = entity_excluded.get(source.entity_id, [])
        if isinstance(value, str):
            initial_value = value
        else:
            initial_value = ", ".join(str(preset) for preset in value)

        return BetterThermostatExcludedPresetsText(
            source.entity_id,
            source.unique_id,
            initial_value,
            source_device_info=device_info,
        )

    added_entity_ids = set()

    def add_source(source):
        """Add a text control once for each source climate entity."""

        if source.entity_id in added_entity_ids:
            return
        added_entity_ids.add(source.entity_id)
        async_add_entities([create_text_entity(source)])

    for source in get_source_entities(hass):
        if autocreate or source.entity_id in selected_entity_ids:
            add_source(source)

    if not autocreate:
        return

    def async_source_added(event):
        """Create an exclusion control when a thermostat appears later."""

        source = er.async_get(hass).async_get(event.data["entity_id"])
        if (
            source is None
            or source.platform != "better_thermostat"
            or source.domain != "climate"
            or source.disabled_by is not None
        ):
            return
        add_source(source)

    entry.async_on_unload(
        async_track_state_added_domain(hass, "climate", async_source_added)
    )
