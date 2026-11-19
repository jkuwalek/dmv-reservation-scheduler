"""Signing someone up, and the confirm / booked / mute loop that follows.

Code validation is a protocol rather than a concrete class, so a state is supported
the moment someone writes its validator and nothing here changes.
"""

import uuid
from collections.abc import Mapping
from datetime import timedelta

from dmvwatch.domain.models import Enrolment, WatchStatus
from dmvwatch.domain.protocols import Clock, CodeValidator, Notifier, WatchRepository
from dmvwatch.security.codes import CodeCipher
from dmvwatch.security.links import Action, ActionLinks

LINK_LIFETIME = timedelta(days=7)
NO_WATCH = uuid.UUID(int=0)


class UnsupportedState(LookupError):
    pass


class EnrolmentService:
    def __init__(
        self,
        validators: Mapping[str, CodeValidator],
        repository: WatchRepository,
        notifier: Notifier,
        cipher: CodeCipher,
        links: ActionLinks,
        clock: Clock,
        base_url: str,
    ) -> None:
        self._validators = {code.upper(): validator for code, validator in validators.items()}
        self._repository = repository
        self._notifier = notifier
        self._cipher = cipher
        self._links = links
        self._clock = clock
        self._base_url = base_url.rstrip("/")

    async def enrol(self, email: str, access_code: str, state_code: str) -> Enrolment:
        validator = self._validators.get(state_code.upper())
        if validator is None:
            raise UnsupportedState(state_code.upper())

        check = await validator.check(access_code)
        if not check.accepted or check.transaction_type is None:
            return Enrolment(
                watch_id=NO_WATCH,
                accepted=False,
                reason=check.reason or "code_not_accepted",
            )

        watch_id = await self._repository.create(
            email=email,
            state_code=state_code.upper(),
            transaction_type=check.transaction_type,
            encrypted_code=self._cipher.encrypt(access_code),
            created_at=self._clock.now(),
        )

        token = self._links.sign(watch_id, Action.CONFIRM)
        await self._notifier.send(
            to=email,
            subject="Confirm your DMV slot watch",
            body=(
                "Confirm this address and we will start watching for a free slot.\n\n"
                f"{self._base_url}/confirm/{token}\n\n"
                "If you did not ask for this, ignore this email and nothing happens."
            ),
        )
        return Enrolment(watch_id=watch_id, accepted=True)

    async def apply(self, token: str, office_id: str | None = None) -> Action:
        watch_id, action = self._links.verify(token, max_age=LINK_LIFETIME)

        match action:
            case Action.CONFIRM | Action.STILL_LOOKING:
                await self._repository.set_status(watch_id, WatchStatus.ACTIVE)
            case Action.BOOKED:
                await self._repository.set_status(watch_id, WatchStatus.CLOSED)
                await self._repository.forget_credential(watch_id)
            case Action.MUTE_OFFICE if office_id is not None:
                await self._repository.mute_office(watch_id, office_id, self._clock.now())
            case _:
                pass

        return action
