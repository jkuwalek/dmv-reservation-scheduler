from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI

from dmvwatch.api.app import build_app
from dmvwatch.domain.models import CodeCheck, TransactionType, WatchStatus
from dmvwatch.security.codes import CodeCipher
from dmvwatch.security.links import ActionLinks
from dmvwatch.services.enrolment import EnrolmentService
from tests.fakes import (
    FakeClock,
    FakeCodeValidator,
    InMemoryWatchRepository,
    RecordingNotifier,
)

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
CODE = "h75-56f-psf-yrs"
ACCEPTED = CodeCheck(
    accepted=True,
    transaction_type=TransactionType.PERMIT_LICENSE_ID,
    office_ids=("7001",),
)


class Wiring:
    def __init__(self) -> None:
        self.repository = InMemoryWatchRepository()
        self.mail = RecordingNotifier()
        self.service = EnrolmentService(
            validators={"NY": FakeCodeValidator("NY", ACCEPTED)},
            repository=self.repository,
            notifier=self.mail,
            cipher=CodeCipher(keys={1: b"0" * 32}, current_version=1),
            links=ActionLinks(secret="s3cret"),
            clock=FakeClock(NOW),
            base_url="https://dmvwatch.example",
        )
        self.app: FastAPI = build_app(self.service)

    def confirm_token_from_outbox(self) -> str:
        body = self.mail.sent[-1][2]
        return body.split("/confirm/")[1].split()[0]


@pytest.fixture
def wiring() -> Wiring:
    return Wiring()


@pytest_asyncio.fixture
async def client(wiring: Wiring) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=wiring.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as open_client:
        yield open_client


async def test_posting_a_watch_accepts_and_sends_mail(
    client: httpx.AsyncClient, wiring: Wiring
) -> None:
    response = await client.post(
        "/watches", json={"email": "a@example.com", "access_code": CODE, "state": "NY"}
    )
    assert response.status_code == 202
    assert len(wiring.mail.sent) == 1


async def test_the_response_does_not_hand_back_a_token(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/watches", json={"email": "a@example.com", "access_code": CODE, "state": "NY"}
    )
    assert "token" not in response.text


async def test_a_bad_email_is_refused_before_anything_is_stored(
    client: httpx.AsyncClient, wiring: Wiring
) -> None:
    response = await client.post(
        "/watches", json={"email": "nope", "access_code": CODE, "state": "NY"}
    )
    assert response.status_code == 422
    assert wiring.repository.watches == {}
    assert wiring.mail.sent == []


async def test_a_malformed_access_code_is_refused(
    client: httpx.AsyncClient, wiring: Wiring
) -> None:
    response = await client.post(
        "/watches", json={"email": "a@example.com", "access_code": "nope", "state": "NY"}
    )
    assert response.status_code == 422
    assert wiring.repository.watches == {}


async def test_an_unsupported_state_says_so(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/watches", json={"email": "a@example.com", "access_code": CODE, "state": "CA"}
    )
    assert response.status_code == 400
    assert "CA" in response.json()["message"]


async def test_confirming_through_the_emailed_link_activates_the_watch(
    client: httpx.AsyncClient, wiring: Wiring
) -> None:
    await client.post(
        "/watches", json={"email": "a@example.com", "access_code": CODE, "state": "NY"}
    )
    response = await client.get(f"/confirm/{wiring.confirm_token_from_outbox()}")
    assert response.status_code == 200
    watch_id = next(iter(wiring.repository.watches))
    assert wiring.repository.watches[watch_id]["status"] is WatchStatus.ACTIVE


async def test_a_forged_link_is_rejected(client: httpx.AsyncClient) -> None:
    assert (await client.get("/confirm/forged")).status_code == 400


async def test_the_api_reports_itself_healthy(client: httpx.AsyncClient) -> None:
    assert (await client.get("/health")).status_code == 200
