# ollama_client.py — Interface to the local Ollama LLM
# All LLM calls funnel through here. Never call Ollama directly elsewhere.

import requests
import json
from typing import Generator, Optional
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from utils.logger import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """
    Thin wrapper around the Ollama REST API.
    Supports:
      - Single-shot completion
      - Streaming completion (word-by-word)
      - Health check
      - Model listing
    """

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model    = model
        logger.info(f"OllamaClient initialised — model: {self.model}")

    # ── Health ─────────────────────────────────────────────────────────────

    def is_running(self) -> bool:
        """Check if Ollama server is up and responding."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.exceptions.ConnectionError:
            logger.warning("Ollama is not running or unreachable.")
            return False

    def list_models(self) -> list[str]:
        """Return list of locally available model names."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            logger.debug(f"Available models: {models}")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    # ── Core Chat ──────────────────────────────────────────────────────────

    def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        stream: bool = False,
    ) -> str:
        """
        Send a conversation to Ollama and return the full response text.

        Args:
            messages: List of {"role": "user"/"assistant"/"system", "content": "..."}
            model:    Override the default model for this call
            stream:   If True, stream tokens (currently returns full text still)

        Returns:
            The assistant's reply as a plain string.
        """
        target_model = model or self.model
        payload = {
            "model":    target_model,
            "messages": messages,
            "stream":   stream,
        }

        logger.debug(f"Sending chat to Ollama [{target_model}] — {len(messages)} messages")

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=OLLAMA_TIMEOUT,
                stream=stream,
            )
            resp.raise_for_status()

            if stream:
                return self._collect_stream(resp)
            else:
                data = resp.json()
                reply = data["message"]["content"].strip()
                logger.debug(f"Ollama replied ({len(reply)} chars)")
                return reply

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out.")
            return "Sorry, I took too long to respond. Please try again."
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Is it running?")
            return "I can't reach my brain right now. Please make sure Ollama is running."
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return f"Something went wrong: {str(e)}"

    def _collect_stream(self, response: requests.Response) -> str:
        """Collect all streamed chunks into a single string."""
        full_text = []
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    full_text.append(token)
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
        return "".join(full_text).strip()

    def stream_chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        Stream tokens from Ollama as a generator.
        Use this for real-time UI updates (word-by-word display).

        Yields:
            Token strings one at a time.
        """
        target_model = model or self.model
        payload = {
            "model":    target_model,
            "messages": messages,
            "stream":   True,
        }

        try:
            with requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=OLLAMA_TIMEOUT,
                stream=True,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield "Error streaming response."

    # ── Simple prompt (no conversation history) ───────────────────────────

    def prompt(self, user_text: str, system_prompt: Optional[str] = None) -> str:
        """
        Single-turn convenience method. No history, just a prompt → reply.

        Args:
            user_text:     The user's message
            system_prompt: Optional system instruction

        Returns:
            The model's reply as a string.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_text})
        return self.chat(messages)


# ── Module-level singleton ─────────────────────────────────────────────────
# Import and use this directly: from ai.ollama_client import ollama
ollama = OllamaClient()