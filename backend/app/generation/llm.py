from dataclasses import dataclass, field

import instructor
import litellm

from app.config import getSettings
from app.generation.schemas import GenBatch

litellm.suppress_debug_info = True

# nazwy dostawcow w LiteLLM
PREFIX = {
    "openrouter": "openrouter",
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "gemini",
    "lmstudio": "lm_studio",
}


@dataclass
class CallResult:
    batch: GenBatch
    raw: dict
    tokensIn: int = 0
    tokensOut: int = 0
    retries: int = 0
    cost: float | None = None
    actualProvider: str | None = None
    extra: dict = field(default_factory=dict)


# jedno wywolanie modelu z wymuszonym schematem odpowiedzi (Instructor ponawia przy blednym JSON)
async def callModel(
    provider: str, model: str, apiKey: str | None, messages: list[dict], temperature: float
) -> CallResult:
    # LM Studio przyjmuje tylko response_format typu json_schema (tryb JSON_SCHEMA w Instructorze)
    mode = instructor.Mode.JSON_SCHEMA if provider == "lmstudio" else instructor.Mode.TOOLS
    client = instructor.from_litellm(litellm.acompletion, mode=mode)
    errors = []
    client.on("parse:error", lambda e: errors.append(str(e)[:200]))

    extra = {"api_key": apiKey} if apiKey else {}
    if provider == "lmstudio":
        extra = {"api_base": getSettings().lmstudioBaseUrl, "api_key": "lm-studio"}

    batch, completion = await client.chat.completions.create_with_completion(
        model=f"{PREFIX[provider]}/{model}",
        messages=messages,
        response_model=GenBatch,
        max_retries=2,
        temperature=temperature,
        max_tokens=6000,
        **extra,
    )
    usage = getattr(completion, "usage", None)
    try:
        cost = litellm.completion_cost(completion_response=completion)
    except Exception:
        cost = None
    return CallResult(
        batch=batch,
        raw=batch.model_dump(),
        tokensIn=getattr(usage, "prompt_tokens", 0) or 0,
        tokensOut=getattr(usage, "completion_tokens", 0) or 0,
        retries=len(errors),
        cost=cost or None,
        # OpenRouter zwraca, ktory dostawca faktycznie odpowiedzial (wazne w badaniach)
        actualProvider=getattr(completion, "provider", None),
    )
