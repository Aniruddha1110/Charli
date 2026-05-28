# routes/code.py — Code assistant endpoints

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ai.ollama_client import ollama
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/code", tags=["Code"])


class CodeRequest(BaseModel):
    action:   str
    code:     Optional[str] = ""
    prompt:   Optional[str] = ""
    language: Optional[str] = "python"


class CodeResponse(BaseModel):
    result:   str
    language: str
    action:   str


def build_prompt(action: str, code: str, prompt: str, language: str) -> str:

    base = f"You are an expert {language} developer and coding assistant."

    if action == "write":
        return f"""{base}
Write clean, well-commented {language} code for the following requirement.
Include brief inline comments explaining key parts.
Return ONLY the code, no explanation before or after.
Wrap the code in ```{language} ``` blocks.

Requirement: {prompt}"""

    elif action == "debug":
        return f"""{base}
Debug the following {language} code. Find all bugs and fix them.
Explain what was wrong briefly, then provide the fixed code.
Wrap fixed code in ```{language} ``` blocks.

Code to debug:
````````````{language}
{code}
````````````

Issue description: {prompt if prompt else "Find and fix all bugs"}"""

    elif action == "explain":
        return f"""{base}
Explain the following {language} code clearly and concisely.
Break it down line by line or section by section.
Use simple language, avoid jargon.

Code:
````````````{language}
{code}
```````````"""

    elif action == "review":
        return f"""{base}
Review the following {language} code professionally.
Check for:
- Bugs and potential errors
- Performance issues
- Security vulnerabilities
- Code style and best practices
- Suggestions for improvement

Provide specific, actionable feedback.

Code:
``````````{language}
{code}
`````````"""

    elif action == "optimize":
        return f"""{base}
Optimize the following {language} code for better performance and readability.
Explain what you changed and why.
Return the optimized code in ```{language} ``` blocks.

Code:
````````{language}
{code}
```````"""

    elif action == "complete":
        return f"""{base}
Complete the following {language} code. Continue from where it left off.
Return ONLY the completed full code in ```{language} ``` blocks.

Code:
``````{language}
{code}
``````

Additional context: {prompt if prompt else "Complete the code logically"}"""

    elif action == "convert":
        return f"""{base}
Convert the following code to {language}.
Maintain the same logic and functionality.
Return ONLY the converted code in ```{language} ``` blocks.

Code to convert:
```````
{code}
```````"""

    elif action == "test":
        return f"""{base}
Write comprehensive unit tests for the following {language} code.
Use the appropriate testing framework for {language}.
Return ONLY the test code in ```{language} ``` blocks.

Code to test:
``````{language}
{code}
`````"""

    else:
        return f"""{base}
{prompt}

Code:
````{language}
{code}
```"""


@router.post("/", response_model=CodeResponse)
async def code_assistant(request: CodeRequest):
    logger.info(
        f"Code request — action: {request.action} "
        f"language: {request.language} "
        f"code_len: {len(request.code or '')}"
    )

    prompt = build_prompt(
        action=request.action,
        code=request.code or "",
        prompt=request.prompt or "",
        language=request.language or "python",
    )

    result = ollama.prompt(prompt)

    return CodeResponse(
        result=result,
        language=request.language or "python",
        action=request.action,
    )


@router.get("/languages")
async def get_languages():
    return {
        "languages": [
            "python", "javascript", "typescript", "java", "c",
            "cpp", "csharp", "go", "rust", "php", "ruby",
            "swift", "kotlin", "html", "css", "sql",
            "bash", "powershell", "r", "matlab",
        ]
    }