DOMAIN = "better_thermostat_presets"

DEFAULT_EXCLUDED_PRESETS = ["boost", "none"]
DEFAULT_ENTITY_ID_SUFFIX = "heating_preset"
LEGACY_DEFAULT_ENTITY_ID_SUFFIX = "heizpreset"
DEFAULT_NAME_SUFFIX = "heating preset"
LEGACY_DEFAULT_NAME_SUFFIX = "Heizpreset"
DEFAULT_NAME_MODE = "suffix"
DEFAULT_NAME_PATTERN = ""
DEFAULT_NAME_REPLACEMENT = ""
DEFAULT_AUTOCREATE = False

CONF_EXCLUDED_PRESETS = "excluded_presets"
CONF_ENTITY_EXCLUDED_PRESETS = "entity_excluded_presets"
CONF_ENTITY_ID_SUFFIX = "entity_id_suffix"
CONF_AUTOCREATE = "autocreate"
CONF_SELECTED_ENTITIES = "selected_entities"
CONF_NAME_SUFFIX = "name_suffix"
CONF_NAME_MODE = "name_mode"
CONF_NAME_PATTERN = "name_pattern"
CONF_NAME_REPLACEMENT = "name_replacement"

NAME_MODE_SUFFIX = "suffix"
NAME_MODE_REGEX = "regex"

PLATFORMS = ["select", "text"]
