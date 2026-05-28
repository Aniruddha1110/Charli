# intent_router.py — Classifies voice/text input and routes to correct module
# Uses Ollama to extract intent + parameters from natural language.

import json
import re
from ai.ollama_client import ollama
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Intent definitions ─────────────────────────────────────────────────────

INTENT_PROMPT = """You are an intent classifier for a desktop AI assistant.
Classify the user's message into one of these intents and extract parameters.

INTENTS:
- open_app       → params: {app: string}
- close_app      → params: {app: string}
- type_text      → params: {text: string}
- press_key      → params: {key: string}
- screenshot     → params: {save: bool}
- set_volume     → params: {level: int 0-100}
- mute           → params: {mute: bool}
- volume_up      → params: {amount: int}
- volume_down    → params: {amount: int}
- clipboard_read → params: {}
- clipboard_write→ params: {text: string}
- run_command    → params: {command: string}
- search_web     → params: {query: string}
- search_files   → params: {query: string}
- create_task    → params: {title: string, priority: string}
- create_note    → params: {content: string, title: string}
- chat           → params: {message: string}
- set_reminder   → params: {text: string}

RULES:
- Return ONLY valid JSON, nothing else
- If unsure, use "chat" intent
- For volume_up/down, amount defaults to 10
- For screenshot without "save", save=false
- Extract the exact app name for open_app

EXAMPLES:
"open chrome" → {"intent": "open_app", "params": {"app": "chrome"}}
"open spotify and play music" → {"intent": "open_app", "params": {"app": "spotify"}}
"take a screenshot" → {"intent": "screenshot", "params": {"save": false}}
"save a screenshot" → {"intent": "screenshot", "params": {"save": true}}
"turn volume up" → {"intent": "volume_up", "params": {"amount": 10}}
"set volume to 50" → {"intent": "set_volume", "params": {"level": 50}}
"mute" → {"intent": "mute", "params": {"mute": true}}
"unmute" → {"intent": "mute", "params": {"mute": false}}
"type hello world" → {"intent": "type_text", "params": {"text": "hello world"}}
"press ctrl c" → {"intent": "press_key", "params": {"key": "ctrl+c"}}
"what is python" → {"intent": "chat", "params": {"message": "what is python"}}
"search for latest news" → {"intent": "search_web", "params": {"query": "latest news"}}
"add task buy groceries" → {"intent": "create_task", "params": {"title": "buy groceries", "priority": "normal"}}
"copy clipboard" → {"intent": "clipboard_read", "params": {}}
"run ipconfig" → {"intent": "run_command", "params": {"command": "ipconfig"}}

User message: "{message}"

JSON:"""


def classify_intent(message: str) -> dict:
    """
    Classify a natural language message into a structured intent.

    Returns:
        Dict with 'intent' and 'params' keys
    """
    logger.info(f"Classifying intent: '{message}'")

    try:
        prompt   = INTENT_PROMPT.replace("{message}", message)
        response = ollama.prompt(prompt)

        # Extract JSON from response
        # Sometimes Ollama adds extra text — find the JSON object
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            logger.info(f"Intent: {result.get('intent')} | Params: {result.get('params')}")
            return result
        else:
            logger.warning(f"No JSON found in response: {response}")
            return {"intent": "chat", "params": {"message": message}}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e} | Response: {response}")
        return {"intent": "chat", "params": {"message": message}}
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        return {"intent": "chat", "params": {"message": message}}


def execute_intent(intent: str, params: dict, history: list = None) -> dict:
    """
    Execute the classified intent by calling the right module.

    Returns:
        Dict with 'response' (text to speak back) and 'data' (any extra data)
    """
    logger.info(f"Executing intent: {intent} | params: {params}")

    try:
        # ── App control ───────────────────────────────────────────────
        if intent == "open_app":
            from modules.automation import open_app
            app  = params.get("app", "")
            result = open_app(app)
            if result["success"]:
                return {"response": f"Opening {app}.", "data": result}
            else:
                return {"response": f"I couldn't open {app}. Make sure it's installed.", "data": result}

        # ── Screenshot ────────────────────────────────────────────────
        elif intent == "screenshot":
            from modules.automation import take_screenshot, save_screenshot
            save = params.get("save", False)
            if save:
                result = save_screenshot()
                if result["success"]:
                    return {"response": f"Screenshot saved to your Desktop.", "data": result}
                else:
                    return {"response": "Screenshot failed.", "data": result}
            else:
                result = take_screenshot()
                if result["success"]:
                    return {
                        "response": f"Screenshot taken. {result['width']} by {result['height']} pixels.",
                        "data":     result,
                        "type":     "screenshot",
                    }
                else:
                    return {"response": "Screenshot failed.", "data": result}

        # ── Volume ────────────────────────────────────────────────────
        elif intent == "set_volume":
            from modules.automation import set_volume
            level  = int(params.get("level", 50))
            result = set_volume(level)
            return {"response": f"Volume set to {level} percent.", "data": result}

        elif intent == "volume_up":
            from modules.automation import get_volume, set_volume
            current = get_volume()
            amount  = int(params.get("amount", 10))
            new_level = min(100, current.get("volume", 50) + amount)
            set_volume(new_level)
            return {"response": f"Volume increased to {new_level} percent.", "data": {"volume": new_level}}

        elif intent == "volume_down":
            from modules.automation import get_volume, set_volume
            current = get_volume()
            amount  = int(params.get("amount", 10))
            new_level = max(0, current.get("volume", 50) - amount)
            set_volume(new_level)
            return {"response": f"Volume decreased to {new_level} percent.", "data": {"volume": new_level}}

        elif intent == "mute":
            from modules.automation import mute_volume
            mute   = params.get("mute", True)
            result = mute_volume(mute)
            return {"response": "Muted." if mute else "Unmuted.", "data": result}

        # ── Type text ─────────────────────────────────────────────────
        elif intent == "type_text":
            from modules.automation import type_text
            text   = params.get("text", "")
            result = type_text(text)
            return {"response": f"Typing: {text}", "data": result}

        # ── Press key ─────────────────────────────────────────────────
        elif intent == "press_key":
            from modules.automation import press_key
            key    = params.get("key", "")
            result = press_key(key)
            return {"response": f"Pressed {key}.", "data": result}

        # ── Clipboard ─────────────────────────────────────────────────
        elif intent == "clipboard_read":
            from modules.automation import get_clipboard
            result = get_clipboard()
            content = result.get("content", "")
            if content:
                short = content[:100] + "..." if len(content) > 100 else content
                return {"response": f"Clipboard contains: {short}", "data": result}
            else:
                return {"response": "Clipboard is empty.", "data": result}

        elif intent == "clipboard_write":
            from modules.automation import set_clipboard
            text   = params.get("text", "")
            result = set_clipboard(text)
            return {"response": f"Copied to clipboard.", "data": result}

        # ── Run command ───────────────────────────────────────────────
        elif intent == "run_command":
            from modules.automation import run_command
            command = params.get("command", "")
            result  = run_command(command)
            output  = result.get("stdout", "")[:200]
            if result["success"]:
                resp = f"Command ran successfully. Output: {output}" if output else "Command completed."
            else:
                resp = f"Command failed: {result.get('stderr', result.get('error', ''))[:100]}"
            return {"response": resp, "data": result}

        # ── Web search ────────────────────────────────────────────────
        elif intent == "search_web":
            from modules.web_search import search_and_summarise
            query  = params.get("query", "")
            result = search_and_summarise(query, max_results=3)
            return {
                "response": result.get("summary", "No results found."),
                "data":     result,
                "type":     "search",
            }

        # ── File search ───────────────────────────────────────────────
        elif intent == "search_files":
            from modules.file_manager import search_files
            query   = params.get("query", "")
            results = search_files(query, max_results=5)
            if results:
                names = ", ".join([r["name"] for r in results[:3]])
                return {
                    "response": f"Found {len(results)} files. Top results: {names}",
                    "data":     {"results": results},
                    "type":     "file_search",
                }
            else:
                return {"response": f"No files found matching '{query}'.", "data": {}}

        # ── Create task ───────────────────────────────────────────────
        elif intent == "create_task":
            from modules.task_manager import create_task
            title    = params.get("title", "")
            priority = params.get("priority", "normal")
            task     = create_task(title=title, priority=priority)
            return {"response": f"Task created: {title}", "data": task}

        # ── Create note ───────────────────────────────────────────────
        elif intent == "create_note":
            from modules.notes import create_note
            content = params.get("content", "")
            title   = params.get("title", "")
            note    = create_note(content=content, title=title)
            return {"response": f"Note saved.", "data": note}
        
        elif intent == "set_reminder":
            from modules.reminders import parse_reminder_time, create_reminder
            text   = params.get("text", "")
            parsed = parse_reminder_time(text)
            result = create_reminder(
                title=parsed.get("title", text),
                remind_at=parsed.get("remind_at", "")
            )
            return {
                "response": f"Reminder set for {parsed.get('remind_at', 'soon')}.",
                "data": result
            }

        # ── Chat (default) ────────────────────────────────────────────
        else:
            from ai.ollama_client import ollama
            from routes.chat import get_bot_name
            bot_name = get_bot_name()
            message  = params.get("message", "")
            system   = (
                f"You are {bot_name}, a smart personal AI assistant. "
                f"Be concise and natural — this is a voice conversation."
            )
            msgs = [{"role": "system", "content": system}]
            if history:
                msgs.extend(history)
            msgs.append({"role": "user", "content": message})
            reply = ollama.chat(msgs)
            return {"response": reply, "data": {}, "type": "chat"}

    except Exception as e:
        logger.error(f"Intent execution failed: {e}")
        return {
            "response": f"Something went wrong: {str(e)}",
            "data":     {"error": str(e)}
        }