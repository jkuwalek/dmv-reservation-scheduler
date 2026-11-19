"""One-click links for the confirm / booked / mute loop.

Signed and expiring, which is what lets the whole product work without accounts:
the link itself is the authorisation, and it stops working after a week.
"""

import uuid
from datetime import timedelta
from enum import StrEnum

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class Action(StrEnum):
    CONFIRM = "confirm"
    BOOKED = "booked"
    STILL_LOOKING = "still_looking"
    MUTE_OFFICE = "mute_office"


class LinkRejected(Exception):
    pass


class ActionLinks:
    def __init__(self, secret: str) -> None:
        self._serializer = URLSafeTimedSerializer(secret, salt="dmvwatch-action")

    def sign(self, watch_id: uuid.UUID, action: Action) -> str:
        return self._serializer.dumps({"w": str(watch_id), "a": action.value})

    def verify(self, token: str, max_age: timedelta) -> tuple[uuid.UUID, Action]:
        try:
            payload = self._serializer.loads(token, max_age=int(max_age.total_seconds()))
        except (BadSignature, SignatureExpired) as exc:
            raise LinkRejected("link is not valid") from exc

        if not isinstance(payload, dict):
            raise LinkRejected("unexpected payload")
        try:
            return uuid.UUID(str(payload["w"])), Action(str(payload["a"]))
        except (KeyError, ValueError) as exc:
            raise LinkRejected("unexpected payload") from exc
