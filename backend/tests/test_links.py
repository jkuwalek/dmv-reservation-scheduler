import uuid
from datetime import timedelta

import pytest

from dmvwatch.security.links import Action, ActionLinks, LinkRejected

WATCH = uuid.UUID("11111111-2222-3333-4444-555555555555")


def test_a_token_round_trips() -> None:
    links = ActionLinks(secret="s3cret")
    token = links.sign(WATCH, Action.CONFIRM)
    assert links.verify(token, max_age=timedelta(days=1)) == (WATCH, Action.CONFIRM)


def test_each_action_gets_its_own_token() -> None:
    links = ActionLinks(secret="s3cret")
    assert links.sign(WATCH, Action.CONFIRM) != links.sign(WATCH, Action.BOOKED)


def test_an_expired_token_is_rejected() -> None:
    links = ActionLinks(secret="s3cret")
    token = links.sign(WATCH, Action.CONFIRM)
    with pytest.raises(LinkRejected):
        links.verify(token, max_age=timedelta(seconds=-1))


def test_a_token_signed_with_another_secret_is_rejected() -> None:
    token = ActionLinks(secret="one").sign(WATCH, Action.CONFIRM)
    with pytest.raises(LinkRejected):
        ActionLinks(secret="two").verify(token, max_age=timedelta(days=1))


def test_a_tampered_token_is_rejected() -> None:
    links = ActionLinks(secret="s3cret")
    token = links.sign(WATCH, Action.CONFIRM)
    with pytest.raises(LinkRejected):
        links.verify(token[:-2] + "xy", max_age=timedelta(days=1))


def test_rubbish_is_rejected_rather_than_crashing() -> None:
    with pytest.raises(LinkRejected):
        ActionLinks(secret="s3cret").verify("not-a-token", max_age=timedelta(days=1))
