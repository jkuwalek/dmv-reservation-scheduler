import httpx

ENDPOINT = "https://api.resend.com/emails"


class SendFailed(Exception):
    pass


class ResendNotifier:
    def __init__(self, client: httpx.AsyncClient, api_key: str, sender: str) -> None:
        self._client = client
        self._api_key = api_key
        self._sender = sender

    async def send(self, to: str, subject: str, body: str) -> None:
        response = await self._client.post(
            ENDPOINT,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"from": self._sender, "to": [to], "subject": subject, "text": body},
        )
        if response.status_code >= 400:
            # Status only. The response body can echo the request, key included.
            raise SendFailed(f"resend returned {response.status_code}")
