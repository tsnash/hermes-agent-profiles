# Skill manufacturing guidelines

## Objective

The info in this file should be used to put together a skill that would be used
to make skills for dispenser plugins (i.e. plugins that are related to a profile
that follow the naming convention PROFILE_NAME-dispenser). Typically the skills
created/edited/patched in this way should be related to operations that are 
within their dispenser plugin's toolset (i.e. it makes sense to put a skill
crafter in the engineer-dispenser because the pda tool could benefit directly
from using it when creating/editing/patching skills).

## The Workflow

### Creating Your Own Skill
Skills are just markdown files with YAML frontmatter. Creating one takes under five minutes.

#### Primary Method: Using the PDA Tool

Use the `pda` tool to automate skill creation. For detailed guidance, see the [dispenser-resource-crafting](../../dispenser-resource-crafting/SKILL.md) skill.
```python
pda({
    "resource": "skill",
    "action": "create",
    "profile": "PROFILE_NAME",
    "plugin_name": "PROFILE_NAME-dispenser",
    "item_name": "my-skill",
    "content": "---\nname: my-skill\ndescription: Brief description.\nmetadata:\n  hermes:\n    requires_tools: [pda]\n---\n\n# My Skill\n\n## When to Use\n...\n\n## Quick Reference\n...\n\n## Procedure\n...\n\n## Pitfalls\n...\n\n## Verification\n..."
})
```

This automatically creates the `~/.hermes/profiles/PROFILE_NAME/plugins/PROFILE_NAME-dispenser/skills/my-skill/SKILL.md` file.

#### Fallback Method: Manual File Creation (Offline)

If the pda tool is unavailable (e.g., offline editing), manually create the directory and files:

1. Create the Directory
`mkdir -p ~/.hermes/profiles/PROFILE_NAME/plugins/PLUGIN_NAME/skills/my-skill`

2. Write SKILL.md with concise instructions
`~/.hermes/profiles/PROFILE_NAME/plugins/PLUGIN_NAME/skills/my-skill/SKILL.md`

3. Add Reference Files (Optional - if content exceeds 500 lines)

4. Utility scripts (Optional - if deterministic operations needed)

Skills can include supporting files the agent loads on demand:
```markdown
my-skill/
├── SKILL.md                    # Main skill document
├── references/
│   ├── api-docs.md             # API reference the agent can consult
│   └── examples.md             # Example inputs/outputs
├── templates/
│   └── config.yaml             # Template files the agent can use
└── scripts/
    └── setup.sh                # Scripts the agent can execute
```
Reference these in your SKILL.md:

For API details, load the reference: `skill_view("my-skill", "references/api-docs.md")`

## Template/Format Rules

### SKILL.md Format
The minimal template is the baseline. This is the exhaustive version with optional features noted

```markdown
---
# Required fields
name: my-skill
description: Brief description (shown in skill search results)
metadata:
  hermes:
    # Minimal Hermes metadata
    #   Keep this block even when only the baseline skill metadata is needed

    # Common Optional Fields
    requires_toolsets: [web]            # Optional — only show when these toolsets are active
    requires_tools: [web_search]        # Optional — only show when these tools are available
    tags: [Category, Subcategory, Keywords]  # Optional — categorize the skill for discovery
    related_skills: [other-skill-name]

    # Advanced Optional Fields
    config:                              # Optional — config.yaml settings the skill needs
      - key: my.setting
        description: "What this setting controls"
        default: "sensible-default"
        prompt: "Display prompt for setup"

# Common Optional Fields
platforms: [macos, linux]          # Optional — restrict to specific OS platforms
                                   #   Valid: macos, linux, windows
                                   #   Omit to load on all platforms (default)

# Advanced Optional Fields
blueprint:                              # Optional — marks this skill a runnable automation
  schedule: "0 9 * * *"              #   cron expr / "every 2h" / ISO timestamp
  deliver: origin                    #   optional (default origin)
  prompt: "Task instruction for each run"  # optional
  no_agent: false                    # optional
required_environment_variables:          # Optional — env vars the skill needs
  - name: MY_API_KEY
    prompt: "Enter your API key"
    help: "Get one at https://example.com"
    required_for: "API access"
required_credential_files:               # Optional — credential files required by the skill
  - path: /path/to/credentials.json
    description: "Credentials file the skill needs"
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

### Format rules

1. Each dispenser skill should require its corresponding tool (i.e. skills that affect dispenser plugins, skills, tools, and hooks should require the pda tool)
                                       
3. Template/Format Rules: Any specific YAML frontmatter or Markdown headers     
(## Objective, ## Pitfalls, etc.) you strictly want every new skill to have.

### Description Requirements

The description is **the only thing your agent sees** when deciding which skill to load. It's surfaced in the system prompt alongside all other installed skills. Your agent reads these descriptions and picks the relevant skill based on the user's request.

**Goal**: Give your agent just enough info to know:

1. What capability this skill provides
2. When/why to trigger it (specific keywords, contexts, file types)

**Format**:

- Max 1024 chars
- Write in third person
- First sentence: what it does
- Second sentence: "Use when [specific triggers]"

**Good example**:

```
Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when user mentions PDFs, forms, or document extraction.
```

**Bad example**:

```
Helps with documents.
```

The bad example gives your agent no way to distinguish this from other document skills.

### When to Split Files

Split into separate files when:

- SKILL.md exceeds 100 lines
- Content has distinct domains (finance vs sales schemas)
- Advanced features are rarely needed

### Review Checklist

After drafting, verify:

- [ ] Description includes triggers ("Use when...")
- [ ] SKILL.md under 100 lines
- [ ] No time-sensitive info
- [ ] Consistent terminology
- [ ] Concrete examples included
- [ ] References one level deep

### Skill Guidelines

#### No External Dependencies
Prefer stdlib Python, curl, and existing Hermes tools (`web_extract`, `terminal`, `read_file`). If a dependency is needed, document installation steps in the skill.

#### Progressive Disclosure
Put the most common workflow first. Edge cases and advanced usage go at the bottom. This keeps token usage low for common tasks.

#### Include Helper Scripts
For XML/JSON parsing or complex logic, include helper scripts in `scripts/` — don't expect the LLM to write parsers inline every time.

#### Skill output and media delivery
When a skill response (or any agent response) includes a bare absolute path to a media file — for example `/home/user/screenshots/diagram.png` — the gateway auto-detects it, strips it from the visible text, and delivers the file natively to the user's chat (Telegram photo, Discord attachment, etc.) instead of leaving the raw path in the message.

For audio specifically, the `[[audio_as_voice]]` directive promotes audio files to native voice-message bubbles on platforms that support them (Telegram, WhatsApp).

Sometimes you want the **opposite** of inline preview: you want the file delivered as a downloadable attachment, not a re-compressed image bubble. The classic example is a high-resolution screenshot or chart — Telegram's `sendPhoto` recompresses it to ~200 KB at 1280 px, destroying readability. A 1-2 MB PNG sent via `sendDocument` keeps the original bytes intact.

If a response (or any text inside it — typically the last line) contains the literal directive `[[as_document]]`, every media path extracted from that response is delivered as a document/file attachment rather than an image bubble:
```
Here is your rendered chart:

/home/user/.hermes/cache/chart-q4-2025.png

[[as_document]]
```
If your skill produces a high-resolution screenshot, chart, or any image where lossy preview compression would hurt — emit the literal directive `[[as_document]]` somewhere in the response (commonly the last line). The gateway strips the directive and delivers every extracted media path in that response as a downloadable file attachment instead of an inline image bubble.

The directive is stripped before delivery, so users never see it. Granularity is intentionally all-or-nothing per response: emit `[[as_document]]` once and every image path in the same response is delivered as a document. This mirrors the scope of `[[audio_as_voice]]`.

Use it from a skill when:

- You produce screenshots or charts the user needs as files (for editing in another tool, archiving, sharing intact).
- The default lossy preview would obscure detail (small text, pixel-accurate diagrams, color-sensitive renders).

Platforms without a separate document path (e.g. SMS) fall back to whatever attachment mechanism they have.

#### Inline shell snippets (opt-in)
Skills can also embed inline shell snippets written as ``` !`cmd` ``` in the SKILL.md body. When enabled, each snippet's stdout is inlined into the message before the agent reads it, so skills can inject dynamic context:
```
Current date: !`date -u +%Y-%m-%d`
Git branch: !`git -C ${HERMES_SKILL_DIR} rev-parse --abbrev-ref HEAD`
```
This is **off by default** — any snippet in a SKILL.md runs on the host without approval, so only enable it for skill sources you trust:
```
# config.yaml
skills:
  inline_shell: true
  inline_shell_timeout: 10   # seconds per snippet
```
Snippets run with the skill directory as their working directory, and output is capped at 4000 characters. Failures (timeouts, non-zero exits) show up as a short `[inline-shell error: ...]` marker instead of breaking the whole skill.

## Examples/Snippets

### Platform-Specific Skills
Skills can restrict themselves to specific operating systems using the platforms field:

|Value|Matches|
|---|---|
|macos|macOS (Darwin)|
|linux|Linux|
|windows|Windows|
```
platforms: [macos]            # macOS only (e.g., iMessage, Apple Reminders, FindMy)
platforms: [macos, linux]     # macOS and Linux
```
When set, the skill is automatically hidden from the system prompt, skills_list(), and slash commands on incompatible platforms. If omitted, the skill loads on all platforms.

### Conditional Skill Activation
Skills can declare dependencies on specific tools or toolsets. This controls whether the skill appears in the system prompt for a given session.
```
metadata:
  hermes:
    requires_toolsets: [web]           # Hide if the web toolset is NOT active
    requires_tools: [web_search]       # Hide if web_search tool is NOT available
    fallback_for_toolsets: [browser]   # Hide if the browser toolset IS active
    fallback_for_tools: [browser_navigate]  # Hide if browser_navigate IS available
```
|Field|Behavior|
|---|---|
|requires_toolsets|Skill is **hidden** when ANY listed toolset is **not** available|
|requires_tools|Skill is **hidden** when ANY listed tool is **not** available|
|fallback_for_toolsets|Skill is **hidden** when ANY listed toolset **is** available|
|fallback_for_tools|Skill is **hidden** when ANY listed tool **is** available|

**Use case for fallback_for_\***: Create a skill that serves as a workaround when a primary tool isn't available. For example, a `duckduckgo-search` skill with `fallback_for_tools: [web_search]` only shows when the web search tool (which requires an API key) is not configured.

**Use case for requires_\***: Create a skill that only makes sense when certain tools are present. For example, a web scraping workflow skill with `requires_toolsets: [web]` won't clutter the prompt when web tools are disabled.

Skills without any conditional fields behave exactly as before — they're always shown.

### Environment Variable Requirements
Skills can declare environment variables they need. When a skill is loaded via skill_view, its required vars are automatically registered for passthrough into sandboxed execution environments (terminal, execute_code).
```
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: "Tenor API key"               # Shown when prompting user
    help: "Get your key at https://tenor.com"  # Help text or URL
    required_for: "GIF search functionality"   # What needs this var
```
Each entry supports:

- `name` (required) — the environment variable name
- `prompt` (optional) — prompt text when asking the user for the value
- `help` (optional) — help text or URL for obtaining the value
- `required_for` (optional) — describes which feature needs this variable

Users can also manually configure passthrough variables in `config.yaml`:
```
terminal:
  env_passthrough:
    - MY_CUSTOM_VAR
```

### Secure Setup on Load
Skills can declare `required environment variables` without disappearing from discovery:
```
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```
When a missing value is encountered, Hermes asks for it securely only when the skill is actually loaded in the local CLI. You can skip setup and keep using the skill. Messaging surfaces never ask for secrets in chat — they tell you to use `hermes setup` or `~/.hermes/.env` locally instead.

Once set, declared env vars are **automatically passed through** to `execute_code` and `terminal` sandboxes — the skill's scripts can use `$TENOR_API_KEY` directly. For non-skill env vars, use the `terminal.env_passthrough` config option. See Environment Variable Passthrough for details.

### Skill Config Settings
Skills can declare non-secret settings that are stored in `config.yaml` under the `skills.config` namespace. Unlike environment variables (which are secrets stored in `.env`), config settings are for paths, preferences, and other non-sensitive values.
```
metadata:
  hermes:
    config:
      - key: myplugin.path
        description: Path to the plugin data directory
        default: "~/myplugin-data"
        prompt: Plugin data directory path
      - key: myplugin.domain
        description: Domain the plugin operates on
        default: ""
        prompt: Plugin domain (e.g., AI/ML research)
```
Each entry supports:

- `key` (required) — dotpath for the setting (e.g., `myplugin.path`)
- `description` (required) — explains what the setting controls
- `default` (optional) — default value if the user doesn't configure it
- `prompt` (optional) — prompt text shown during `hermes config migrate`; falls back to `description`

**How it works:**

1. **Storage:** Values are written to `config.yaml` under `skills.config.<key>`:
```
skills:
  config:
    myplugin:
      path: ~/my-data
```
2. **Discovery:** `hermes config migrate` scans all enabled skills, finds unconfigured settings, and prompts the user. Settings also appear in `hermes config show` under "Skill Settings."

3. **Runtime injection:** When a skill loads, its config values are resolved and appended to the skill message:
```
[Skill config (from ~/.hermes/config.yaml):
  myplugin.path = /home/user/my-data
]
```
The agent sees the configured values without needing to read `config.yaml` itself.

4. **Manual setup:** Users can also set values directly:
```
hermes config set skills.config.myplugin.path ~/my-data
```
### Environment Variable Passthrough
Both `execute_code` and `terminal` strip sensitive environment variables from child processes to prevent credential exfiltration by LLM-generated code. However, skills that declare `required_environment_variables` legitimately need access to those vars.

#### How It Works
Two mechanisms allow specific variables through the sandbox filters:

**1. Skill-scoped passthrough (automatic)**

When a skill is loaded (via `skill_view` or the `/skill` command) and declares `required_environment_variables`, any of those vars that are actually set in the environment are automatically registered as passthrough. Missing vars (still in setup-needed state) are not registered.
```
# In a skill's SKILL.md frontmatter
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
```
After loading this skill, `TENOR_API_KEY` passes through to `execute_code`,` `terminal` (local), **and remote backends (Docker, Modal)** — no manual configuration needed.

##### *Docker & Modal*
Prior to v0.5.1, Docker's `forward_env` was a separate system from the skill passthrough. They are now merged — skill-declared env vars are automatically forwarded into Docker containers and Modal sandboxes without needing to add them to `docker_forward_env` manually.

**2. Config-based passthrough (manual)**

For env vars not declared by any skill, add them to `terminal.env_passthrough` in `config.yaml`:
```
terminal:
  env_passthrough:
    - MY_CUSTOM_KEY
    - ANOTHER_TOKEN
```
### When to use which
Use `required_environment_variables` for API keys, tokens, and other **secrets** (stored in `~/.hermes/.env`, never shown to the model). Use `config` for **paths, preferences, and non-sensitive settings** (stored in `config.yaml`, visible in config show).

### Credential File Passthrough (OAuth tokens, etc.)
Some skills need files (not just env vars) in the sandbox — for example, Google Workspace stores OAuth tokens as `google_token.json` under the active profile's `HERMES_HOME`. Skills declare these in frontmatter:
```
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials
```
When loaded, Hermes checks if these files exist in the active profile's ``HERMES_HOME` and registers them for mounting:

Docker: Read-only bind mounts (`-v host:container:ro`)`
Modal: Mounted at sandbox creation + synced before each command (handles mid-session OAuth setup)
Local: No action needed (files already accessible)
You can also list credential files manually in `config.yaml`:
```
terminal:
  credential_files:
    - google_token.json
    - my_custom_oauth_token.json
```
Paths are relative to `~/.hermes/`. Files are mounted to `/root/.hermes/` inside the container. This list is read by `tools/credential_files.py` (`terminal.credential_files`) — it lives under the `terminal:` block but is loaded by the credential-files module, not the core terminal backend, so it isn't part of the bundled `DEFAULT_CONFIG` snapshot.

### What Each Sandbox Filters
|Sandbox|Default Filter|Passthrough Override|
|---|---|---|
|**execute_code**|Blocks vars containing `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL`, `PASSWD`, `AUTH` in name; only allows safe-prefix vars through|✅ Passthrough vars bypass both checks|
|**terminal** (local)|Blocks explicit Hermes infrastructure vars (provider keys, gateway tokens, tool API keys)|✅ Passthrough vars bypass the blocklist|
|**terminal** (Docker)|BlocksNo host env vars by default|✅ Passthrough vars + ``docker_forward_env` forwarded via `-e`|
|**terminal** (Modal)|No host env/files by default|✅ Credential files mounted; env passthrough via sync|
|**MCP	Blocks**|everything except safe system vars + explicitly configured `env`|❌ Not affected by passthrough (use MCP `env` config instead)|

### Blueprints: skills that are also automations
A **blueprint** is an ordinary skill that additionally declares a schedule in its frontmatter. Add a `metadata.hermes.blueprint` block and the skill becomes a shareable, runnable automation:
```
metadata:
  hermes:
    tags: [blueprint, email]
    blueprint:
      schedule: "0 8 * * *"     # presence of `blueprint:` marks it runnable
      deliver: telegram          # optional (default: origin)
      prompt: "Summarize my unread email and today's calendar."  # optional
      no_agent: false            # optional
```
Because a blueprint **is** a skill, it flows through the entire skills pipeline unchanged — search, inspect, install, security scan, provenance, taps, the centralized index, and `hermes skills publish` for sharing. Nothing new to learn.

**Installing a blueprint**. When you install a skill that carries a `blueprint:` block, Hermes registers it as a **suggested cron job** rather than scheduling it. Scheduling is **opt-in** — installing never silently creates a recurring job. You review and accept it via `/suggestions`:
```
hermes skills install owner/morning-brief
# → Blueprint: 'morning-brief' is an automation (schedule 0 8 * * *).
#   Added to your suggestions — run /suggestions to schedule or dismiss it.

# then, in a session:
/suggestions             # lists pending suggestions, numbered
/suggestions accept 1    # creates the cron job
/suggestions dismiss 1   # never offer it again
```
Blueprints are one **source** of the unified Suggested Cron Jobs surface — the same place curated starter automations and (later) usage-pattern and integration suggestions appear. See Suggested Cron Jobs below.

The blueprint layer adds no new object type, store, or transport — the blueprint is a skill, the schedule is a cron job, and sharing is the existing publish/tap/index path.

### Suggested Cron Jobs
Hermes can *propose* automations and let you accept them with one tap, instead of making you assemble cron jobs by hand. Every proposal flows through one surface — the `/suggestions` command — regardless of where it came from:

|Source|Trigger|
|---|---|
|`catalog`|Curated starter automations (`/suggestions catalog`) — daily briefing, important-mail monitor, weekly review, workday-start reminder|
|`blueprint`|You installed a skill carrying a blueprint: block|
|`usage`|The background review noticed a recurring ask a schedule would serve|
|`integration`|	You connected an account (Gmail, GitHub, ...) and the obvious automations are offered|
```
/suggestions             # list pending
/suggestions accept N    # schedule suggestion N (creates the cron job)
/suggestions dismiss N   # dismiss it — latched, never re-offered
/suggestions catalog     # add the curated starter automations
```
Accepting a suggestion calls the same `cron.jobs.create_job` the `cronjob` tool uses — there is no second job engine. Suggestions never auto-create jobs; acceptance is always explicit. Dismissed suggestions latch by a stable key so the same proposal is never re-offered. The pending list is capped so it never becomes a nag wall.

The **important-mail monitor** catalog entry is the poll→classify→surface pattern: it scores inbox items with a cheap classifier model (`auxiliary.monitor` in `config.yaml`) and delivers only the ones above an urgency threshold, staying silent otherwise.

### Bundle skills
Plugins can ship skill files that the agent loads via `skill_view("plugin:skill")`. Register them in your `__init__.py`:
```
~/.hermes/profiles/PROFILE_NAME/plugins/PLUGIN_NAME/skills/my-skill
├── __init__.py
├── plugin.yaml
└── skills/
    ├── my-workflow/
    │   └── SKILL.md
    └── my-checklist/
        └── SKILL.md
```
```
from pathlib import Path

def register(ctx):
    skills_dir = Path(__file__).parent / "skills"
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            ctx.register_skill(child.name, skill_md)
```
The agent can now load your skills with their namespaced name:
```
skill_view("my-plugin:my-workflow")   # → plugin's version
skill_view("my-workflow")              # → built-in version (unchanged)
```
Key properties:

Plugin skills are **read-only** — they don't enter `~/.hermes/skills/` and can't be edited via `skill_manage`.
Plugin skills are **not** listed in the system prompt's `<available_skills>` index — they're opt-in explicit loads.
Bare skill names are unaffected — the namespace prevents collisions with built-in skills.
When the agent loads a plugin skill, a bundle context banner is prepended listing sibling skills from the same plugin.

### Security Considerations
- The passthrough only affects vars you or your skills explicitly declare — the default security posture is unchanged for arbitrary LLM-generated code
- Credential files are mounted read-only into Docker containers
- Skills Guard scans skill content for suspicious env access patterns before installation
- Missing/unset vars are never registered (you can't leak what doesn't exist)
- Hermes infrastructure secrets (provider API keys, gateway tokens) should never be added to env_passthrough — they have dedicated mechanisms
