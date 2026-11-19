"use client";

import { useState, type FormEvent } from "react";

const CODE_SHAPE = /^[A-Za-z0-9]{3}-[A-Za-z0-9]{3}-[A-Za-z0-9]{3}-[A-Za-z0-9]{3}$/;

/** Groups what the person types into the four blocks the DMV codes come in. */
function groupCode(raw: string): string {
  const cleaned = raw.replace(/[^A-Za-z0-9]/g, "").slice(0, 12);
  return cleaned.replace(/(.{3})(?=.)/g, "$1-");
}

type Outcome = { tone: "open" | "plain"; message: string };

export function WatchForm() {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [sending, setSending] = useState(false);
  const [outcome, setOutcome] = useState<Outcome | null>(null);

  const codeLooksRight = CODE_SHAPE.test(code);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setOutcome(null);

    if (!codeLooksRight) {
      setOutcome({
        tone: "plain",
        message: "An access code is twelve characters in four blocks, like abc-123-def-456.",
      });
      return;
    }

    setSending(true);
    try {
      const response = await fetch("/api/watch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, accessCode: code }),
      });
      const body = (await response.json()) as { message?: string };
      setOutcome({
        tone: response.ok ? "open" : "plain",
        message:
          body.message ??
          (response.ok
            ? "Check your inbox and confirm the address. Watching starts after that."
            : "That did not go through. Try again in a minute."),
      });
    } catch {
      setOutcome({ tone: "plain", message: "Could not reach the server. Check your connection." });
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <label className="field">
        <span className="label">Email</span>
        <span className="hint">Where the alert goes. Nothing else is sent here.</span>
        <input
          className="input"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
        />
      </label>

      <label className="field">
        <span className="label">Access code</span>
        <span className="hint">
          The twelve-character code in your DMV pre-screening email.
        </span>
        <input
          className="input"
          type="text"
          name="accessCode"
          inputMode="text"
          autoComplete="off"
          spellCheck={false}
          required
          value={code}
          onChange={(event) => setCode(groupCode(event.target.value))}
          placeholder="abc-123-def-456"
          aria-describedby={outcome ? "watch-outcome" : undefined}
        />
      </label>

      <button className="submit" type="submit" disabled={sending}>
        {sending ? "Checking your code" : "Start watching"}
      </button>

      {outcome && (
        <p
          id="watch-outcome"
          className={outcome.tone === "open" ? "notice noticeOpen" : "notice"}
          role="status"
        >
          {outcome.message}
        </p>
      )}
    </form>
  );
}
