# Better Thermostat Presets

A Home Assistant custom integration that creates preset selector entities for Better Thermostat climate devices.

## Project attribution

The initial scaffold and first commit were generated with ChatGPT. The subsequent implementation, refinements, and maintenance were done by GitHub Copilot.

## Status

This repository is for active development and is intended for installation as a custom Home Assistant integration.

## Features

- Automatic discovery of Better Thermostat climate entities.
- Preset selector entities for the thermostat's available modes.
- Filter out presets such as `boost` or `none`.
- Configurable entity ID suffix.
- Fixed naming mode with `prefix` or `regex`.
- Translation files for German, English and French.

## How it works

The integration searches the entity registry for climate entities from `better_thermostat` and creates a `select` entity for each matching thermostat.

The selector name is based on the Better Thermostat `friendly_name`, not the entity ID. The naming mode can be set to `prefix` or `regex`.

When a user selects a new preset, the integration calls the standard climate service:

- `climate.set_preset_mode`

## Installation

### Install via HACS / Home Assistant Marketplace

1. Open Home Assistant.
2. Go to HACS.
3. Add this repository as a custom integration:

   `https://github.com/jakrol/better_thermostat_presets`

4. Install the integration.
5. Restart Home Assistant.
6. Open Settings > Devices & Services > Add Integration.
7. Search for `Better Thermostat Presets` and add it.

## Configuration

| Option | Default |
|---|---|
| Excluded presets | `boost, none` |
| Entity ID suffix | `heizpreset` |
| Name mode | `prefix` |
| Name suffix | `Heizpreset` |
| Regex pattern | empty |
| Regex replacement | empty |

In `prefix` mode, a fixed suffix is added to the Better Thermostat `friendly_name`, for example `Wohnzimmer: Heizpreset`.
In `regex` mode, the name is rewritten with a custom regex pattern such as `^(.*)$` and a replacement like `\1: Nachtmodus`.

## Project structure

- `__init__.py` initializes the integration and loads the `select` platform.
- `select.py` contains the selector logic.
- `config_flow.py` defines the setup and options UI.
- `const.py` stores defaults and metadata.
- `translations/*.json` contains localized labels.

## Development and testing

The repository includes a minimal unit-test suite under `tests/` for normalization and selector behavior.

Run it with:

```bash
python3 -m unittest discover -s tests -v
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Notes

This project wraps the preset system already provided by Better Thermostat. It does not replace the thermostat logic itself.
