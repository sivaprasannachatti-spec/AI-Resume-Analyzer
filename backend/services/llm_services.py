import json
import logging
import os
import sys
from collections.abc import Callable
from typing import Any

from langchain_openai import ChatOpenAI
from config import (
    OPENROUTER_API_KEY_1,
    OPENROUTER_API_KEY_2,
    OPENROUTER_API_KEY_3,
    OPENROUTER_API_KEY_4,
    OPENROUTER_API_KEY_5,
    OPENROUTER_API_KEY_6,
    OPENROUTER_API_KEY_7,
    OPENROUTER_MODEL,
)

from src.exception import CustomException
from backend.prompts import (
    EXTRACT_KEYWORDS_PROMPT,
    PARSE_RESUME_PROMPT,
    RESUME_SCHEMA_EXAMPLE,
)
from backend.output_parsers import ResumeSchema

logger = logging.getLogger(__name__)


def _create_openrouter_model(api_key: str, max_tokens: int = 4096) -> ChatOpenAI:
    """Create an OpenRouter client for one configured API key."""
    try:
        return ChatOpenAI(
            model=OPENROUTER_MODEL,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise CustomException(e, sys)


def _extract_json_object(content: str) -> str:
    """Extract one JSON object from a model response without accepting arrays."""
    try:
        cleaned = content.strip()
        if cleaned.startswith("["):
            raise ValueError("LLM response must be a JSON object, not an array")
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].rstrip()

        start = cleaned.find("{")
        if start < 0:
            raise ValueError("LLM response did not contain a JSON object")

        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(cleaned)):
            character = cleaned[index]
            if escaped:
                escaped = False
                continue
            if character == "\\" and in_string:
                escaped = True
                continue
            if character == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return cleaned[start:index + 1]

        raise ValueError("LLM response contained an incomplete JSON object")
    except Exception as e:
        raise CustomException(e, sys)


def _response_text(response: Any) -> str:
    """Normalize LangChain message content into text for JSON parsing."""
    try:
        content = getattr(response, "content", response)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and isinstance(item.get("text"), str)
            ]
            return "".join(text_parts)
        raise ValueError("LLM response content was not text")
    except Exception as e:
        raise CustomException(e, sys)


def _summarize_json_for_logging(value: Any, key: str = "") -> Any:
    """Keep LLM diagnostics useful without logging personal resume content."""
    try:
        sensitive_keys = {
            "name",
            "email",
            "phone",
            "location",
            "address",
            "linkedin",
            "linkedin_url",
            "github",
            "github_url",
            "website",
            "portfolio_url",
            "resume_text",
        }
        if key.casefold() in sensitive_keys:
            return "[REDACTED]"
        if isinstance(value, dict):
            return {
                item_key: _summarize_json_for_logging(item_value, item_key)
                for item_key, item_value in value.items()
            }
        if isinstance(value, list):
            return [_summarize_json_for_logging(item, key) for item in value]
        if isinstance(value, str) and len(value) > 240:
            return f"{value[:240]}... [truncated]"
        return value
    except Exception as e:
        raise CustomException(e, sys)


async def complete_json(
    prompt: str,
    system_prompt: str | None = None,
    max_tokens: int = 4096,
    retries: int = 2,
    schema_type: str = "generic",
    response_validator: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Call OpenRouter and return a validated JSON object."""
    try:
        if not prompt.strip():
            raise ValueError("LLM prompt cannot be empty")
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero")
        if retries < 0:
            raise ValueError("retries cannot be negative")

        base_system_prompt = (
            (system_prompt or "").strip()
            + "\n\nReturn only one valid JSON object. Do not use Markdown or explanations."
        ).strip()
        configured_keys = [
            (index, key)
            for index, key in enumerate(
                (
                    OPENROUTER_API_KEY_1,
                    OPENROUTER_API_KEY_2,
                    OPENROUTER_API_KEY_3,
                    OPENROUTER_API_KEY_4,
                    OPENROUTER_API_KEY_5,
                    OPENROUTER_API_KEY_6,
                    OPENROUTER_API_KEY_7,
                ),
                start=1,
            )
            if key
        ]
        if not configured_keys:
            raise RuntimeError("At least one OPENROUTER_API_KEY_1-7 is required")

        last_error: Exception | None = None
        for key_number, api_key in configured_keys:
            model = _create_openrouter_model(
                api_key=api_key,
                max_tokens=max_tokens,
            ).bind(response_format={"type": "json_object"})

            for attempt in range(retries + 1):
                retry_hint = ""
                if attempt:
                    retry_hint = (
                        "\n\nYour previous response was invalid. Return a complete JSON "
                        f"object for the {schema_type} response and satisfy every required field."
                    )
                try:
                    response = await model.ainvoke(
                        [
                            ("system", base_system_prompt),
                            ("user", prompt + retry_hint),
                        ]
                    )
                except Exception as error:
                    last_error = error
                    logger.warning(
                        "OpenRouter request failed with configured key %d (%s); "
                        "trying the next configured key",
                        key_number,
                        type(error).__name__,
                    )
                    break

                try:
                    result = json.loads(_extract_json_object(_response_text(response)))
                    if not isinstance(result, dict):
                        raise ValueError("LLM response must be a JSON object")
                    logger.info(
                        "OpenRouter produced %s JSON on attempt %d/%d: %s",
                        schema_type,
                        attempt + 1,
                        retries + 1,
                        json.dumps(
                            _summarize_json_for_logging(result),
                            ensure_ascii=False,
                            default=str,
                        ),
                    )
                    if response_validator is not None:
                        try:
                            result = response_validator(result)
                        except Exception as validation_error:
                            logger.warning(
                                "OpenRouter %s JSON failed validation. Parsed values: %s",
                                schema_type,
                                json.dumps(
                                    _summarize_json_for_logging(result),
                                    ensure_ascii=False,
                                    default=str,
                                ),
                            )
                            raise validation_error
                        if not isinstance(result, dict):
                            raise ValueError("response_validator must return a JSON object")
                    return result
                except (CustomException, json.JSONDecodeError, TypeError, ValueError) as error:
                    last_error = error
                    logger.warning(
                        "OpenRouter returned invalid %s JSON on attempt %d/%d: %s",
                        schema_type,
                        attempt + 1,
                        retries + 1,
                        error,
                    )
            else:
                raise ValueError(
                    f"OpenRouter did not return valid {schema_type} JSON after "
                    f"{retries + 1} attempts"
                ) from last_error

        raise RuntimeError("All configured OpenRouter API keys failed") from last_error
    except Exception as e:
        raise CustomException(e, sys)


def _validate_resume_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize the complete structured resume payload."""
    try:
        return ResumeSchema.model_validate(result).model_dump()
    except Exception as e:
        raise CustomException(e, sys)


async def parse_resume_json(resume_text: str) -> dict[str, Any]:
    """Parse extracted resume text into the application's structured resume JSON."""
    try:
        if not isinstance(resume_text, str) or not resume_text.strip():
            raise ValueError("Resume text cannot be empty")

        prompt = PARSE_RESUME_PROMPT.format(
            schema=RESUME_SCHEMA_EXAMPLE,
            resume_text=resume_text,
        )
        return await complete_json(
            prompt=prompt,
            system_prompt=(
                "You are an expert resume parser. Extract only facts present in the "
                "provided resume. Do not invent skills, employers, dates, metrics, or "
                "achievements."
            ),
            max_tokens=8192,
            schema_type="resume",
            response_validator=_validate_resume_result,
        )
    except Exception as e:
        raise CustomException(e, sys)


async def parse_resume_to_json(resume_text: str) -> dict[str, Any]:
    """Backward-compatible alias for structured resume parsing."""
    try:
        return await parse_resume_json(resume_text)
    except Exception as e:
        raise CustomException(e, sys)
