WRENCH = {
    "name": "wrench",
    "description": (
        "Maintain dispenser manifest for plugins, tools, and skills. "
        "Use this tool to list registered plugins, register new ones, remove them, "
        "or edit their properties in the manifest."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "register", "remove", "edit", "sync"],
                "description": "The action to perform on the manifest. 'sync' updates a plugin's entry based on its files."
            },
            "name": {
                "type": "string",
                "description": "The name of the plugin (required for register, remove, edit, and sync)."
            },
            "path": {
                "type": "string",
                "description": "The filesystem path to the plugin directory (required for register/edit)."
            },
            "tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of tool names provided by the plugin."
            },
            "hooks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of hook names provided by the plugin."
            },
            "skills": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "associated_tools": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "description": "A list of skills provided by the plugin."
            }
        },
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "action": {"const": "list"}
                },
                "required": ["action"]
            },
            {
                "type": "object",
                "properties": {
                    "action": {"const": "register"}
                },
                "required": ["action", "name", "path"]
            },
            {
                "type": "object",
                "properties": {
                    "action": {"const": "remove"}
                },
                "required": ["action", "name"]
            },
            {
                "type": "object",
                "properties": {
                    "action": {"const": "edit"}
                },
                "required": ["action", "name", "path"]
            },
            {
                "type": "object",
                "properties": {
                    "action": {"const": "sync"}
                },
                "required": ["action", "name"]
            }
        ]
    }
}


PDA = {
    "name": "pda",
    "description": (
        "Builds and modifies skills, tools, and hooks within profile-restricted dispenser plugins. "
        "Strictly sandboxed to the active profile's plugin directory."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "resource": {
                "type": "string",
                "enum": ["plugin", "tool", "hook", "skill"],
                "description": "The type of dispenser resource to manage."
            },
            "action": {
                "type": "string",
                "enum": ["create", "edit", "remove", "list", "evaluate"],
                "description": "The lifecycle action to perform."
            },
            "profile": {
                "type": "string",
                "description": "The target Hermes profile."
            },
            "plugin_name": {
                "type": "string",
                "description": "The name of the dispenser plugin."
            },
            "item_name": {
                "type": "string",
                "description": "Name of the tool, hook, or skill to manage. Required for create/edit/remove actions on tool, hook, and skill resources."
            },
            "content": {
                "type": "string",
                "description": "Content for the target resource. Required for edit/evaluate actions on tool, hook, and skill resources."
            }
        },
        "required": ["resource", "action", "profile", "plugin_name"],
        "allOf": [
            {
                "if": {
                    "properties": {
                        "resource": {"enum": ["tool", "hook", "skill"]},
                        "action": {"enum": ["create", "edit", "remove"]}
                    },
                    "required": ["resource", "action"]
                },
                "then": {
                    "required": ["item_name"]
                }
            },
            {
                "if": {
                    "properties": {
                        "resource": {"enum": ["tool", "hook", "skill"]},
                        "action": {"enum": ["edit", "evaluate"]}
                    },
                    "required": ["resource", "action"]
                },
                "then": {
                    "required": ["content"]
                }
            }
        ]
    }
}

TELEPORTER = {
    "name": "teleporter",
    "description": "Send a clarification request asynchronously via a Teleporter to the Home channel. Use this when you are in a background task (e.g. cron/kanban) and need user input. After using this, suspend your work.",
    "parameters": {
        "type": "object",
        "properties": {
            "context_id": {
                "type": "string",
                "description": "Task ID, job name, or context reference (e.g. 'Task 102')."
            },
            "question": {
                "type": "string",
                "description": "The clarification question."
            },
            "choices": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of choices for the user to select from."
            }
        },
        "required": ["context_id", "question"]
    }
}

