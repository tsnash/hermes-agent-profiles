---
name: teleporter
description: "Guidelines and instructions for using the teleporter tool in background processes."
metadata:
  hermes:
    requires_tools: [teleporter]
---

# Teleporter

When running in background systems (like cronjobs, dispatchers, or Kanban tasks), standard chat clarification is impossible.

## When to use
Use `teleporter` whenever you hit a roadblock requiring user decision or when you need explicit confirmation to proceed on a high-stakes background task.

## Execution Pattern
1. Call `teleporter` with the `context_id` (e.g., Kanban task ID or cronjob name), a clear `question`, and `choices` (if applicable).
2. **Immediate Suspension**: After successfully firing the request, you MUST suspend the work.
   - If in Kanban: Call `kanban_block` on the task so it is parked.
   - If in Cron: End the current execution with a status summary (the user will reply to the thread/message to resolve it).

Do NOT wait synchronously. The tool call is a fire-and-forget broadcast. When the user replies, a new agent will be spawned to process their answer.