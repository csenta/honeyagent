"""
Tripwire Callback Server for HoneyAgent.
Intercepts token usage, image beacon calls, and API authentication probes.
"""

import uuid
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from honeyagent.core.models import TripwireIncident
from honeyagent.core.registry import HoneytokenRegistry
from honeyagent.core.generator import HoneytokenGenerator
from honeyagent.engine.alerts import AlertDispatcher

# 1x1 Transparent GIF bytes
TRANSPARENT_GIF = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


def create_tripwire_app(
    registry: HoneytokenRegistry,
    generator: HoneytokenGenerator,
    dispatcher: AlertDispatcher,
) -> FastAPI:
    app = FastAPI(
        title="HoneyAgent Tripwire Listener",
        description="Deception Callback Listener for AI RAG Honeytokens",
        version="1.0.0",
    )

    def _record_intrusion(request: Request, token_id: str, token_type: str, provenance: str):
        client_ip = request.client.host if request.client else "127.0.0.1"
        user_agent = request.headers.get("user-agent", "unknown")
        incident = TripwireIncident(
            incident_id=f"inc_{uuid.uuid4().hex[:10]}",
            token_id=token_id,
            token_type=token_type,
            provenance_tag=provenance,
            attacker_ip=client_ip,
            user_agent=user_agent,
            request_method=request.method,
            request_path=str(request.url.path),
            headers=dict(request.headers),
        )
        dispatcher.dispatch(incident)

    @app.get("/status")
    async def status_check():
        return {
            "service": "HoneyAgent Tripwire Listener",
            "active_tokens": len(registry.tokens),
            "status": "listening",
        }

    @app.get("/beacon/{token_id}")
    async def beacon_callback(token_id: str, request: Request):
        """Image tracker beacon called when canary doc is viewed or parsed."""
        token = registry.get(token_id)
        provenance = token.provenance_tag if token else "unregistered_or_forged"
        token_type = token.token_type.value if token else "CANARY_DOCUMENT"

        _record_intrusion(request, token_id, token_type, provenance)
        return Response(content=TRANSPARENT_GIF, media_type="image/gif")

    @app.api_route("/api/v1/auth", methods=["GET", "POST"])
    @app.api_route("/api/v1/user", methods=["GET", "POST"])
    async def auth_probe(request: Request):
        """Intercepts attacker attempting to use stolen API Bearer token."""
        auth_header = request.headers.get("authorization", "")
        token_id = "unknown_bearer"
        provenance = "unmapped_token"

        for part in auth_header.split():
            if part.startswith("sec_live_ht_"):
                extracted_id = part.replace("sec_live_", "")
                token = registry.get(extracted_id)
                token_id = extracted_id
                if token:
                    provenance = token.provenance_tag
                break

        _record_intrusion(request, token_id, "API_BEARER_TOKEN", provenance)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid or revoked credentials"},
        )

    @app.api_route("/aws-sts", methods=["GET", "POST"])
    async def aws_sts_probe(request: Request):
        """Intercepts attacker attempting to use stolen AWS access key."""
        body = await request.body()
        auth_header = request.headers.get("authorization", "")
        content = (body.decode("utf-8", errors="ignore") + auth_header).upper()

        token_id = "unknown_aws_key"
        provenance = "unmapped_aws_key"

        for token in registry.tokens.values():
            if token.value in content:
                token_id = token.token_id
                provenance = token.provenance_tag
                break

        _record_intrusion(request, token_id, "AWS_ACCESS_KEY", provenance)
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            content="<ErrorResponse><Error><Code>InvalidClientTokenId</Code></Error></ErrorResponse>",
            media_type="application/xml",
        )

    return app
