---
name: manifest-sync-job
description: Weekly blueprint to synchronize the dispenser manifest with the actual filesystem contents of all registered plugins. Use when manually asked to verify or update the manifest.
metadata:
  hermes:
    requires_tools: [wrench]
    blueprint:
      schedule: "0 0 * * 0" # Every Sunday at midnight
      deliver: origin
      prompt: "Run the manifest sync job: use the wrench tool to list all plugins, then for each plugin, run the wrench 'sync' action."
---

# Manifest Sync Job

This is a scheduled blueprint that ensures our `DISPENSER_MANIFEST.md` correctly matches the files inside each profile's dispenser plugin.

## When to Use
- Automatically triggered weekly via cron.
- Manually triggered if the user asks to "update the manifest", "sync the registry", or verify tools/skills are correctly tracked.

## Quick Reference
```python
# 1. Get all plugins
res = wrench({"action": "list"})
plugins = res["plugins"]

# 2. Sync each one
for p in plugins:
    # Extract profile from path if possible, or default to engineer
    wrench({"action": "sync", "name": p["name"]})
```

## Procedure
1. Call `wrench(action="list")` to get the current list of registered plugins.
2. Iterate through the returned list.
3. Call `wrench(action="sync", name="<plugin_name>")`.
4. Report completion.

## Verification
Read the `DISPENSER_MANIFEST.md` file or call `wrench(action="list")` to verify that newly added custom skills, tools, or hooks are now appearing correctly.