import datetime
import uuid
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
    CalendarEntityFeature,
    EVENT_DESCRIPTION,
    EVENT_END,
    EVENT_LOCATION,
    EVENT_START,
    EVENT_SUMMARY,
)
from .const import DOMAIN
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
import logging

_LOGGER = logging.getLogger(__name__)


class SemanticIndex(CalendarEntity):
    """Representation of a Calendar."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the calendar."""
        self.hass = hass
        self._attr_name = config_entry.title
        self._attr_unique_id = config_entry.entry_id
        self._events = hass.data[DOMAIN].get("events", [])
        self._current_event = None
        self._attr_supported_features = (
            CalendarEntityFeature.CREATE_EVENT | CalendarEntityFeature.DELETE_EVENT
        )
        _LOGGER.info(f"events in backend: {self.hass.data[DOMAIN].get('events', [])}")
        _LOGGER.info(f"events loaded: {self._events}")

    def _ensure_datetime(self, dt):
        """Ensure the input is a datetime.datetime object."""
        if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
            dt = datetime.datetime.combine(dt, datetime.datetime.min.time())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        events = []

        # Ensure start_date and end_date are datetime.datetime objects and timezone-aware
        start_date = self._ensure_datetime(start_date)
        end_date = self._ensure_datetime(end_date)

        for event in self._events:
            # Ensure event.end and event.start are datetime.datetime objects and timezone-aware
            event_end = self._ensure_datetime(event.end)
            event_start = self._ensure_datetime(event.start)

            if event_end > start_date and event_start < end_date:
                events.append(event)
        return events

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "events": [event.summary for event in self._events],
        }

    @property
    def event(self):
        """Return the current event."""
        return self._current_event

    async def async_create_event(self, **kwargs: any) -> None:
        """Add a new event to calendar."""
        dtstart = kwargs[EVENT_START]
        dtend = kwargs[EVENT_END]
        start: datetime.datetime
        end: datetime.datetime
        summary = kwargs[EVENT_SUMMARY]
        description = kwargs.get(EVENT_DESCRIPTION)
        location = kwargs.get(EVENT_LOCATION)

        if isinstance(dtstart, datetime.datetime):
            start = dt_util.as_local(dtstart)
            end = dt_util.as_local(dtend)
        else:
            start = dtstart
            end = dtend

        event = CalendarEvent(
            uid=str(uuid.uuid4()),
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location
        )

        self._events.append(event)
        await self.async_update()

    async def async_delete_event(
        self,
        uid: str,
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Delete an event on the calendar."""
        self._events = [event for event in self._events if event.uid != uid]
        await self.async_update()

    async def async_update(self) -> None:
        self.hass.data[DOMAIN]["events"] = self._events
        self.async_write_ha_state()
        _LOGGER.info(f"events: {self.hass.data[DOMAIN].get('events', [])}")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar platform."""

    calendar_entity = SemanticIndex(hass, config_entry)
    async_add_entities([calendar_entity])


async def async_remove(self):
    """Handle removal of the entity."""
    _LOGGER.info(f"Removing calendar entity: {self._attr_name}")
    await super().async_remove()