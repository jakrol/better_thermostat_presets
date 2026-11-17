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
    text_mod = types.ModuleType("homeassistant.components.text")

    class SelectEntity:
        def __init__(self):
            self.hass = None

        @property
        def name(self):
            return self._attr_name

        @property
        def unique_id(self):
            return self._attr_unique_id

        async def async_added_to_hass(self):
            return None

        def async_on_remove(self, callback):
            return None

    select_mod.SelectEntity = SelectEntity

    class TextEntity:
        @property
        def native_value(self):
            return self._attr_native_value

        async def async_added_to_hass(self):
            return None

    class TextMode:
        TEXT = "text"

    text_mod.TextEntity = TextEntity
    text_mod.TextMode = TextMode

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

    class OptionsFlowWithReload(OptionsFlow):
        pass

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigFlow = ConfigFlow
    config_entries.OptionsFlow = OptionsFlow
    config_entries.OptionsFlowWithReload = OptionsFlowWithReload

    core = types.ModuleType("homeassistant.core")

    class HomeAssistant:
        pass

    core.HomeAssistant = HomeAssistant
    core.callback = lambda func: func
    const_mod = types.ModuleType("homeassistant.const")

    class EntityCategory:
        CONFIG = "config"

    const_mod.EntityCategory = EntityCategory

    helpers = types.ModuleType("homeassistant.helpers")
    helpers.__path__ = []
    entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")
    device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
    event = types.ModuleType("homeassistant.helpers.event")
    dispatcher = types.ModuleType("homeassistant.helpers.dispatcher")
    restore_state = types.ModuleType("homeassistant.helpers.restore_state")
    selector = types.ModuleType("homeassistant.helpers.selector")

    added_domain_listeners = []
    dispatcher_listeners = {}

    def async_track_state_added_domain(hass, domain, callback):
        added_domain_listeners.append((hass, domain, callback))
        return lambda: None

    def async_dispatcher_connect(hass, signal, callback):
        dispatcher_listeners.setdefault(signal, []).append(callback)

        def disconnect():
            dispatcher_listeners[signal].remove(callback)

        return disconnect

    def async_dispatcher_send(hass, signal, *args):
        for callback in dispatcher_listeners.get(signal, []):
            callback(*args)

    event.async_track_state_added_domain = async_track_state_added_domain
    event.added_domain_listeners = added_domain_listeners
    dispatcher.async_dispatcher_connect = async_dispatcher_connect
    dispatcher.async_dispatcher_send = async_dispatcher_send

    class RestoreEntity:
        async def async_added_to_hass(self):
            return None

        async def async_get_last_state(self):
            return None

    restore_state.RestoreEntity = RestoreEntity

    class SelectSelectorMode:
        DROPDOWN = "dropdown"

    class SelectSelectorConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class SelectSelector:
        def __init__(self, config):
            self.config = config

    class BooleanSelector:
        pass

    selector.SelectSelectorMode = SelectSelectorMode
    selector.SelectSelectorConfig = SelectSelectorConfig
    selector.SelectSelector = SelectSelector
    selector.BooleanSelector = BooleanSelector

    class AddEntitiesCallback:
        pass

    entity_platform.AddEntitiesCallback = AddEntitiesCallback

    class Registry:
        def __init__(self):
            self.entities = {}

    class DeviceRegistry:
        def __init__(self):
            self.devices = {}

        def async_get(self, device_id):
            return self.devices.get(device_id)

    entity_registry.async_get = lambda hass: Registry()
    device_registry.async_get = lambda hass: DeviceRegistry()

    homeassistant.components = components
    homeassistant.config_entries = config_entries
    homeassistant.core = core
    homeassistant.helpers = helpers
    helpers.entity_registry = entity_registry
    helpers.device_registry = device_registry
    helpers.entity_platform = entity_platform
    helpers.event = event
    helpers.dispatcher = dispatcher
    helpers.restore_state = restore_state
    helpers.selector = selector
    components.select = select_mod
    components.text = text_mod

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.select"] = select_mod
    sys.modules["homeassistant.components.text"] = text_mod
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.const"] = const_mod
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.entity_registry"] = entity_registry
    sys.modules["homeassistant.helpers.device_registry"] = device_registry
    sys.modules["homeassistant.helpers.entity_platform"] = entity_platform
    sys.modules["homeassistant.helpers.event"] = event
    sys.modules["homeassistant.helpers.dispatcher"] = dispatcher
    sys.modules["homeassistant.helpers.restore_state"] = restore_state
    sys.modules["homeassistant.helpers.selector"] = selector

    voluptuous = types.ModuleType("voluptuous")

    class Schema:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class Required:
        def __init__(self, key, default=None):
            self.key = key
            self.default = default

    class Optional:
        def __init__(self, key, default=None):
            self.key = key
            self.default = default

    class In:
        def __init__(self, values):
            self.values = values

    voluptuous.Schema = Schema
    voluptuous.Required = Required
    voluptuous.Optional = Optional
    voluptuous.In = In
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
    text = load_module(f"{package_name}.text", PACKAGE_DIR / "text.py")
    flow = load_module(f"{package_name}.config_flow", PACKAGE_DIR / "config_flow.py")

    return const, select, text, flow


class BetterThermostatPresetLogicTests(unittest.TestCase):
    def setUp(self):
        self.const, self.select_module, self.text_module, self.flow_module = load_package_modules()

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

    def test_parse_options_supports_entity_specific_excluded_presets(self):
        parsed = self.flow_module.parse_options({
            self.const.CONF_EXCLUDED_PRESETS: "boost, none",
            self.const.CONF_ENTITY_EXCLUDED_PRESETS: '{"climate.living_room": ["eco"], "climate.kitchen": "away, boost"}',
            self.const.CONF_ENTITY_ID_SUFFIX: "heizpreset",
            self.const.CONF_NAME_SUFFIX: "Heizpreset",
        })

        self.assertEqual(parsed["excluded_presets"], ["boost", "none"])
        self.assertEqual(
            parsed["entity_excluded_presets"],
            {"climate.living_room": ["eco"], "climate.kitchen": ["away", "boost"]},
        )

    def test_parse_options_reads_selected_entities_and_autocreate(self):
        parsed = self.flow_module.parse_options(
            {
                self.const.CONF_EXCLUDED_PRESETS: "boost, none",
                self.const.CONF_ENTITY_ID_SUFFIX: "heizpreset",
                self.const.CONF_NAME_MODE: "suffix",
                self.const.CONF_AUTOCREATE: False,
                self.const.CONF_SELECTED_ENTITIES: ["climate.living_room"],
            },
        )

        self.assertFalse(parsed[self.const.CONF_AUTOCREATE])
        self.assertEqual(
            parsed[self.const.CONF_SELECTED_ENTITIES],
            ["climate.living_room"],
        )

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
            name_mode="regex",
        )

        self.assertEqual(entity._attr_name, "Wohnzimmer: Nachtmodus")

    def test_select_entity_object_id_removes_climate_domain_from_name(self):
        entity = self.select_module.BetterThermostatPresetSelect(
            source_entity_id="climate.eg_bad_heizung",
            source_unique_id="room-1",
            source_name="EG: Bad Heizung",
            excluded_presets=set(),
            entity_id_suffix="heizpreset",
            name_suffix="Heizpreset",
        )

        self.assertEqual(entity._attr_name, "EG: Bad Heizung: Heizpreset")
        self.assertEqual(entity.suggested_object_id, "eg_bad_heizung_heizpreset")

    def test_source_state_friendly_name_is_used_instead_of_entity_id(self):
        source = types.SimpleNamespace(
            entity_id="climate.dg_schlafzimmer_heizung",
            name=None,
            original_name=None,
        )
        hass = types.SimpleNamespace(
            states=types.SimpleNamespace(
                get=lambda entity_id: types.SimpleNamespace(
                    attributes={"friendly_name": "DG: Schlafzimmer: Heizung"}
                )
            )
        )

        self.assertEqual(
            self.select_module.get_source_friendly_name(hass, source),
            "DG: Schlafzimmer: Heizung",
        )

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

    def test_select_entity_links_to_better_thermostat_device(self):
        device_info = {"identifiers": {("better_thermostat", "thermostat-1")}}
        entity = self.select_module.BetterThermostatPresetSelect(
            source_entity_id="climate.room",
            source_unique_id="abc123",
            source_name="Wohnzimmer",
            excluded_presets={"boost", "none"},
            entity_id_suffix="heizpreset",
            name_suffix="Heizpreset",
            source_device_info=device_info,
        )

        self.assertEqual(entity._attr_device_info, device_info)

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
            },
            async_on_unload=lambda callback: None,
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

    def test_async_setup_entry_applies_entity_specific_exclusions(self):
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
                self.const.CONF_EXCLUDED_PRESETS: ["none"],
                self.const.CONF_ENTITY_EXCLUDED_PRESETS: {"climate.living_room": ["boost", "eco"]},
                self.const.CONF_ENTITY_ID_SUFFIX: "heizpreset",
                self.const.CONF_NAME_SUFFIX: "Heizpreset",
            },
            async_on_unload=lambda callback: None,
        )
        added = []

        asyncio.run(
            self.select_module.async_setup_entry(
                hass={},
                entry=entry,
                async_add_entities=lambda entities: added.extend(entities),
            )
        )

        self.assertEqual(added[0].excluded_presets, {"none", "boost", "eco"})

    def test_async_setup_entry_prefers_configure_options_to_entry_defaults(self):
        source = types.SimpleNamespace(
            entity_id="climate.living_room",
            unique_id="abc123",
            name="Living Room",
            original_name="Living Room",
            platform="better_thermostat",
            domain="climate",
            disabled_by=None,
        )
        self.select_module.er.async_get = lambda hass: types.SimpleNamespace(
            entities={source.entity_id: source}
        )
        entry = types.SimpleNamespace(
            data={
                self.const.CONF_EXCLUDED_PRESETS: ["boost"],
                self.const.CONF_ENTITY_ID_SUFFIX: "heizpreset",
                self.const.CONF_NAME_SUFFIX: "Heizpreset",
            },
            options={
                self.const.CONF_EXCLUDED_PRESETS: ["none"],
            },
            async_on_unload=lambda callback: None,
        )
        source_state = types.SimpleNamespace(
            state="heat",
            attributes={"preset_mode": "eco", "preset_modes": ["eco", "boost", "none"]},
        )
        hass = types.SimpleNamespace(
            states=types.SimpleNamespace(get=lambda entity_id: source_state),
        )
        added = []

        asyncio.run(
            self.select_module.async_setup_entry(
                hass=hass,
                entry=entry,
                async_add_entities=lambda entities: added.extend(entities),
            )
        )

        self.assertEqual(added[0].excluded_presets, {"none"})
        added[0].hass = hass
        self.assertEqual(added[0].options, ["eco", "boost"])

    def test_async_setup_entry_creates_only_selected_entities_when_autocreate_off(self):
        sources = [
            types.SimpleNamespace(
                entity_id=f"climate.room_{index}",
                unique_id=f"room-{index}",
                name=f"Room {index}",
                original_name=f"Room {index}",
                platform="better_thermostat",
                domain="climate",
                disabled_by=None,
            )
            for index in (1, 2)
        ]
        self.select_module.er.async_get = lambda hass: types.SimpleNamespace(
            entities={source.entity_id: source for source in sources}
        )
        entry = types.SimpleNamespace(
            data={
                self.const.CONF_AUTOCREATE: False,
                self.const.CONF_SELECTED_ENTITIES: ["climate.room_2"],
                self.const.CONF_ENTITY_ID_SUFFIX: "preset",
                self.const.CONF_NAME_SUFFIX: "Presets",
            },
            async_on_unload=lambda callback: None,
        )
        added = []

        asyncio.run(
            self.select_module.async_setup_entry(
                hass={},
                entry=entry,
                async_add_entities=lambda entities: added.extend(entities),
            )
        )

        self.assertEqual([entity.source_entity_id for entity in added], ["climate.room_2"])

    def test_async_setup_entry_migrates_only_legacy_generated_entity_id(self):
        source = types.SimpleNamespace(
            entity_id="climate.eg_bad_heizung",
            unique_id="room-1",
            name="climate.eg_bad_heizung",
            original_name="climate.eg_bad_heizung",
            platform="better_thermostat",
            domain="climate",
            disabled_by=None,
        )

        class FakeRegistry:
            def __init__(self):
                self.entities = {source.entity_id: source}
                self.updates = []
                self.lookups = []

            def async_get_entity_id(self, entity_domain, platform, unique_id):
                self.lookups.append((entity_domain, platform, unique_id))
                return "select.climate_eg_bad_heizung_heizpreset"

            def async_update_entity(self, entity_id, **kwargs):
                self.updates.append((entity_id, kwargs))

        registry = FakeRegistry()
        self.select_module.er.async_get = lambda hass: registry
        entry = types.SimpleNamespace(
            data={
                self.const.CONF_AUTOCREATE: True,
                self.const.CONF_ENTITY_ID_SUFFIX: "heizpreset",
                self.const.CONF_NAME_SUFFIX: "Heizpreset",
            },
            async_on_unload=lambda callback: None,
        )
        hass = types.SimpleNamespace(
            data={},
            states=types.SimpleNamespace(get=lambda entity_id: None),
        )

        asyncio.run(
            self.select_module.async_setup_entry(
                hass=hass,
                entry=entry,
                async_add_entities=lambda entities: None,
            )
        )

        self.assertEqual(registry.lookups, [("select", self.const.DOMAIN, "room-1_heizpreset")])
        self.assertEqual(
            registry.updates,
            [
                (
                    "select.climate_eg_bad_heizung_heizpreset",
                    {"new_entity_id": "select.eg_bad_heizung_heizpreset"},
                )
            ],
        )

    def test_autocreate_adds_better_thermostats_that_appear_later(self):
        first = types.SimpleNamespace(
            entity_id="climate.room_1",
            unique_id="room-1",
            name="Room 1",
            original_name="Room 1",
            platform="better_thermostat",
            domain="climate",
            disabled_by=None,
        )
        entities = {first.entity_id: first}

        class FakeRegistry:
            @property
            def entities(self):
                return entities

            def async_get(self, entity_id):
                return entities.get(entity_id)

        registry = FakeRegistry()
        self.select_module.er.async_get = lambda hass: registry
        entry = types.SimpleNamespace(
            data={
                self.const.CONF_AUTOCREATE: True,
                self.const.CONF_ENTITY_ID_SUFFIX: "preset",
                self.const.CONF_NAME_SUFFIX: "Presets",
            },
            async_on_unload=lambda callback: None,
        )
        added = []

        asyncio.run(
            self.select_module.async_setup_entry(
                hass={},
                entry=entry,
                async_add_entities=lambda batch: added.extend(batch),
            )
        )
        event_module = sys.modules["homeassistant.helpers.event"]
        _, domain, listener = event_module.added_domain_listeners[-1]
        self.assertEqual(domain, "climate")

        second = types.SimpleNamespace(
            entity_id="climate.room_2",
            unique_id="room-2",
            name="Room 2",
            original_name="Room 2",
            platform="better_thermostat",
            domain="climate",
            disabled_by=None,
        )
        entities[second.entity_id] = second
        listener(types.SimpleNamespace(data={"entity_id": second.entity_id}))

        self.assertEqual(
            [entity.source_entity_id for entity in added],
            ["climate.room_1", "climate.room_2"],
        )

    def test_exclusion_text_control_changes_selector_options(self):
        source_state = types.SimpleNamespace(
            state="heat",
            attributes={
                "preset_mode": "comfort",
                "preset_modes": ["comfort", "eco", "away", "boost"],
            },
        )
        hass = types.SimpleNamespace(
            states=types.SimpleNamespace(get=lambda entity_id: source_state),
            data={},
        )
        selector = self.select_module.BetterThermostatPresetSelect(
            source_entity_id="climate.room",
            source_unique_id="room-1",
            source_name="Room",
            excluded_presets={"boost"},
            entity_id_suffix="preset",
            name_suffix="Presets",
        )
        selector.hass = hass
        control = self.text_module.BetterThermostatExcludedPresetsText(
            source_entity_id="climate.room",
            source_unique_id="room-1",
            initial_value="",
        )
        control.hass = hass
        control.async_write_ha_state = lambda: None

        asyncio.run(control.async_set_value("away, ECO"))

        self.assertEqual(selector.options, ["comfort"])
        self.assertEqual(
            self.select_module.get_entity_exclusion_store(hass)["climate.room"],
            ["away", "eco"],
        )

    def test_selected_thermostat_gets_exclusion_control(self):
        source = types.SimpleNamespace(
            entity_id="climate.room",
            unique_id="room-1",
            name="Study",
            original_name="Study",
            platform="better_thermostat",
            domain="climate",
            disabled_by=None,
        )

        class FakeRegistry:
            entities = {source.entity_id: source}

            def async_get(self, entity_id):
                return self.entities.get(entity_id)

        self.text_module.er.async_get = lambda hass: FakeRegistry()
        entry = types.SimpleNamespace(
            data={
                self.const.CONF_AUTOCREATE: False,
                self.const.CONF_SELECTED_ENTITIES: [source.entity_id],
                self.const.CONF_ENTITY_EXCLUDED_PRESETS: {
                    source.entity_id: ["away"]
                },
                self.const.CONF_NAME_MODE: "suffix",
                self.const.CONF_NAME_SUFFIX: "Presets",
            },
            async_on_unload=lambda callback: None,
        )
        hass = types.SimpleNamespace(data={}, states=types.SimpleNamespace(get=lambda entity_id: None))
        added = []

        asyncio.run(
            self.text_module.async_setup_entry(
                hass=hass,
                entry=entry,
                async_add_entities=lambda entities: added.extend(entities),
            )
        )

        self.assertEqual(len(added), 1)
        self.assertEqual(added[0].native_value, "away")
        self.assertEqual(added[0]._attr_device_info["name"], "Study: Presets")

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

    def test_config_flow_creates_default_entry_without_form(self):
        flow = self.flow_module.BetterThermostatPresetsConfigFlow()

        result = asyncio.run(flow.async_step_user())

        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["title"], "Better Thermostat Presets")
        self.assertEqual(result["data"][self.const.CONF_EXCLUDED_PRESETS], ["boost", "none"])
        self.assertEqual(result["data"][self.const.CONF_ENTITY_ID_SUFFIX], "heizpreset")
        self.assertEqual(result["data"][self.const.CONF_NAME_MODE], "suffix")
        self.assertTrue(result["data"][self.const.CONF_AUTOCREATE])

    def test_options_flow_uses_existing_entry_data_and_selected_entity_options(self):
        config_entry = types.SimpleNamespace(
            data={
                self.const.CONF_EXCLUDED_PRESETS: ["boost", "none"],
                self.const.CONF_ENTITY_ID_SUFFIX: "heizpreset",
                self.const.CONF_NAME_SUFFIX: "Heizpreset",
            },
            options={},
        )
        source = types.SimpleNamespace(
            entity_id="climate.living_room",
            platform="better_thermostat",
            domain="climate",
            disabled_by=None,
            name="Living Room",
            original_name="Living Room",
        )
        self.flow_module.er.async_get = lambda hass: types.SimpleNamespace(
            entities={source.entity_id: source}
        )

        flow = self.flow_module.BetterThermostatPresetsOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = types.SimpleNamespace(
            states=types.SimpleNamespace(get=lambda entity_id: None),
        )
        result = asyncio.run(flow.async_step_init())

        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "init")
        schema_fields = result["data_schema"].args[0]
        field_names = [field.key for field in schema_fields]
        self.assertIn(self.const.CONF_AUTOCREATE, field_names)
        self.assertIn(self.const.CONF_SELECTED_ENTITIES, field_names)
        entity_field = next(
            field
            for field in schema_fields
            if field.key == self.const.CONF_SELECTED_ENTITIES
        )
        self.assertEqual(
            schema_fields[entity_field].config.kwargs["options"],
            [{"label": "Living Room", "value": "climate.living_room"}],
        )


if __name__ == "__main__":
    unittest.main()
