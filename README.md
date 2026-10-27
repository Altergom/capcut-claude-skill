# CapCut skill for Claude Code

English | [简体中文](README.zh-CN.md)

A [Claude Code](https://claude.com/claude-code) skill that lets Claude edit **CapCut (剪映国际版) cloud drafts** through CapCut's official MCP server: upload local media, build and edit drafts (clips, music, sound effects, text, captions, filters, transitions, text templates), search materials and templates, run automatic captions, AI rough cuts, and AI image/video generation.

CapCut published its MCP plugin for OpenAI Codex. This skill adapts it to Claude: how to connect, which parts of the Codex workflow don't apply, and the real-world boundaries found by testing (what the cloud keeps or drops, push pitfalls, account/login behaviour).

> Unofficial. Not affiliated with CapCut or ByteDance. CapCut's own plugin files are **not** included here; `scripts/fetch_official.py` downloads them from CapCut's CDN.

## Install

Requirements: Claude desktop app (Windows or macOS), Python 3.8+, Node.js 14+ (for `npx` and the official uploader), a CapCut account (Pro needed for automatic captions; AI generation spends credits).

```bash
git clone https://github.com/Altergom/capcut-claude-skill ~/.claude/skills/capcut
python ~/.claude/skills/capcut/scripts/fetch_official.py
```

Then open a Claude Code session and say something like "connect CapCut and run a test". The skill walks Claude through the rest; you only sign in to CapCut in your browser and restart Claude once.

### Connection (summary)

CapCut must be added as **local MCP servers via `mcp-remote`** in `claude_desktop_config.json`. Adding it as a claude.ai custom connector does not work: CapCut's OAuth server rejects the registration.

```json
"capcut":          {"command": "cmd", "args": ["/c", "npx", "-y", "mcp-remote", "https://www.capcut.com/api/external_mcp"]},
"capcut_resource": {"command": "cmd", "args": ["/c", "npx", "-y", "mcp-remote", "https://www.capcut.com/api/external_mcp/resource"]}
```

(On macOS use `"command": "npx", "args": ["-y", "mcp-remote", "<url>"]`.)

## Layout

| Path | What |
| --- | --- |
| `SKILL.md` | The skill: connection, workflow, verified boundaries and pitfalls |
| `scripts/draft_tool.py` | Validate / slim a draft for pushing / summarise server read-backs / extract editor links |
| `scripts/fetch_official.py` | Downloads the official CapCut plugin bundle into `official/` (git-ignored) |
| `official/` | Created by the fetch script: CapCut's skill docs, STDraft builder, Node uploader |

## Known limits (verified)

- Video effects / face effects are dropped when a draft is saved to the cloud.
- Keyframes on speed-changed clips are rescaled and mostly dropped.
- Automatic captions are speech recognition — useless for song lyrics.
- Fonts, text effects, text templates, transitions, filters and face effects come from a fixed curated list.
- Interactive cards are not rendered in the Code tab; Claude shows the data as text instead.
- Export happens in the CapCut web editor; the MCP has no export call.

## License

MIT for the files in this repository (`SKILL.md`, `README.md`, `README.zh-CN.md`, `scripts/`). CapCut's plugin material fetched into `official/` remains CapCut's and is subject to its own terms.
