"""Prints instead of sending, so the confirm loop can be walked locally without
an email provider or a real inbox."""


class ConsoleNotifier:
    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"--- email to {to}\n{subject}\n\n{body}\n---")
