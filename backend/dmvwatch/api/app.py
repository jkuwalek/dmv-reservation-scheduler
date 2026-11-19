"""HTTP surface. Thin on purpose: validate input, call a service, map errors."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from dmvwatch.security.links import LinkRejected
from dmvwatch.services.enrolment import EnrolmentService, UnsupportedState

CODE_PATTERN = r"^[A-Za-z0-9]{3}(-[A-Za-z0-9]{3}){3}$"


class WatchRequest(BaseModel):
    email: EmailStr
    access_code: str = Field(pattern=CODE_PATTERN)
    state: str = Field(min_length=2, max_length=2)


def build_app(enrolment: EnrolmentService) -> FastAPI:
    app = FastAPI(title="dmvwatch")

    async def apply_token(token: str, office_id: str | None = None) -> JSONResponse:
        try:
            action = await enrolment.apply(token, office_id=office_id)
        except LinkRejected:
            return JSONResponse(
                status_code=400,
                content={"message": "That link is not valid any more."},
            )
        return JSONResponse(status_code=200, content={"action": action.value})

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/watches", status_code=202)
    async def create_watch(request: WatchRequest) -> JSONResponse:
        try:
            outcome = await enrolment.enrol(
                email=str(request.email),
                access_code=request.access_code,
                state_code=request.state,
            )
        except UnsupportedState as exc:
            return JSONResponse(
                status_code=400,
                content={"message": f"{exc.args[0]} is not supported yet."},
            )

        if not outcome.accepted:
            return JSONResponse(
                status_code=400,
                content={"message": "The DMV did not accept that access code."},
            )

        return JSONResponse(
            status_code=202,
            content={"message": "Check your inbox and confirm the address."},
        )

    @app.get("/confirm/{token}")
    async def confirm(token: str) -> JSONResponse:
        return await apply_token(token)

    @app.get("/booked/{token}")
    async def booked(token: str) -> JSONResponse:
        return await apply_token(token)

    @app.get("/still-looking/{token}")
    async def still_looking(token: str) -> JSONResponse:
        return await apply_token(token)

    @app.get("/mute/{token}/{office_id}")
    async def mute(token: str, office_id: str) -> JSONResponse:
        return await apply_token(token, office_id=office_id)

    return app
