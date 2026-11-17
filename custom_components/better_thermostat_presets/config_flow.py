import json

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er, selector

from .const import (
    DOMAIN,
    DEFAULT_EXCLUDED_PRESETS,
    DEFAULT_ENTITY_ID_SUFFIX,
    DEFAULT_NAME_MODE,
    DEFAULT_NAME_SUFFIX,
    DEFAULT_NAME_PATTERN,
    DEFAULT_NAME_REPLACEMENT,
    DEFAULT_AUTOCREATE,
    NAME_MODE_SUFFIX,
    NAME_MODE_REGEX,
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

def _normalize_excluded_presets(value):
    """Normalize excluded preset values into lowercase strings."""

    if value is None:
        return []

    if isinstance(value, str):
        value = value.split(",")

    normalized = []
    for item in value:
        if item is None:
            continue
        normalized.extend(
            part.strip().lower()
            for part in str(item).split(",")
            if part.strip()
        )

    return normalized


def _normalize_entity_excluded_presets(value):
    """Normalize per-entity excluded preset overrides."""

    if not value:
        return {}

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}

    normalized = {}
    if isinstance(value, dict):
        for entity_id, presets in value.items():
            normalized[str(entity_id)] = _normalize_excluded_presets(presets)

    return normalized


def get_available_entity_options(hass):
    """Return Better Thermostat climate entities for the manual selector."""

    registry = er.async_get(hass)
    options = []
    for entity in registry.entities.values():
        if (
            entity.platform != "better_thermostat"
            or entity.domain != "climate"
            or entity.disabled_by is not None
        ):
            continue

        state = hass.states.get(entity.entity_id)
        friendly_name = (
            state.attributes.get("friendly_name") if state is not None else None
        )
        name = friendly_name or entity.name or entity.original_name or entity.entity_id
        options.append({"label": name, "value": entity.entity_id})

    return sorted(options, key=lambda option: option["label"].casefold())


def get_schema(defaults, entity_options):
    """Build the shared integration options schema."""

    mode = defaults.get(CONF_NAME_MODE, DEFAULT_NAME_MODE)
    if mode == "prefix":
        mode = NAME_MODE_SUFFIX
    fields = {
        vol.Required(
            CONF_EXCLUDED_PRESETS,
            default=", ".join(
                defaults[CONF_EXCLUDED_PRESETS]
            ),
        ): str,
        vol.Required(
            CONF_ENTITY_ID_SUFFIX,
            default=defaults[CONF_ENTITY_ID_SUFFIX],
        ): str,
        vol.Required(
            CONF_NAME_MODE,
            default=mode,
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[NAME_MODE_SUFFIX, NAME_MODE_REGEX],
                translation_key="name_mode",
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            CONF_AUTOCREATE,
            default=defaults.get(CONF_AUTOCREATE, DEFAULT_AUTOCREATE),
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_SELECTED_ENTITIES,
            default=defaults.get(CONF_SELECTED_ENTITIES, []),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=entity_options,
                multiple=True,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }

    return vol.Schema(fields)


def get_naming_schema(defaults, mode):
    """Build the schema for the selected naming mode."""

    if mode == NAME_MODE_REGEX:
        return vol.Schema({
            vol.Optional(
                CONF_NAME_PATTERN,
                default=defaults.get(CONF_NAME_PATTERN, DEFAULT_NAME_PATTERN),
            ): str,
            vol.Optional(
                CONF_NAME_REPLACEMENT,
                default=defaults.get(
                    CONF_NAME_REPLACEMENT,
                    DEFAULT_NAME_REPLACEMENT,
                ),
            ): str,
        })

    return vol.Schema({
        vol.Optional(
            CONF_NAME_SUFFIX,
            default=defaults.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX),
        ): str,
    })


def parse_options(user_input, defaults=None):
    """Normalize configuration options."""

    defaults = defaults or {}
    excluded = _normalize_excluded_presets(
        user_input.get(
            CONF_EXCLUDED_PRESETS,
            defaults.get(CONF_EXCLUDED_PRESETS, DEFAULT_EXCLUDED_PRESETS),
        )
    )
    entity_excluded = _normalize_entity_excluded_presets(
        user_input.get(
            CONF_ENTITY_EXCLUDED_PRESETS,
            defaults.get(CONF_ENTITY_EXCLUDED_PRESETS, {}),
        )
    )

    mode = user_input.get(
        CONF_NAME_MODE,
        defaults.get(CONF_NAME_MODE, DEFAULT_NAME_MODE),
    )
    if mode == "prefix":
        mode = NAME_MODE_SUFFIX
    selected_entities = user_input.get(
        CONF_SELECTED_ENTITIES,
        defaults.get(CONF_SELECTED_ENTITIES, []),
    )
    if isinstance(selected_entities, str):
        selected_entities = [selected_entities] if selected_entities else []
    parsed = {
        CONF_EXCLUDED_PRESETS: excluded,
        CONF_ENTITY_EXCLUDED_PRESETS: entity_excluded,
        CONF_ENTITY_ID_SUFFIX: user_input.get(
            CONF_ENTITY_ID_SUFFIX,
            defaults.get(CONF_ENTITY_ID_SUFFIX, DEFAULT_ENTITY_ID_SUFFIX),
        ).strip(),
        CONF_NAME_MODE: mode,
        CONF_AUTOCREATE: user_input.get(
            CONF_AUTOCREATE,
            defaults.get(CONF_AUTOCREATE, DEFAULT_AUTOCREATE),
        ),
        CONF_SELECTED_ENTITIES: list(selected_entities),
        CONF_NAME_PATTERN: str(
            user_input.get(
                CONF_NAME_PATTERN,
                defaults.get(CONF_NAME_PATTERN, DEFAULT_NAME_PATTERN),
            )
        ).strip(),
        CONF_NAME_REPLACEMENT: str(
            user_input.get(
                CONF_NAME_REPLACEMENT,
                defaults.get(
                    CONF_NAME_REPLACEMENT,
                    DEFAULT_NAME_REPLACEMENT,
                ),
            )
        ).strip(),
        CONF_NAME_SUFFIX: str(
            user_input.get(
                CONF_NAME_SUFFIX,
                defaults.get(CONF_NAME_SUFFIX, DEFAULT_NAME_SUFFIX),
            )
        ).strip(),
    }

    return parsed


def get_default_data():
    """Return the default config entry data for a newly installed integration."""

    return {
        CONF_EXCLUDED_PRESETS: DEFAULT_EXCLUDED_PRESETS,
        CONF_ENTITY_EXCLUDED_PRESETS: {},
        CONF_ENTITY_ID_SUFFIX: DEFAULT_ENTITY_ID_SUFFIX,
        CONF_AUTOCREATE: DEFAULT_AUTOCREATE,
        CONF_SELECTED_ENTITIES: [],
        CONF_NAME_MODE: DEFAULT_NAME_MODE,
        CONF_NAME_SUFFIX: DEFAULT_NAME_SUFFIX,
        CONF_NAME_PATTERN: DEFAULT_NAME_PATTERN,
        CONF_NAME_REPLACEMENT: DEFAULT_NAME_REPLACEMENT,
    }


class BetterThermostatPresetsConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle integration setup."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the integration entry using defaults."""

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="Better Thermostat Presets",
            data=get_default_data(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""

        return BetterThermostatPresetsOptionsFlow()


class BetterThermostatPresetsOptionsFlow(
    config_entries.OptionsFlowWithReload,
):
    """Handle integration options."""

    async def async_step_init(self, user_input=None):
        """Manage integration options."""

        current = get_default_data()
        current.update(self.config_entry.data)
        current.update(self.config_entry.options)
        current[CONF_EXCLUDED_PRESETS] = _normalize_excluded_presets(
            current.get(CONF_EXCLUDED_PRESETS)
        )
        current[CONF_ENTITY_EXCLUDED_PRESETS] = (
            _normalize_entity_excluded_presets(
                current.get(CONF_ENTITY_EXCLUDED_PRESETS)
            )
        )
        current.setdefault(CONF_AUTOCREATE, DEFAULT_AUTOCREATE)

        if user_input is not None:
            self._pending_options = parse_options(user_input, current)
            return await self.async_step_naming()

        return self.async_show_form(
            step_id="init",
            data_schema=get_schema(
                current,
                get_available_entity_options(self.hass),
            ),
        )

    async def async_step_naming(self, user_input=None):
        """Configure the suffix or regex selected in the previous step."""

        current = getattr(self, "_pending_options", None)
        if current is None:
            current = get_default_data()
            current.update(self.config_entry.data)
            current.update(self.config_entry.options)
            if current.get(CONF_NAME_MODE) == "prefix":
                current[CONF_NAME_MODE] = NAME_MODE_SUFFIX

        mode = current.get(CONF_NAME_MODE, DEFAULT_NAME_MODE)
        if user_input is not None:
            current.update(user_input)
            return self.async_create_entry(data=parse_options(current, current))

        return self.async_show_form(
            step_id="naming",
            data_schema=get_naming_schema(current, mode),
        )
