# Better Thermostat Presets

A Home Assistant custom integration that creates preset selectors
for Better Thermostat climate entities.

## Features

- Automatic discovery through the Better Thermostat integration.
- Dynamic preset options.
- Configurable excluded presets.
- Configurable entity ID suffix.
- Configurable display name suffix.
- Configuration options can be changed after installation.
- German, English and French translations.

## Installation

Copy the directory:

`custom_components/better_thermostat_presets`

into your Home Assistant configuration directory.

Restart Home Assistant and add the integration through:

Settings > Devices & Services > Add Integration

Search for Better Thermostat Presets.

## Configuration defaults

| Option | Default |
|---|---|
| Excluded presets | boost, none |
| Entity ID suffix | heizpreset |
| Display name suffix | Heizpreset |

## Entity discovery

Entities are discovered through the integration domain
`better_thermostat`, not through their entity IDs.

## Development status

Dynamic discovery and device association require further testing
against the target Home Assistant version.
