"""Engineer Dispenser Plugin - Registration."""

import os
import json
import html
import httpx
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from . import schemas, tools

# Load env variables for profile configuration
PROFILES_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROFILES_DIR / ".env")

logger = logging.getLogger(__name__)

# Per-tool allow-lists: which parameters are safe to include in summaries and broadcasts
SAFE_ARGS_ALLOWLIST = {
    "wrench": {"action", "name"},  # Exclude: path, tools, hooks, skills (sensitive or verbose)
    "pda": {"resource", "action", "profile", "plugin_name"},  # Exclude: content, item_name
}

def _redact_args(tool_name: str, args: dict) -> dict:
    """Return only safe arguments for LLM prompt and broadcast based on per-tool allow-list."""
    allowlist = SAFE_ARGS_ALLOWLIST.get(tool_name, set())
    return {k: v for k, v in args.items() if k in allowlist}

async def _generate_tool_summary(ctx, tool_name: str, args: dict, result: str) -> str:
    try:
        # Redact sensitive arguments before building LLM prompt
        safe_args = _redact_args(tool_name, args)
        
        # Map tool name to its schema
        tool_schema = getattr(schemas, tool_name.upper(), {})
        
        prompt = (
            f"Write a single brief one-liner summarizing the execution of the tool '{tool_name}'.\n"
            f"Arguments provided: {json.dumps(safe_args, default=str)}\n"
            f"Tool Schema: {json.dumps(tool_schema, default=str)}\n\n"
            "Focus ONLY on the action and explicitly reference the parameters that were *required* for this specific action (infer this from the conditional logic in the Tool Schema). "
            "Do NOT detail or list the result string. Do NOT restate or include the name of the tool in your sentence, as it is already displayed in the message header."
        )
        response = await asyncio.to_thread(
            ctx.llm.complete,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            purpose="hooks.tool-broadcast-summary"
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed to generate summary for {tool_name}: {e}")
        return f"Tool {tool_name} executed."

def _escape_telegram_text(text: str) -> str:
    return html.escape(text, quote=False)


def _build_telegram_payload(chat_id: str, text: str, escape_html: bool = True) -> dict:
    safe_text = _escape_telegram_text(text) if escape_html else text
    return {
        "chat_id": chat_id,
        "text": safe_text,
        "parse_mode": "HTML",
    }


def _format_tool_broadcast_message(tool_name: str, summary: str) -> str:
    icon = "🔧" if tool_name == "wrench" else "📱"
    # Ensure tool name is safely escaped in HTML bold tags
    safe_tool_name = _escape_telegram_text(tool_name.capitalize())
    safe_summary = _escape_telegram_text(summary)
    return f"{icon} <b>{safe_tool_name}</b>\n{safe_summary}"


async def _broadcast_to_telegram(message: str):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_UPDATE_CHANNEL_ID")
    if not bot_token or not chat_id:
        logger.warning("Telegram credentials not found in environment, skipping broadcast.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = _build_telegram_payload(chat_id=chat_id, text=message, escape_html=False)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to broadcast to Telegram: {type(e).__name__} (URL sanitized)")


def _log_task_exception(task):
    try:
        task.result()
    except asyncio.CancelledError:
        logger.debug("Background broadcast task was cancelled.")
    except Exception:
        logger.exception("Background broadcast task failed.")


def register(ctx):
    """Register bundled skills, wire schemas to handlers, and register hooks."""
    skills_dir = Path(__file__).parent / "skills"
    if skills_dir.exists():
        for child in sorted(skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.exists():
                ctx.register_skill(child.name, skill_md)
    else:
        # Log warning or handle missing skills directory
        pass

    ctx.register_tool(name="wrench", toolset="engineer-tools", schema=schemas.WRENCH, handler=tools.wrench)
    ctx.register_tool(name="pda", toolset="engineer-tools", schema=schemas.PDA, handler=tools.pda)

    async def _on_post_tool_call_async(event_ctx, tool_name, args, result):
        if tool_name not in ["wrench", "pda"]:
            return
            
        summary = await _generate_tool_summary(event_ctx, tool_name, args, result)
        message = _format_tool_broadcast_message(tool_name, summary)
        await _broadcast_to_telegram(message)
        
    def _on_post_tool_call_sync(tool_name, args, result, task_id, **kwargs):
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(_on_post_tool_call_async(ctx, tool_name, args, result))
            task.add_done_callback(_log_task_exception)
        except RuntimeError:
            asyncio.run(_on_post_tool_call_async(ctx, tool_name, args, result))

    # This hook fires for ALL tool calls, not just ours
    ctx.register_hook("post_tool_call", _on_post_tool_call_sync)

