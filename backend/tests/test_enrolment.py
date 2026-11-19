from datetime import UTC, datetime, timedelta

import pytest

from dmvwatch.domain.models import CodeCheck, TransactionType, WatchStatus
from dmvwatch.security.codes import CodeCipher
from dmvwatch.security.links import Action, ActionLinks, LinkRejected
from dmvwatch.services.enrolment import EnrolmentService, UnsupportedState
from tests.fakes import (
    FakeClock,
    FakeCodeValidator,
    InMemoryWatchRepository,
    RecordingNotifier,
)

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
CODE = "h75-56f-psf-yrs"
SECRET = "s3cret"
ACCEPTED = CodeCheck(
    accepted=True,
    transaction_type=TransactionType.PERMIT_LICENSE_ID,
    office_ids=("7001", "7002"),
)
REJECTED = CodeCheck(accepted=False, reason="code_not_found")


def _service(
    check: CodeCheck = ACCEPTED,
) -> tuple[EnrolmentService, InMemoryWatchRepository, RecordingNotifier]:
    repository = InMemoryWatchRepository()
    mail = RecordingNotifier()
    service = EnrolmentService(
        validators={"NY": FakeCodeValidator("NY", check)},
        repository=repository,
        notifier=mail,
        cipher=CodeCipher(keys={1: b"0" * 32}, current_version=1),
        links=ActionLinks(secret=SECRET),
        clock=FakeClock(NOW),
        base_url="https://dmvwatch.example",
    )
    return service, repository, mail


async def test_a_good_code_creates_a_pending_watch() -> None:
    service, repo, _ = _service()
    outcome = await service.enrol("a@example.com", CODE, "NY")
    assert outcome.accepted is True
    assert repo.watches[outcome.watch_id]["status"] is WatchStatus.PENDING_CONFIRMATION


async def test_the_code_is_stored_encrypted_not_in_the_clear() -> None:
    service, repo, _ = _service()
    outcome = await service.enrol("a@example.com", CODE, "NY")
    assert CODE.encode() not in repo.credentials[outcome.watch_id].ciphertext


async def test_enrolling_sends_a_confirmation_email_with_a_working_link() -> None:
    service, _, mail = _service()
    outcome = await service.enrol("a@example.com", CODE, "NY")
    to, _subject, body = mail.sent[0]
    assert to == "a@example.com"
    token = body.split("/confirm/")[1].split()[0]
    verified = ActionLinks(secret=SECRET).verify(token, max_age=timedelta(days=7))
    assert verified == (outcome.watch_id, Action.CONFIRM)


async def test_the_confirmation_email_never_contains_the_code() -> None:
    service, _, mail = _service()
    await service.enrol("a@example.com", CODE, "NY")
    assert CODE not in mail.sent[0][2]


async def test_a_rejected_code_creates_nothing_and_sends_nothing() -> None:
    service, repo, mail = _service(check=REJECTED)
    outcome = await service.enrol("a@example.com", CODE, "NY")
    assert outcome.accepted is False
    assert outcome.reason == "code_not_found"
    assert repo.watches == {}
    assert mail.sent == []


async def test_an_unsupported_state_is_refused_rather_than_guessed_at() -> None:
    service, _, _ = _service()
    with pytest.raises(UnsupportedState):
        await service.enrol("a@example.com", CODE, "CA")


async def test_confirming_activates_the_watch() -> None:
    service, repo, _ = _service()
    outcome = await service.enrol("a@example.com", CODE, "NY")
    await service.apply(ActionLinks(secret=SECRET).sign(outcome.watch_id, Action.CONFIRM))
    assert repo.watches[outcome.watch_id]["status"] is WatchStatus.ACTIVE


async def test_reporting_a_booking_closes_the_watch_and_deletes_the_code() -> None:
    service, repo, _ = _service()
    outcome = await service.enrol("a@example.com", CODE, "NY")
    await service.apply(ActionLinks(secret=SECRET).sign(outcome.watch_id, Action.BOOKED))
    assert repo.watches[outcome.watch_id]["status"] is WatchStatus.CLOSED
    assert outcome.watch_id not in repo.credentials


async def test_still_looking_leaves_the_watch_active_and_the_code_in_place() -> None:
    service, repo, _ = _service()
    outcome = await service.enrol("a@example.com", CODE, "NY")
    links = ActionLinks(secret=SECRET)
    await service.apply(links.sign(outcome.watch_id, Action.CONFIRM))
    await service.apply(links.sign(outcome.watch_id, Action.STILL_LOOKING))
    assert repo.watches[outcome.watch_id]["status"] is WatchStatus.ACTIVE
    assert outcome.watch_id in repo.credentials


async def test_muting_an_office_records_it() -> None:
    service, repo, _ = _service()
    outcome = await service.enrol("a@example.com", CODE, "NY")
    token = ActionLinks(secret=SECRET).sign(outcome.watch_id, Action.MUTE_OFFICE)
    await service.apply(token, office_id="7002")
    assert repo.mutes == [(outcome.watch_id, "7002")]


async def test_a_forged_link_is_refused() -> None:
    service, _, _ = _service()
    with pytest.raises(LinkRejected):
        await service.apply("forged")


async def test_state_codes_are_matched_case_insensitively() -> None:
    service, _, _ = _service()
    assert (await service.enrol("a@example.com", CODE, "ny")).accepted is True
