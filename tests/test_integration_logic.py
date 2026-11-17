import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "custom_components" / "better_thermostat_presets"


def install_runtime_stubs():
    """Provide minimal Home Assistant / voluptuous stubs for import-time tests."""

    homeassistant = types.ModuleType("homeassistant")
    homeassistant.__path__ = []

    components = types.ModuleType("homeassistant.components")
    components.__path__ = []
    select_mod = types.ModuleType("homeassistant.components.select")

    class SelectEntity:
        def __init__(self):
            self.hass = None

    select_mod.SelectEntity = SelectEntity

    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        pass

    class ConfigFlow:
        VERSION = 1

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__()

        def __init__(self, *args, **kwargs):
            self.data = None

        async def async_set_unique_id(self, _unique_id):
            return None

        def _abort_if_unique_id_configured(self):
            return None

        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

        def async_create_entry(self, **kwargs):
            return {"type": "create_entry", **kwargs}

    class OptionsFlow:
        @property
        def config_entry(self):
            return self._config_entry

        def __init__(self, *args, **kwargs):
            self._config_entry = kwargs.get("config_entry")

        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

        def async_create_entry(self, **kwargs):
            return {"type": "create_entry", **kwargs}

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigFlow = ConfigFlow
    config_entries.OptionsFlow = OptionsFlow

    core = types.ModuleType("homeassistant.core")

    class HomeAssistant:
        pass

    core.HomeAssistant = HomeAssistant
    core.callback = lambda func: func

    helpers = types.ModuleType("homeassistant.helpers")
    helpers.__path__ = []
    entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")
    entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")

    class AddEntitiesCallback:
        pass

    entity_platform.AddEntitiesCallback = AddEntitiesCallback

    class Registry:
        def __init__(self):
            self.entities = {}

    entity_registry.async_get = lambda hass: Registry()

    homeassistant.components = components
    homeassistant.config_entries = config_entries
    homeassistant.core = core
    homeassistant.helpers = helpers
    helpers.entity_registry = entity_registry
    helpers.entity_platform = entity_platform
    components.select = select_mod

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.select"] = select_mod
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.entity_registry"] = entity_registry
    sys.modules["homeassistant.helpers.entity_platform"] = entity_platform

    voluptuous = types.ModuleType("voluptuous")

    class Schema:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class Required:
        def __init__(self, key, default=None):
            self.key = key
            self.default = default

    voluptuous.Schema = Schema
    voluptuous.Required = Required
    sys.modules["voluptuous"] = voluptuous


def load_module(name, file_path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_package_modules():
    install_runtime_stubs()

    package_name = "better_thermostat_presets"
    package_module = types.ModuleType(package_name)
    package_module.__path__ = [str(PACKAGE_DIR)]
    sys.modules[package_name] = package_module

    const = load_module(f"{package_name}.const", PACKAGE_DIR / "const.py")
    select = load_module(f"{package_name}.select", PACKAGE_DIR / "select.py")
    flow = load_module(f"{package_name}.config_flow", PACKAGE_DIR / "config_flow.py")

    return const, select, flow


class BetterThermostatPresetLogicTests(unittest.TestCase):
    def setUp(self):
        self.const, self.select_module, self.flow_module = load_package_modules()

    def test_slugify_replaces_invalid_chars(self):
        self.assertEqual(self.select_module.slugify("My Preset!"), "my_preset")
        self.assertEqual(self.select_module.slugify("  Zimmer 1  "), "zimmer_1")
        self.assertEqual(self.select_module.slugify("eco"), "eco")

    def test_parse_options_normalizes_excluded_presets_and_strings(self):
        parsed = self.flow_module.parse_options({
            self.const.CONF_EXCLUDED_PRESETS: " boost, none, eco ",
            self.const.CONF_ENTITY_ID_SUFFIX: "  Heizpreset  ",
            self.const.CONF_NAME_SUFFIX: "  Heizpreset  ",
            self.const.CONF_NAME_PATTERN: "^(.+)$",
            self.const.CONF_NAME_REPLACEMENT: "\\1: Heizpreset",
        })

        self.assertEqual(parsed["excluded_presets"], ["boost", "none", "eco"])
        self.assertEqual(parsed["entity_id_suffix"], "Heizpreset")
        self.assertEqual(parsed["name_suffix"], "Heizpreset")
        self.assertEqual(parsed["name_pattern"], "^(.+)$")
        self.assertEqual(parsed["name_replacement"], "\\1: Heizpreset")

    def test_select_entity_uses_regex_pattern_for_friendly_name(self):
        entity = self.select_module.BetterThermostatPresetSelect(
            source_entity_id="climate.room",
            source_unique_id="abc123",
            source_name="Wohnzimmer",
            excluded_presets={"boost", "none"},
            entity_id_suffix="heizpreset",
            name_suffix="Heizpreset",
            name_pattern=r"^(.*)$",
            name_replacement=r"\1: Nachtmodus",
        )

        self.assertEqual(entity._attr_name, "Wohnzimmer: Nachtmodus")

    def test_select_entity_exposes_current_and_available_presets(self):
        source_state = types.SimpleNamespace(
            state="heat",
            attributes={
                "preset_mode": "eco",
                "preset_modes": ["eco", "boost", "none"],
            },
        )

        entity = self.select_module.BetterThermostatPresetSelect(
            source_entity_id="climate.room",
            source_unique_id="abc123",
            source_name="Wohnzimmer",
            excluded_presets={"boost", "none"},
            entity_id_suffix="heizpreset",
            name_suffix="Heizpreset",
        )
        entity.hass = types.SimpleNamespace(states={"climate.room": source_state})

        self.assertTrue(entity.available)
        self.assertEqual(entity.current_option, "eco")
        self.assertEqual(entity.options, ["eco"])

    def test_get_source_entities_only_returns_valid_better_thermostat_climate_entries(self):
        valid = types.SimpleNamespace(
            entity_id="climate.living_room",
            platform="better_thermostat",
            domain="climate",
            disabled_by=None,
            name="Wohnzimmer",
            unique_id="living-room",
        )
        invalid_disabled = types.SimpleNamespace(
            entity_id="climate.disabled",
            platform="better_thermostat",
            domain="climate",
            disabled_by="user",
            name="Disabled",
            unique_id="disabled",
        )
        invalid_platform = types.SimpleNamespace(
            entity_id="sensor.temp",
            platform="mqtt",
            domain="sensor",
            disabled_by=None,
            name="Temp",
            unique_id="sensor-temp",
        )
        invalid_domain = types.SimpleNamespace(
            entity_id="climate.other",
            platform="better_thermostat",
            domain="switch",
            disabled_by=None,
            name="Other",
            unique_id="other",
        )

        fake_registry = types.SimpleNamespace(
            entities={
                "climate.living_room": valid,
                "climate.disabled": invalid_disabled,
                "sensor.temp": invalid_platform,
                "climate.other": invalid_domain,
            }
        )
        self.select_module.er.async_get = lambda hass: fake_registry

        result = self.select_module.get_source_entities({})

        self.assertEqual(result, [valid])

    def test_async_setup_entry_creates_select_entities_for_matching_sources(self):
        source = types.SimpleNamespace(
            entity_id="climate.living_room",
            unique_id="abc123",
            name="Wohnzimmer",
            original_name="Wohnzimmer",
            platform="better_thermostat",
            domain="climate",
            disabled_by=None,
        )
        fake_registry = types.SimpleNamespace(entities={source.entity_id: source})
        self.select_module.er.async_get = lambda hass: fake_registry

        entry = types.SimpleNamespace(
            data={
                self.const.CONF_EXCLUDED_PRESETS: ["boost", "none"],
                self.const.CONF_ENTITY_ID_SUFFIX: "heizpreset",
                self.const.CONF_NAME_SUFFIX: "Heizpreset",
            }
        )
        added = []

        asyncio.run(
            self.select_module.async_setup_entry(
                hass={},
                entry=entry,
                async_add_entities=lambda entities: added.extend(entities),
            )
        )

        self.assertEqual(len(added), 1)
        self.assertEqual(added[0].source_entity_id, "climate.living_room")
        self.assertEqual(added[0]._attr_name, "Wohnzimmer: Heizpreset")

    def test_async_select_option_ignores_invalid_values_and_calls_service_for_valid_ones(self):
        source_state = types.SimpleNamespace(
            state="heat",
            attributes={
                "preset_mode": "eco",
                "preset_modes": ["eco", "boost", "none"],
            },
        )
        entity = self.select_module.BetterThermostatPresetSelect(
            source_entity_id="climate.room",
            source_unique_id="abc123",
            source_name="Wohnzimmer",
            excluded_presets={"boost", "none"},
            entity_id_suffix="heizpreset",
            name_suffix="Heizpreset",
        )
        calls = []

        async def fake_async_call(domain, service, data, blocking=True):
            calls.append((domain, service, data, blocking))

        entity.hass = types.SimpleNamespace(
            states={"climate.room": source_state},
            services=types.SimpleNamespace(async_call=fake_async_call),
        )
        entity.async_write_ha_state = lambda: None

        asyncio.run(entity.async_select_option("away"))
        self.assertEqual(calls, [])

        asyncio.run(entity.async_select_option("eco"))
        self.assertEqual(
            calls,
            [
                (
                    "climate",
                    "set_preset_mode",
                    {"entity_id": "climate.room", "preset_mode": "eco"},
                    True,
                )
            ],
        )

    def test_config_flow_uses_default_values_in_form(self):
        flow = self.flow_module.BetterThermostatPresetsConfigFlow()
        result = flow.async_show_form(step_id="user", data_schema=None)

        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "user")

    def test_options_flow_uses_existing_entry_data(self):
        config_entry = types.SimpleNamespace(
            data={
                self.const.CONF_EXCLUDED_PRESETS: ["boost", "none"],
                self.const.CONF_ENTITY_ID_SUFFIX: "heizpreset",
                self.const.CONF_NAME_SUFFIX: "Heizpreset",
            }
        )

        flow = self.flow_module.BetterThermostatPresetsOptionsFlow(config_entry)
        self.assertIs(flow.config_entry, config_entry)
        result = flow.async_show_form(step_id="init", data_schema=None)

        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "init")


if __name__ == "__main__":
    unittest.main()
