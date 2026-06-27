---
name: dispenser-skill-crafter
description: Create and format new skills for dispenser plugins using the PDA tool. Use when the user asks to create a skill for a profile's dispenser plugin.
metadata:
  hermes:
    requires_tools: [pda]
---

# Dispenser Skill Crafter

This skill provides the standard operating procedure and templates for fabricating new skills inside dispenser plugins using the `pda` tool. 

**Full Guidelines**: To read the exhaustive underlying guidelines, call `skill_view("engineer-dispenser:dispenser-skill-crafter", "references/docs.md")`.

## When to Use
Use when the user requests the creation of a new skill for a specific profile's dispenser plugin (e.g., `scout-dispenser`, `medic-dispenser`).

## Quick Reference
To create a skill using the PDA:
```python
pda({
    "resource": "skill",
    "action": "create",
    "profile": "<target_profile>",
    "plugin_name": "<target_profile>-dispenser",
    "item_name": "<skill-name>",
    "content": "<full_skill_md_content_including_frontmatter>"
})
```

## Procedure

1. **Understand the Goal**: Identify the target profile, plugin name, and the core workflow the skill will automate.
2. **Draft the Frontmatter**: Adhere strictly to the required YAML structure.
    - `name`: Lowercase, hyphenated.
    - `description`: Max 1024 chars, written in the 3rd person. First sentence explains what it does. Second sentence is "Use when [triggers]".
    - `metadata.hermes.requires_tools`: Include the primary tools the skill relies on. For dispenser-centric operations, this is usually `[pda]`.
3. **Draft the Body**: Always use the required structural headers: `## When to Use`, `## Quick Reference`, `## Procedure`, `## Pitfalls`, and `## Verification`.
4. **Deploy**: Use the `pda` tool to deploy the skill in a single step, passing the full markdown text into the `content` parameter.

## Template/Format Rules

Every skill generated MUST follow this exact structure:

```markdown
---
name: my-skill
description: Brief description. Use when [trigger conditions].
metadata:
  hermes:
    requires_tools: [pda] # or other dependencies
---

# Skill Title

Brief intro.

## When to Use
Trigger conditions — when should the agent load this skill?

## Quick Reference
Table of common commands or API calls.

## Procedure
Step-by-step instructions the agent follows.

## Pitfalls
Known failure modes and how to handle them.

## Verification
How the agent confirms it worked.
```

- **Keep it concise**: Try to keep SKILL.md under 100 lines. Focus on the core workflow.
- **Progressive Disclosure**: Put the most common workflow first.

## Pitfalls
- **Poor Descriptions**: The description is the *only* thing the agent sees during discovery. "Helps with documents" is bad. "Extracts text from PDFs. Use when working with PDF files." is good.
- **Forgetting Tool Dependencies**: Every skill targeting a dispenser MUST require its corresponding tool (`requires_tools: [pda]`) when the skill truly depends on that tool being available. Use `requires_tools` for skills that need a tool to be present, and use `fallback_for_tools` for skills that are optional fallbacks and should be hidden when the tool is already available. See [references/docs.md](references/docs.md) for the full semantics of both mechanisms.
- **Invalid YAML**: Watch out for special characters in the YAML description; use quotes if necessary.

## Verification
1. After creating the skill, verify it exists by calling `pda` with `resource="skill"` and `action="list"`.
2. Ensure the output confirms the new skill name is listed.