import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

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
    CONF_ENTITY_ID_SUFFIX,
    CONF_NAME_SUFFIX,
    CONF_NAME_MODE,
    CONF_NAME_PATTERN,
    CONF_NAME_REPLACEMENT,
)


def get_schema(defaults):
    """Build the configuration schema."""

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


def parse_options(user_input):
    """Normalize configuration options."""

    excluded = [
        item.strip().lower()
        for item in user_input[CONF_EXCLUDED_PRESETS].split(",")
        if item.strip()
    ]

    mode = user_input.get(CONF_NAME_MODE, DEFAULT_NAME_MODE)
    parsed = {
        CONF_EXCLUDED_PRESETS: excluded,
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


class BetterThermostatPresetsConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle integration setup."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle initial setup."""

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        defaults = {
            CONF_EXCLUDED_PRESETS: DEFAULT_EXCLUDED_PRESETS,
            CONF_ENTITY_ID_SUFFIX: DEFAULT_ENTITY_ID_SUFFIX,
            CONF_NAME_MODE: DEFAULT_NAME_MODE,
            CONF_NAME_SUFFIX: DEFAULT_NAME_SUFFIX,
            CONF_NAME_PATTERN: DEFAULT_NAME_PATTERN,
            CONF_NAME_REPLACEMENT: DEFAULT_NAME_REPLACEMENT,
        }

        if user_input is not None:
            return self.async_create_entry(
                title="Better Thermostat Presets",
                data=parse_options(user_input),
            )

        return self.async_show_form(
            step_id="user",
            data_schema=get_schema(defaults),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""

        return BetterThermostatPresetsOptionsFlow(config_entry)


class BetterThermostatPresetsOptionsFlow(
    config_entries.OptionsFlow,
):
    """Handle integration options."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage integration options."""

        current = {
            CONF_EXCLUDED_PRESETS: self.config_entry.data.get(
                CONF_EXCLUDED_PRESETS,
                DEFAULT_EXCLUDED_PRESETS,
            ),
            CONF_ENTITY_ID_SUFFIX: self.config_entry.data.get(
                CONF_ENTITY_ID_SUFFIX,
                DEFAULT_ENTITY_ID_SUFFIX,
            ),
            CONF_NAME_MODE: self.config_entry.data.get(
                CONF_NAME_MODE,
                DEFAULT_NAME_MODE,
            ),
            CONF_NAME_SUFFIX: self.config_entry.data.get(
                CONF_NAME_SUFFIX,
                DEFAULT_NAME_SUFFIX,
            ),
            CONF_NAME_PATTERN: self.config_entry.data.get(
                CONF_NAME_PATTERN,
                DEFAULT_NAME_PATTERN,
            ),
            CONF_NAME_REPLACEMENT: self.config_entry.data.get(
                CONF_NAME_REPLACEMENT,
                DEFAULT_NAME_REPLACEMENT,
            ),
        }

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=parse_options(user_input),
            )

        return self.async_show_form(
            step_id="init",
            data_schema=get_schema(current),
        )
