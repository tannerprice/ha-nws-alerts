from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import NWSAlertsCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NWSAlertsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NWSAlertsSensor(coordinator, entry)])


class NWSAlertsSensor(SensorEntity):
    _attr_icon = "mdi:alert"
    _attr_name = DEFAULT_NAME
    _attr_native_unit_of_measurement = "alerts"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: NWSAlertsCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_active_alerts"
        self._unsub_coordinator_update: CALLBACK_TYPE | None = None
        self._sync_from_coordinator()

    async def async_added_to_hass(self) -> None:
        self._unsub_coordinator_update = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_coordinator_update is not None:
            self._unsub_coordinator_update()
            self._unsub_coordinator_update = None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._sync_from_coordinator()
        self.async_write_ha_state()

    def _sync_from_coordinator(self) -> None:
        data = self.coordinator.data or {}
        self._attr_available = self.coordinator.last_update_success
        self._attr_native_value = int(data.get("count", 0))
        self._attr_extra_state_attributes = {
            "alerts": data.get("alerts", []),
            "url": data.get("url"),
        }
