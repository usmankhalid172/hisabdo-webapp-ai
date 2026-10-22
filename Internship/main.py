from fastapi import FastAPI
from fastapi import HTTPException
from embeddings import (
    generate_embeddings,
    EmbeddingProviderError,
)
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from google import genai
from prompt import build_system_prompt
from memory import get_session, add_message
from logger import logger

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()
from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    chunks: list[str] = Field(min_length=1, max_length=100)


@app.post("/api/v1/embeddings")
def create_embeddings(request: EmbeddingRequest):
    try:
        vectors = generate_embeddings(request.chunks)

        return {
            "count": len(vectors),
            "dimensions": len(vectors[0]) if vectors else 0,
            "embeddings": vectors,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except EmbeddingProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

class ChatRequest(BaseModel):
    session_id: str
    message: str
    user: dict = {}
    business: dict = {}
    customer: dict = {}
    tasks: list = []
    notes: list = []


@app.get("/")
def home():
    return {"message": "HisabDo AI API is running"}



@app.post("/api/v1/chat")
def chat(request: ChatRequest):
    session = get_session(request.session_id)

    add_message(request.session_id, "user", request.message)

    logger.info(
        f"Chat request received for session: {request.session_id}"
    )

    # Build a system prompt using the available business profile
    system_prompt = build_system_prompt(request.business)

    # Add the request's available business context
    context = f"""
User Data: {request.user}
Business Data: {request.business}
Customer Data: {request.customer}
Tasks: {request.tasks}
Notes: {request.notes}
Conversation History: {session}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=(
            f"{system_prompt}\n\n"
            f"{context}\n\n"
            f"User Question: {request.message}"
        )
    )

    ai_response = response.text or (
        "Sorry, I could not generate a response."
    )

    add_message(request.session_id, "assistant", ai_response)

    logger.info(
        f"Chat response generated for session: {request.session_id}"
    )

    return {
        "session_id": request.session_id,
        "response": ai_response
    }

