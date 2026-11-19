import httpx
import pytest

from dmvwatch.adapters.email.console import ConsoleNotifier
from dmvwatch.adapters.email.resend import ResendNotifier, SendFailed


async def test_the_console_notifier_shows_what_it_would_send(
    capsys: pytest.CaptureFixture[str],
) -> None:
    await ConsoleNotifier().send("a@example.com", "Subject", "Body")
    printed = capsys.readouterr().out
    assert "a@example.com" in printed
    assert "Body" in printed


async def test_resend_posts_the_message() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization", "")
        seen["body"] = request.content.decode()
        return httpx.Response(200, json={"id": "abc"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        notifier = ResendNotifier(client=client, api_key="key", sender="bot@example.com")
        await notifier.send("a@example.com", "Subject", "Body")

    assert seen["url"] == "https://api.resend.com/emails"
    assert seen["auth"] == "Bearer key"
    assert "a@example.com" in seen["body"]
    assert "bot@example.com" in seen["body"]


async def test_resend_raises_when_the_api_refuses() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "bad"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        notifier = ResendNotifier(client=client, api_key="key", sender="bot@example.com")
        with pytest.raises(SendFailed):
            await notifier.send("a@example.com", "Subject", "Body")


async def test_the_failure_message_does_not_leak_the_api_key() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        notifier = ResendNotifier(client=client, api_key="sup3rsecret", sender="b@e.com")
        with pytest.raises(SendFailed) as caught:
            await notifier.send("a@example.com", "Subject", "Body")
    assert "sup3rsecret" not in str(caught.value)
