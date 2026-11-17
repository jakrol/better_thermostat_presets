# Testing notes

This project keeps its validation lightweight so it can be run in a minimal local environment without a full Home Assistant installation.

## Commands

Run the automated checks from the project root:

```bash
python3 -m unittest discover -s tests -v
```

## What the tests cover

- `slugify` sanitizes entity-id fragments.
- configuration parsing strips whitespace and lowercases excluded presets.
- the selector entity exposes the available preset list correctly and reflects the current state.

## Why this approach

The project depends on Home Assistant runtime types during import, but the testing environment in this workspace does not include the full Home Assistant package. The tests therefore inject minimal stubs for the required modules and validate the actual project logic instead of relying on a live HA instance.

## Notes

These tests validate behavior and logic, but they do not replace a real Home Assistant runtime verification in an end-to-end installation.
