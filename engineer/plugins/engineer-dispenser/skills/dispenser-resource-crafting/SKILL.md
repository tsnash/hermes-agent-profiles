---
name: dispenser-resource-crafting
description: Procedures for crafting tools, hooks, and skills within a dispenser plugin.
metadata:
  hermes:
    requires_tools: [pda]
---

# Dispenser Resource Crafting

This skill defines the methodology for crafting new resources for a Hermes dispenser plugin using the `pda` tool.

## 1. Tool Crafting
Tools are functional units defined in `tools.py`.
- **Command**: `pda(resource='tool', action='create', profile='engineer', plugin_name='<plugin>', item_name='<name>', content='def <name>(args: dict, **kwargs) -> str:\n    ...')`
- **Verification**: `pda(resource='tool', action='list', ...)`

## 2. Hook Crafting
Hooks are lifecycle triggers defined in `__init__.py`.
- **Command**: `pda(resource='hook', action='create', profile='engineer', plugin_name='<plugin>', item_name='<name>', content='\ndef <name>(**kwargs):\n    ...')`
- **Verification**: `pda(resource='hook', action='list', ...)`

## 3. Skill Crafting
Skills are documentation artifacts in `skills/<name>/SKILL.md`.
- **Command**: `pda(resource='skill', action='create', profile='engineer', plugin_name='<plugin>', item_name='<name>', content='...')`
- **Verification**: `pda(resource='skill', action='list', ...)`
