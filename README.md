# Better Thermostat Presets

A Home Assistant custom integration that creates preset selectors for Better Thermostat climate entities. It allows users to select a preset through a dedicated entity instead of changing the original thermostat state manually.

## Project attribution

The initial repository scaffold and first commit were generated with ChatGPT. Subsequent implementation work, refinements and maintenance were performed by GitHub Copilot.

## Features

- Automatic discovery of Better Thermostat climate entities.
- Dynamic preset options based on the source thermostat state.
- Exclusion of presets such as `boost` or `none`.
- Configurable entity ID suffix.
- Configurable display name suffix.
- Settings support via the Home Assistant config flow and options flow.
- Translation files for German, English and French.

## How it works

The integration searches the entity registry for climate entities coming from the `better_thermostat` platform. For each matching entity, it creates a `select` entity that mirrors the available preset modes and reflects the current preset state.

When a user selects a new preset in Home Assistant, the integration calls the standard climate service:

- `climate.set_preset_mode`

This keeps the preset selector in sync with the underlying Better Thermostat entity without duplicating the thermostat logic itself.

## Installation

Copy the directory:

`custom_components/better_thermostat_presets`

into your Home Assistant configuration directory and restart Home Assistant.

Then add the integration via:

Settings > Devices & Services > Add Integration

Search for `Better Thermostat Presets`.

## Configuration

The integration supports the following values:

| Option | Default |
|---|---|
| Excluded presets | `boost, none` |
| Entity ID suffix | `heizpreset` |
| Display name suffix | `Heizpreset` |

The excluded presets are normalized to lowercase and filtered from the select options.

## Project structure

- `__init__.py` initializes the integration and loads the `select` platform.
- `select.py` contains the selector entity and logic for reading and setting presets.
- `config_flow.py` defines the UI flow for initial setup and options changes.
- `const.py` stores defaults and platform metadata.
- `translations/*.json` contains localized labels.

## Development and testing

The repository includes a minimal unit-test suite under `tests/` that validates the normalization logic and core selector behavior without requiring a full Home Assistant runtime.

Run the tests with:

```bash
python3 -m unittest discover -s tests -v
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Notes

This project is intentionally lightweight and depends on the Better Thermostat entity state model. It does not implement its own thermostat logic; it wraps and exposes the preset system already provided by Better Thermostat.
