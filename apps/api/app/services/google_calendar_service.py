import logging
from datetime import datetime, timedelta
from typing import Optional

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from app.config import settings
from app.core.security import decrypt_value

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        encrypted: bool = False,
    ) -> None:
        if encrypted:
            decrypted_access = decrypt_value(access_token)
            if not decrypted_access:
                raise Exception("Failed to decrypt Google Calendar access token.")
            access_token = decrypted_access

            if refresh_token:
                decrypted_refresh = decrypt_value(refresh_token)
                if decrypted_refresh:
                    refresh_token = decrypted_refresh
                else:
                    refresh_token = None

        self._credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        self._calendar = build("calendar", "v3", credentials=self._credentials)

    def create_event(
        self,
        title: str,
        description: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
    ) -> str:
        """
        Creates an event in the user's primary Google Calendar.
        Returns the event ID.
        """
        if end_time is None:
            # Default to a 30-minute block for the post publication
            end_time = start_time + timedelta(minutes=30)

        event_body = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
            },
            "end": {
                "dateTime": end_time.isoformat(),
            },
        }

        try:
            event = self._calendar.events().insert(calendarId="primary", body=event_body).execute()
            logger.info(f"Created Google Calendar event: {event.get('id')}")
            return event.get("id")
        except Exception as exc:
            logger.error(f"Failed to create Google Calendar event: {exc}")
            raise

    def delete_event(self, event_id: str) -> None:
        """
        Deletes a previously scheduled event from the user's primary calendar.
        """
        try:
            self._calendar.events().delete(calendarId="primary", eventId=event_id).execute()
            logger.info(f"Deleted Google Calendar event: {event_id}")
        except Exception as exc:
            logger.error(f"Failed to delete Google Calendar event {event_id}: {exc}")
            # We suppress the error so cancelling a post doesn't fail just because the calendar event was manually deleted
