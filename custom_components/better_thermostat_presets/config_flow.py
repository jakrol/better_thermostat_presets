import json

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
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

ENTITY_EXCLUSIONS_FIELD_PREFIX = "Excluded presets for "


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


def get_entity_exclusion_fields(hass):
    """Map readable options fields to Better Thermostat entity IDs."""

    registry = er.async_get(hass)
    fields = {}
    for entity in registry.entities.values():
        if (
            entity.platform != "better_thermostat"
            or entity.domain != "climate"
            or entity.disabled_by is not None
        ):
            continue

        name = entity.name or entity.original_name or entity.entity_id
        field = f"{ENTITY_EXCLUSIONS_FIELD_PREFIX}{name} [{entity.entity_id}]"
        fields[field] = entity.entity_id

    return fields


def get_schema(defaults, entity_fields=None):
    """Build the integration options schema."""

    mode = defaults.get(CONF_NAME_MODE, DEFAULT_NAME_MODE)
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
        ): vol.In([NAME_MODE_PREFIX, NAME_MODE_REGEX]),
    }

    entity_excluded = defaults.get(CONF_ENTITY_EXCLUDED_PRESETS, {})
    for field, entity_id in (entity_fields or {}).items():
        fields[vol.Optional(
            field,
            default=", ".join(entity_excluded.get(entity_id, [])),
        )] = str

    if mode == NAME_MODE_REGEX:
        fields.update({
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
    else:
        fields.update({
            vol.Optional(
                CONF_NAME_SUFFIX,
                default=defaults[CONF_NAME_SUFFIX],
            ): str,
        })

    return vol.Schema(fields)


def parse_options(user_input, entity_fields=None):
    """Normalize configuration options."""

    excluded = _normalize_excluded_presets(
        user_input.get(CONF_EXCLUDED_PRESETS, DEFAULT_EXCLUDED_PRESETS)
    )
    entity_excluded = _normalize_entity_excluded_presets(
        user_input.get(CONF_ENTITY_EXCLUDED_PRESETS, {})
    )
    for field, entity_id in (entity_fields or {}).items():
        if field in user_input:
            presets = _normalize_excluded_presets(user_input[field])
            if presets:
                entity_excluded[entity_id] = presets
            else:
                entity_excluded.pop(entity_id, None)

    mode = user_input.get(CONF_NAME_MODE, DEFAULT_NAME_MODE)
    parsed = {
        CONF_EXCLUDED_PRESETS: excluded,
        CONF_ENTITY_EXCLUDED_PRESETS: entity_excluded,
        CONF_ENTITY_ID_SUFFIX: user_input[
            CONF_ENTITY_ID_SUFFIX
        ].strip(),
        CONF_NAME_MODE: mode,
        CONF_NAME_PATTERN: str(
            user_input.get(CONF_NAME_PATTERN, DEFAULT_NAME_PATTERN)
        ).strip(),
        CONF_NAME_REPLACEMENT: str(
            user_input.get(CONF_NAME_REPLACEMENT, DEFAULT_NAME_REPLACEMENT)
        ).strip(),
    }

    if mode == NAME_MODE_REGEX:
        parsed[CONF_NAME_SUFFIX] = user_input.get(
            CONF_NAME_SUFFIX,
            DEFAULT_NAME_SUFFIX,
        ).strip()
    else:
        parsed[CONF_NAME_SUFFIX] = user_input.get(
            CONF_NAME_SUFFIX,
            DEFAULT_NAME_SUFFIX,
        ).strip()

    return parsed


def get_default_data():
    """Return the default config entry data for a newly installed integration."""

    return {
        CONF_EXCLUDED_PRESETS: DEFAULT_EXCLUDED_PRESETS,
        CONF_ENTITY_EXCLUDED_PRESETS: {},
        CONF_ENTITY_ID_SUFFIX: DEFAULT_ENTITY_ID_SUFFIX,
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
        entity_fields = get_entity_exclusion_fields(self.hass)

        if user_input is not None:
            user_input = dict(user_input)
            entity_ids_in_form = set(entity_fields.values())
            user_input[CONF_ENTITY_EXCLUDED_PRESETS] = {
                entity_id: presets
                for entity_id, presets in current[
                    CONF_ENTITY_EXCLUDED_PRESETS
                ].items()
                if entity_id not in entity_ids_in_form
            }
            return self.async_create_entry(
                data=parse_options(user_input, entity_fields),
            )

        return self.async_show_form(
            step_id="init",
            data_schema=get_schema(current, entity_fields),
        )
