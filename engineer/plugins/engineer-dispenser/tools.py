import json
import os
import re
import shutil
import ast
import textwrap
import yaml
from pathlib import Path

# Try to import registry and schemas if available
try:
    from tools.registry import registry
except ImportError:
    registry = None
    
try:
    from .schemas import WRENCH, PDA
except ImportError:
    pass

# We removed dotenv from top-level to resolve environment errors during script execution
# as stated in memory.
PROFILES_DIR = os.getenv("HERMES_PROFILES_DIR", str(Path("~/.hermes/profiles").expanduser()))
MANIFEST_PATH = Path(PROFILES_DIR) / "engineer/metadata/DISPENSER_MANIFEST.md"

def check_manifest():
    return MANIFEST_PATH.exists()

def wrench(args: dict, **kwargs) -> str:
    """
    Used to maintain the dispenser manifest that tracks which profiles have which plugins, tools, and skills.
    Supported actions: list, register, remove, edit, sync
    """
    try:
        action = args.get("action", "list")
        
        content = MANIFEST_PATH.read_text()
        match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
        if not match:
            return json.dumps({"success": False, "error": "No plugin data found in manifest."})
            
        json_str = match.group(1).replace("${HERMES_PROFILES_DIR}", str(PROFILES_DIR))
        data = json.loads(json_str)
        plugins = data.get("plugins", [])

        if action == "list":
            return json.dumps({"success": True, "plugins": plugins})

        elif action == "register":
            name = args.get("name")
            if not name: return json.dumps({"success": False, "error": "Name required"})
            plugins.append({
                "name": name,
                "path": args.get("path", ""),
                "tools": args.get("tools", []),
                "hooks": args.get("hooks", []),
                "skills": args.get("skills", []),
                "status": "active"
            })
            
        elif action == "remove":
            name = args.get("name")
            plugins = [p for p in plugins if p["name"] != name]
            
        elif action == "edit":
            name = args.get("name")
            permitted_fields = {"path", "tools", "hooks", "skills"}
            for p in plugins:
                if p["name"] == name:
                    p.update({k: v for k, v in args.items() if k in permitted_fields})

        elif action == "sync":
            target_name = args.get("name")
            target_profile = args.get("profile", "engineer")
            plugin_entry = next((p for p in plugins if p["name"] == target_name), None)
            if not plugin_entry:
                return json.dumps({"success": False, "error": f"Plugin {target_name} not found in manifest."})
            
            plugin_dir = Path(PROFILES_DIR) / target_profile / "plugins" / target_name
            
            # Tools
            tools_file = plugin_dir / "tools.py"
            tools_list = []
            if tools_file.exists():
                try:
                    tree = ast.parse(tools_file.read_text())
                    tools_list = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and any(arg.arg == 'args' for arg in node.args.args)]
                except (SyntaxError, TypeError):
                    tools_list = []
                
            # Hooks
            init_file = plugin_dir / "__init__.py"
            hooks_list = []
            if init_file.exists():
                try:
                    tree = ast.parse(init_file.read_text())
                    hooks_list = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                    if "register" in hooks_list:
                        hooks_list.remove("register")
                except (SyntaxError, TypeError):
                    hooks_list = []
                
            # Skills
            skill_dir = plugin_dir / "skills"
            skills_list = []
            if skill_dir.exists():
                for s in skill_dir.iterdir():
                    if s.is_dir() and (s / "SKILL.md").exists():
                        skill_text = (s / "SKILL.md").read_text()
                        associated = []
                        try:
                            frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", skill_text, re.DOTALL)
                            parsed = yaml.safe_load(frontmatter_match.group(1)) if frontmatter_match else {}
                            if isinstance(parsed, dict) and "requires_tools" in parsed:
                                requires_tools = parsed["requires_tools"]
                                if isinstance(requires_tools, list):
                                    associated = requires_tools
                                elif isinstance(requires_tools, str):
                                    associated = [requires_tools]
                        except (yaml.YAMLError, AttributeError):
                            associated = []
                        skills_list.append({
                            "name": s.name,
                            "associated_tools": [t for t in associated if t]
                        })
                        
            plugin_entry["tools"] = tools_list
            plugin_entry["hooks"] = hooks_list
            plugin_entry["skills"] = skills_list

        else:
            return json.dumps({"success": False, "error": f"Action {action} not implemented."})

        # Save back
        data["plugins"] = plugins
        new_json = json.dumps(data, indent=2).replace(str(PROFILES_DIR), "${HERMES_PROFILES_DIR}")
        new_content = content.replace(match.group(1), new_json, 1)
        MANIFEST_PATH.write_text(new_content)
        
        return json.dumps({"success": True, "action": action})

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def _write_plugin_file(plugin_dir: Path, rel_path: str, content: str) -> bool:
    """Writes content to a file inside the sandboxed plugin directory."""
    file_path = plugin_dir / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    return True

def _get_sandboxed_plugin_path(profile: str, plugin_name: str) -> Path:
    """Ensure operations are strictly confined to the profile's plugin directory."""
    if not profile or not plugin_name:
        raise ValueError("Profile and plugin_name are required.")
    
    # Prevent directory traversal
    if ".." in profile or ".." in plugin_name or "/" in plugin_name:
        raise ValueError("Invalid profile or plugin name.")

    target_dir = Path(PROFILES_DIR) / profile / "plugins" / plugin_name
    
    # Resolve and ensure it sits within the profiles root
    resolved_profiles_dir = Path(PROFILES_DIR).resolve()
    resolved_target = target_dir.resolve()
    if not str(resolved_target).startswith(str(resolved_profiles_dir)):
        raise ValueError("Path traversal attempt blocked.")

    return target_dir

def _is_full_function_definition(src: str, item_name: str) -> bool:
    try:
        parsed = ast.parse(src)
    except SyntaxError:
        return False

    if len(parsed.body) != 1:
        return False

    node = parsed.body[0]
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == item_name

def _surgical_edit(file_path: Path, item_name: str, new_content: str):
    content = file_path.read_text()

    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        raise ValueError(f"Failed to parse {file_path}: {exc}") from exc

    target_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == item_name:
            if target_node is None or (node.lineno, node.col_offset) < (target_node.lineno, target_node.col_offset):
                target_node = node

    if target_node is None:
        raise ValueError(f"Function {item_name} not found in {file_path}")

    decorator_lines = []
    for decorator in target_node.decorator_list:
        decorator_source = ast.unparse(decorator).lstrip("@")
        decorator_indent = max(decorator.col_offset - 1, 0)
        decorator_lines.append(f"{' ' * decorator_indent}@{decorator_source}")

    start_lineno = min((decorator.lineno for decorator in target_node.decorator_list), default=target_node.lineno)
    start_col_offset = min((max(decorator.col_offset - 1, 0) for decorator in target_node.decorator_list), default=target_node.col_offset)
    end_lineno = target_node.end_lineno
    end_col_offset = target_node.end_col_offset

    line_starts = [0]
    for line in content.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))

    start_idx = line_starts[start_lineno - 1] + start_col_offset
    end_idx = line_starts[end_lineno - 1] + end_col_offset

    body_text = new_content.rstrip("\n")
    if not body_text.strip():
        body_text = "pass"

    if _is_full_function_definition(body_text, item_name):
        replacement = body_text
    else:
        header_indent = " " * target_node.col_offset
        body_indent = " " * (target_node.col_offset + 4)
        header = f"{header_indent}{'async ' if isinstance(target_node, ast.AsyncFunctionDef) else ''}def {item_name}"
        if file_path.name == "tools.py":
            header += "(args: dict, **kwargs) -> str:"
        else:
            header += "(**kwargs):"

        body_lines = textwrap.indent(body_text, body_indent).splitlines()
        replacement_lines = decorator_lines + [header] + body_lines
        replacement = "\n".join(replacement_lines)

    file_path.write_text(content[:start_idx] + replacement + content[end_idx:])

def _surgical_remove(file_path: Path, item_name: str):
    if not file_path.exists():
        return
    content = file_path.read_text()
    pattern = re.compile(rf"\ndef {item_name}\(.*?\):.*?(?=\n\n|\Z)", re.DOTALL)
    new_file_content = pattern.sub("", content)
    file_path.write_text(new_file_content)

def _handle_plugin_list(plugin_dir, args):
    return json.dumps({"success": True, "plugins": [p.name for p in Path(PROFILES_DIR).glob("*/plugins/*")]})

def _handle_plugin_remove(plugin_dir, args):
    if not plugin_dir.exists():
         return json.dumps({"success": False, "error": "Plugin does not exist."})

    plugin_name = args.get("plugin_name")
    backup_dir = plugin_dir.parent / f".{plugin_name}.backup"

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    try:
        shutil.move(str(plugin_dir), str(backup_dir))
    except Exception as exc:
        return json.dumps({"success": False, "error": f"Failed to move plugin directory before manifest update: {exc}"})

    try:
        manifest_result = wrench({"action": "remove", "name": plugin_name})
        manifest_payload = json.loads(manifest_result)
        if not manifest_payload.get("success"):
            shutil.move(str(backup_dir), str(plugin_dir))
            return json.dumps({"success": False, "error": manifest_payload.get("error", "Failed to update manifest.")})
    except Exception as exc:
        if backup_dir.exists():
            shutil.move(str(backup_dir), str(plugin_dir))
        return json.dumps({"success": False, "error": f"Failed to update manifest while removing plugin: {exc}"})

    try:
        shutil.rmtree(backup_dir)
    except Exception as exc:
        return json.dumps({"success": False, "error": f"Plugin removed from manifest but failed to clean up backup directory: {exc}"})

    return json.dumps({"success": True, "message": "Plugin removed."})

def _handle_tool_list(plugin_dir, args):
    tools_file = plugin_dir / "tools.py"
    if not tools_file.exists(): return json.dumps({"success": True, "tools": []})
    content = tools_file.read_text()
    tools = re.findall(r"def (\w+)\(args: dict", content)
    return json.dumps({"success": True, "tools": tools})

def _handle_tool_edit(plugin_dir, args):
    item_name = args.get("item_name")
    content = args.get("content")
    if not item_name or not content:
        return json.dumps({"success": False, "error": "item_name and content required for edit"})
    _surgical_edit(plugin_dir / "tools.py", item_name, content)
    wrench({"action": "sync", "name": args.get("plugin_name"), "profile": args.get("profile")})
    return json.dumps({"success": True, "message": f"Tool {item_name} edited"})

def _handle_tool_remove(plugin_dir, args):
    item_name = args.get("item_name")
    if not item_name:
        return json.dumps({"success": False, "error": "item_name required"})
    _surgical_remove(plugin_dir / "tools.py", item_name)
    wrench({"action": "sync", "name": args.get("plugin_name"), "profile": args.get("profile")})
    return json.dumps({"success": True, "message": f"Tool {item_name} removed"})

def _handle_tool_evaluate(plugin_dir, args):
    content = args.get("content")
    if not content: return json.dumps({"success": False, "error": "Content required."})
    try:
        ast.parse(content)
        return json.dumps({"success": True, "message": "Syntax is valid."})
    except SyntaxError as e:
        return json.dumps({"success": False, "error": f"Syntax error: {e}"})

def _handle_hook_list(plugin_dir, args):
    init_file = plugin_dir / "__init__.py"
    if not init_file.exists(): return json.dumps({"success": True, "hooks": []})
    content = init_file.read_text()
    hooks = re.findall(r"def (\w+)\(", content)
    return json.dumps({"success": True, "hooks": hooks})

def _handle_hook_edit(plugin_dir, args):
    item_name = args.get("item_name")
    content = args.get("content")
    if not item_name or not content:
        return json.dumps({"success": False, "error": "item_name and content required for edit"})
    _surgical_edit(plugin_dir / "__init__.py", item_name, content)
    wrench({"action": "sync", "name": args.get("plugin_name"), "profile": args.get("profile")})
    return json.dumps({"success": True, "message": f"Hook {item_name} edited"})

def _handle_hook_remove(plugin_dir, args):
    item_name = args.get("item_name")
    if not item_name:
        return json.dumps({"success": False, "error": "item_name required"})
    _surgical_remove(plugin_dir / "__init__.py", item_name)
    wrench({"action": "sync", "name": args.get("plugin_name"), "profile": args.get("profile")})
    return json.dumps({"success": True, "message": f"Hook {item_name} removed"})

def _handle_hook_evaluate(plugin_dir, args):
    content = args.get("content")
    if not content: return json.dumps({"success": False, "error": "Content required."})
    try:
        ast.parse(content)
        return json.dumps({"success": True, "message": "Syntax is valid."})
    except SyntaxError as e:
        return json.dumps({"success": False, "error": f"Syntax error: {e}"})

def _handle_skill_list(plugin_dir, args):
    skills_dir = plugin_dir / "skills"
    if not skills_dir.exists() or not skills_dir.is_dir():
        return json.dumps({"success": True, "skills": []})
    skills = [d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    return json.dumps({"success": True, "skills": sorted(skills)})

def _handle_skill_edit(plugin_dir, args):
    item_name = args.get("item_name")
    content = args.get("content")
    if not item_name or not content:
        return json.dumps({"success": False, "error": "item_name and content required for edit"})
    skill_file = plugin_dir / f"skills/{item_name}/SKILL.md"
    if not skill_file.exists():
        return json.dumps({"success": False, "error": f"Skill {item_name} does not exist."})
    skill_file.write_text(content)
    wrench({"action": "sync", "name": args.get("plugin_name"), "profile": args.get("profile")})
    return json.dumps({"success": True, "message": f"Skill {item_name} updated"})

def _handle_skill_remove(plugin_dir, args):
    item_name = args.get("item_name")
    if not item_name:
        return json.dumps({"success": False, "error": "item_name required"})
    skill_dir = plugin_dir / f"skills/{item_name}"
    if not skill_dir.exists():
        return json.dumps({"success": False, "error": f"Skill {item_name} does not exist."})
    try:
        shutil.rmtree(skill_dir)
        wrench({"action": "sync", "name": args.get("plugin_name"), "profile": args.get("profile")})
        return json.dumps({"success": True, "message": f"Skill {item_name} removed"})
    except Exception as e:
        return json.dumps({"success": False, "error": f"Failed to remove skill: {e}"})

def _handle_skill_evaluate(plugin_dir, args):
    content = args.get("content")
    if not content:
        return json.dumps({"success": False, "error": "Content required."})
    errors = []
    if not content.startswith("---"): errors.append("Missing YAML frontmatter.")
    if "# " not in content: errors.append("Missing top-level heading.")
    if errors: return json.dumps({"success": False, "error": "Validation failed.", "details": errors})
    return json.dumps({"success": True, "message": "Skill structure appears valid."})

def pda(args: dict, **kwargs) -> str:
    """
    Builds and modifies skills, tools, and hooks within dispenser plugins.
    """
    try:
        action = args.get("action")
        profile = args.get("profile")
        plugin_name = args.get("plugin_name")
        resource = args.get("resource")
        
        if not action or not profile or not plugin_name:
            return json.dumps({"success": False, "error": "Missing required arguments: action, profile, plugin_name"})

        try:
            plugin_dir = _get_sandboxed_plugin_path(profile, plugin_name)
        except ValueError as e:
            return json.dumps({"success": False, "error": str(e)})

        # Route by resource/action pattern
        if resource == "plugin" and action == "create":
            if plugin_dir.exists(): return json.dumps({"success": False, "error": f"Plugin {plugin_name} already exists."})
            plugin_dir.mkdir(parents=True, exist_ok=True)
            (plugin_dir / "skills").mkdir(exist_ok=True)
            (plugin_dir / "plugin.yaml").write_text(f"name: {plugin_name}\nversion: 0.1.0\ndescription: Dispenser plugin for {profile}\n")
            (plugin_dir / "__init__.py").write_text('def register(ctx):\n    pass\n')
            wrench({"action": "register", "name": plugin_name, "path": f"${{HERMES_PROFILES_DIR}}/{profile}/plugins/{plugin_name}"})
            return json.dumps({"success": True, "message": f"Plugin {plugin_name} scaffolded"})
        
        elif resource == "tool" and action == "create":
            item_name = args.get("item_name")
            if not item_name: return json.dumps({"success": False, "error": "item_name required"})
            tools_file = plugin_dir / "tools.py"
            if not tools_file.exists():
                tools_file.write_text("import json\n\n")
            else:
                tools_content = tools_file.read_text()
                if "import json" not in tools_content:
                    tools_file.write_text("import json\n" + tools_content)
            content = args.get("content", f"def {item_name}(args: dict, **kwargs) -> str:\n    return json.dumps({{'success': True, 'msg': 'Placeholder'}})")
            with open(tools_file, "a") as f: f.write(f"\n{content}\n")
            wrench({"action": "sync", "name": plugin_name, "profile": profile})
            return json.dumps({"success": True, "message": f"Tool {item_name} added"})
        elif resource == "tool" and action == "list": return _handle_tool_list(plugin_dir, args)
        elif resource == "tool" and action == "edit": return _handle_tool_edit(plugin_dir, args)
        elif resource == "tool" and action == "remove": return _handle_tool_remove(plugin_dir, args)
        elif resource == "tool" and action == "evaluate": return _handle_tool_evaluate(plugin_dir, args)

        elif resource == "hook" and action == "create":
            item_name = args.get("item_name")
            if not item_name: return json.dumps({"success": False, "error": "item_name required"})
            init_file = plugin_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("def register(ctx):\n    pass\n\n")
            init_content = init_file.read_text()
            if ("json." in init_content or "json(" in init_content) and "import json" not in init_content and "from json" not in init_content:
                init_file.write_text("import json\n" + init_content)
            content = args.get("content", f"\ndef {item_name}(**kwargs):\n    pass\n")
            with open(init_file, "a") as f: f.write(f"\n{content}\n")
            wrench({"action": "sync", "name": plugin_name, "profile": profile})
            return json.dumps({"success": True, "message": f"Hook {item_name} added"})
        elif resource == "hook" and action == "list": return _handle_hook_list(plugin_dir, args)
        elif resource == "hook" and action == "edit": return _handle_hook_edit(plugin_dir, args)
        elif resource == "hook" and action == "remove": return _handle_hook_remove(plugin_dir, args)
        elif resource == "hook" and action == "evaluate": return _handle_hook_evaluate(plugin_dir, args)

        elif resource == "skill" and action == "create":
            item_name = args.get("item_name")
            if not item_name: return json.dumps({"success": False, "error": "item_name required"})
            _write_plugin_file(plugin_dir, f"skills/{item_name}/SKILL.md", args.get("content", "# New Skill"))
            wrench({"action": "sync", "name": plugin_name, "profile": profile})
            return json.dumps({"success": True, "message": f"Skill {item_name} added"})
        elif resource == "skill" and action == "list": return _handle_skill_list(plugin_dir, args)
        elif resource == "skill" and action == "edit": return _handle_skill_edit(plugin_dir, args)
        elif resource == "skill" and action == "remove": return _handle_skill_remove(plugin_dir, args)
        elif resource == "skill" and action == "evaluate": return _handle_skill_evaluate(plugin_dir, args)

        else:
            return json.dumps({"success": False, "error": f"Unknown resource '{resource}' or action '{action}'"})

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def teleporter(args: dict, **kwargs) -> str:
    """
    Sends a clarification request asynchronously via a Teleporter to the Home channel.
    """
    import urllib.request
    import urllib.error
    
    context_id = args.get("context_id")
    question = args.get("question")
    choices = args.get("choices", [])

    if context_id in (None, "") or question in (None, ""):
        return json.dumps({
            "success": False,
            "error": "Missing required arguments: context_id, question"
        })

    context_id = str(context_id)
    question = str(question)
    choices = [str(c) for c in (choices or [])]
    
    profile_dir = Path(PROFILES_DIR) / "engineer"
    env_path = profile_dir / ".env"
    
    bot_token = None
    chat_id = None
    
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    bot_token = line.split("=", 1)[1].strip().strip('"\'')
                elif line.startswith("TELEGRAM_HOME_CHANNEL="):
                    chat_id = line.split("=", 1)[1].strip().strip('"\'')
                    
    if not bot_token or not chat_id:
        return json.dumps({
            "success": False,
            "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_HOME_CHANNEL in profile .env"
        })
        
    # Send plain text (no Markdown parsing) and ensure interpolated
    # fragments are simple strings. This avoids Telegram parsing errors
    # when content contains control characters or unexpected markup.
    msg = f"🔧 Teleporter Clarification Request\nContext: {context_id}\n\n{question}"
    if choices:
        msg += "\n\nOptions:\n"
        for idx, c in enumerate(choices, 1):
            msg += f"{idx}. {c}\n"
            
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    # No parse_mode: send as plain text to avoid parse failures.
    payload = {
        "chat_id": chat_id,
        "text": msg,
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.getcode() == 200:
                return json.dumps({
                    "success": True,
                    "message": "Clarification teleported successfully. You should now suspend your work."
                })
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Failed with status {resp.getcode()}"
                })
    except urllib.error.URLError as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })

