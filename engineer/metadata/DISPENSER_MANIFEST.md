# DISPENSER_MANIFEST.md

This manifest tracks the dispenser plugins (tools, skills, and hooks) assigned to each agent profile.

## Maintenance
- **Maintainer**: engineer profile
- **Update Frequency**: Every addition, removal, or modification of dispenser plugin capabilities.

## Registered Plugins
```json
{
  "plugins": [
    {
      "name": "engineer-dispenser",
      "path": "${HERMES_PROFILES_DIR}/engineer/plugins/engineer-dispenser",
      "tools": [
        "wrench",
        "pda"
      ],
      "hooks": [
        "_on_post_tool_call"
      ],
      "skills": [
        {
          "name": "manifest-sync-job",
          "associated_tools": [
            "wrench"
          ]
        },
        {
          "name": "dispenser-skill-crafter",
          "associated_tools": [
            "pda"
          ]
        },
        {
          "name": "dispenser-resource-crafting",
          "associated_tools": []
        }
      ],
      "status": "active"
    }
  ]
}
```
