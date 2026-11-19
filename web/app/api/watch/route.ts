import { NextResponse } from "next/server";

const CODE_SHAPE = /^[A-Za-z0-9]{3}-[A-Za-z0-9]{3}-[A-Za-z0-9]{3}-[A-Za-z0-9]{3}$/;
const EMAIL_SHAPE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export async function POST(request: Request) {
  let payload: { email?: unknown; accessCode?: unknown };
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ message: "Send JSON." }, { status: 400 });
  }

  const email = typeof payload.email === "string" ? payload.email.trim() : "";
  const accessCode = typeof payload.accessCode === "string" ? payload.accessCode.trim() : "";

  if (!EMAIL_SHAPE.test(email)) {
    return NextResponse.json({ message: "That email address does not look right." }, { status: 400 });
  }

  if (!CODE_SHAPE.test(accessCode)) {
    return NextResponse.json(
      { message: "An access code is twelve characters in four blocks, like abc-123-def-456." },
      { status: 400 },
    );
  }

  const backend = process.env.DMVWATCH_API_URL;
  if (!backend) {
    return NextResponse.json(
      {
        message:
          "Watching is not switched on yet. The New York checker is still being built, so nothing has been saved.",
      },
      { status: 503 },
    );
  }

  const upstream = await fetch(`${backend}/watches`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, access_code: accessCode }),
  });

  const body = (await upstream.json().catch(() => ({}))) as { message?: string };
  return NextResponse.json(
    { message: body.message ?? "Check your inbox and confirm the address." },
    { status: upstream.status },
  );
}
