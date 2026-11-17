# Initial project scaffold created with ChatGPT.
# Subsequent implementation and refinements were authored by GitHub Copilot.
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_AUTOCREATE,
    CONF_ENTITY_ID_SUFFIX,
    CONF_NAME_SUFFIX,
    DEFAULT_ENTITY_ID_SUFFIX,
    DEFAULT_NAME_SUFFIX,
    DOMAIN,
    LEGACY_DEFAULT_ENTITY_ID_SUFFIX,
    LEGACY_DEFAULT_NAME_SUFFIX,
    PLATFORMS,
)


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    """Set up the integration."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up a config entry."""

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Migrate old defaults and selector IDs."""

    if entry.version == 1 and entry.minor_version < 4:
        data = dict(entry.data)
        options = dict(entry.options)
        if data.get(CONF_AUTOCREATE) is True and CONF_AUTOCREATE not in options:
            data[CONF_AUTOCREATE] = False

        migrate_suffix = (
            data.get(CONF_ENTITY_ID_SUFFIX) == LEGACY_DEFAULT_ENTITY_ID_SUFFIX
            and CONF_ENTITY_ID_SUFFIX not in options
        )
        if migrate_suffix:
            from .select import slugify

            registry = er.async_get(hass)

            @callback
            def migrate_select_entity(entity_entry):
                """Update only selector IDs generated with the old default."""

                old_suffix = f"_{LEGACY_DEFAULT_ENTITY_ID_SUFFIX}"
                if (
                    entity_entry.domain != "select"
                    or entity_entry.platform != DOMAIN
                    or not entity_entry.unique_id.endswith(old_suffix)
                ):
                    return None

                source_unique_id = entity_entry.unique_id[: -len(old_suffix)]
                source_entity_id = registry.async_get_entity_id(
                    "climate",
                    "better_thermostat",
                    source_unique_id,
                )
                if source_entity_id is None:
                    return None

                source_object_id = source_entity_id.removeprefix("climate.")
                old_object_id = slugify(
                    f"{source_object_id}_{LEGACY_DEFAULT_ENTITY_ID_SUFFIX}"
                )
                new_object_id = slugify(
                    f"{source_object_id}_{DEFAULT_ENTITY_ID_SUFFIX}"
                )
                generated_old_ids = {
                    f"select.{old_object_id}",
                    f"select.climate_{old_object_id}",
                }
                if entity_entry.original_name:
                    generated_old_ids.add(
                        f"select.{slugify(entity_entry.original_name)}"
                    )

                changes = {
                    "new_unique_id": (
                        f"{source_unique_id}_{DEFAULT_ENTITY_ID_SUFFIX}"
                    )
                }
                if entity_entry.entity_id in generated_old_ids:
                    changes["new_entity_id"] = f"select.{new_object_id}"
                return changes

            await er.async_migrate_entries(
                hass,
                entry.entry_id,
                migrate_select_entity,
            )
            data[CONF_ENTITY_ID_SUFFIX] = DEFAULT_ENTITY_ID_SUFFIX

        if (
            data.get(CONF_NAME_SUFFIX) == LEGACY_DEFAULT_NAME_SUFFIX
            and CONF_NAME_SUFFIX not in options
        ):
            data[CONF_NAME_SUFFIX] = DEFAULT_NAME_SUFFIX

        hass.config_entries.async_update_entry(
            entry,
            data=data,
            minor_version=4,
        )

    return True
