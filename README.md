# Better Thermostat Presets

A Home Assistant custom integration that creates preset selectors for Better Thermostat climate entities. It allows users to select a preset through a dedicated entity instead of changing the original thermostat state manually.

## Project attribution

The initial repository scaffold and first commit were generated with ChatGPT. Subsequent implementation work, refinements and maintenance were performed by GitHub Copilot.

## Status

This project is currently in active development and is not yet published as a formal release. The repository is intended for installation as a custom Home Assistant integration and may evolve as new features and compatibility fixes are added.

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

### Install via HACS / Home Assistant Marketplace

1. Open Home Assistant.
2. Go to HACS.
3. Open the HACS menu and choose the option to add a custom repository.
4. Add this repository:

   `https://github.com/jakrol/better_thermostat_presets`

5. Select the repository type as a custom integration.
6. Install the integration from HACS.
7. Restart Home Assistant.
8. Open Settings > Devices & Services > Add Integration.
9. Search for `Better Thermostat Presets` and add it.

This is the recommended installation method for Home Assistant users and follows the standard custom integration flow used in the marketplace ecosystem.

## Configuration

The integration supports the following values:

| Option | Default |
|---|---|
| Excluded presets | `boost, none` |
| Entity ID suffix | `heizpreset` |
| Display name suffix | `Heizpreset` |
| Friendly name regex | empty |
| Friendly name replacement | empty |

The friendly name is built from the original Better Thermostat entity name. If no regex is configured, the display name becomes `Wohnzimmer: Heizpreset`. If a regex is configured, it is applied to the friendly name instead, which allows custom patterns such as `^(.*)$` with a replacement like `\1: Nachtmodus`.

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
