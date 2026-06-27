"""Engineer Dispenser Plugin - Registration."""

from . import schemas, tools
from pathlib import Path
    

def _on_post_tool_call(tool_name, args, result, task_id, **kwargs):
    """Hook: runs after every tool call (not just ours)."""
    if (tool_name == "wrench"):
        # Handle wrench tool post-call logic here
        pass
    elif (tool_name == "pda"):
        # Handle pda tool post-call logic here
        pass
    pass

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

    # This hook fires for ALL tool calls, not just ours
    ctx.register_hook("post_tool_call", _on_post_tool_call)