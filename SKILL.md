---
name: capcut
description: Use for any CapCut / 剪映 work from Claude through the CapCut MCP — uploading local media, building or editing CapCut cloud drafts (video clips, music, sound effects, text, captions, filters, transitions, text templates), material/template search, automatic captions, AI rough cuts (AI Lab), AI image/video generation, and fixing the CapCut MCP connection or login. Adapts the official CapCut Codex plugin to Claude; read before the first CapCut tool call.
---

# CapCut from Claude

The CapCut MCP was built for Codex. This skill is the Claude adaptation: the official material is kept verbatim under `official/` (plugin v0.2.6), and this file states how to use it here, plus what was verified in real use (2026-10-26/27, Claude desktop Code tab, Windows).

Paths below are relative to this skill's folder (`~/.claude/skills/capcut/`).

If `official/` is missing (fresh clone), run `python scripts/fetch_official.py` first — it downloads CapCut's plugin bundle from CapCut's CDN (the official material is not redistributed in this repo). `--force` refreshes it to the latest published version.

## 0. Connection (do this first if tools are missing or failing)

The only working way to connect is **local MCP servers in the Claude desktop config, via `mcp-remote`**. Adding CapCut as a claude.ai custom connector does NOT work: CapCut's OAuth server rejects Claude's dynamic client registration ("无法在 CapCut 的登录服务中注册"), and a client ID cannot be supplied.

`%LOCALAPPDATA%\Claude-Data\<profile>\claude_desktop_config.json` (or `%APPDATA%\Claude\claude_desktop_config.json`) → `mcpServers`:

```json
"capcut":          {"command": "cmd", "args": ["/c", "npx", "-y", "mcp-remote", "https://www.capcut.com/api/external_mcp"]},
"capcut_resource": {"command": "cmd", "args": ["/c", "npx", "-y", "mcp-remote", "https://www.capcut.com/api/external_mcp/resource"]}
```

- `capcut` = account-bound tools (OAuth). `capcut_resource` = identity-free card tools (no login). Back up the config before editing; the user must fully quit and reopen Claude after editing.

**Setup from scratch** (no `mcp__capcut__*` tools in the session):
1. Check prerequisites: `node --version` (≥14) and `npx` on PATH.
2. Find the live config: search `%LOCALAPPDATA%\Claude-Data\*\claude_desktop_config.json` first, then `%APPDATA%\Claude\claude_desktop_config.json`. Read it, copy it to `claude_desktop_config.json.bak-<date>`, add the two entries under `mcpServers` (create the key if absent) without touching anything else, and re-parse the file as JSON to confirm it's valid.
3. Ask the user to sign the **system default browser** into the CapCut account the drafts should live in, then fully quit Claude (tray icon → Quit) and reopen it.
4. On start, mcp-remote opens the CapCut authorize page in that browser; the user approves (an instant flash-and-close means it auto-approved — fine).
5. The current session cannot see servers added after it started: continue in a **new** Code-tab session. Verify there with `start_stdraft_session` (should return a `session_id`) and `search_capcut_material` (`type: music`).
6. Optional: sign Claude's built-in browser into the same CapCut account so drafts can be inspected there.
- OAuth tokens are cached in `~/.mcp-auth/mcp-remote-v1/<hash>_tokens.json` and `<hash>_client_info.json`.
- **Re-authorize / switch account**: ask the user first; delete those two files; the user signs the *system default browser* into the desired CapCut account (same login method — Google/email/TikTok are different accounts) *before* restarting; then fully quit and reopen Claude; mcp-remote opens the CapCut authorize page (it may flash and close if that browser is already signed in — that is success). Verify with `start_stdraft_session`.
- Symptom `get user workspace failed: check login error` on every call = the cached grant is dead → re-authorize as above.
- Re-authorizing logs the same account out of other CapCut web sessions (including Claude's built-in browser); the user must sign in there again.
- Drafts are saved into **whichever account the MCP is authorized as**. If the user can't see a draft, compare accounts first.

## 1. Which surface works

| Surface | Status |
| --- | --- |
| Claude desktop **Code tab** session | Everything below works. Use this for CapCut work. |
| Phone remote-controlling a Code-tab session | Same as Code tab (tools run on the PC). |
| Desktop **Chat** / phone chat reaching the PC tools | Draft tools fail with "missing session_id" (the bridge appears to drop a parameter literally named `session_id`); cards may not show. Don't do draft editing there. |
| Phone chat on its own | No CapCut at all (servers are local to the PC). |

Cards (`capcut_resource`: templates_preview_v2, editing_plan, video_preview, background_music, billing_confirmation) are fetched but **not rendered** in the Code tab — results arrive as text/JSON. Never wait on a card; read the data and present it yourself.

## 2. Official docs to read (only what the task needs)

Must-read for any draft work: `official/capcut-stdraft-builder/reference/application.md` (function contracts). Everything else only when the task touches it.

| Task | Read |
| --- | --- |
| Rough-cut handoff or captions on an existing video | `official/video-editing/references/post-editing.md` |
| Session/version/push/conflicts | `official/web-collaborative-editing/SKILL.official.md` (+ `references/conflict-recovery.md`) |
| Field-level protocol questions | `official/capcut-stdraft-builder/reference/STDraft_Protocol.md`, `validation.md` |
| Materials | `official/video-editing/references/materials.md` |
| Captions | `official/video-editing/references/auto-captions.md` |
| AI rough cut | `official/video-editing/references/ai-rough-cut.md` |
| Image/video generation | `official/generate-media/SKILL.official.md` + `references/` |
| Template search | `official/search-templates/SKILL.official.md` |

Ignore Codex-only parts: `codex plugin` install/upgrade, `codex app-server`/`capcut-login.mjs` OAuth, "New-Task Handoff"/fork, `require_escalated` sandbox flags, TTY ticket entry, "end the turn silently after a card".

## 3. Core workflow: build/edit a cloud draft

Shell: run commands in the **Bash tool** (Git Bash), not PowerShell. Use forward-slash Windows paths (`D:/proj/clip.mp4`) or single-quoted ones. Work in the user's project folder (e.g. `<project>/capcut_work/`) so upload maps and drafts survive the session.

1. **Upload local media** with the official uploader only (never hand-rolled VOD code):
   - `capcut_asset_upload_credential` with `version: 2` and `files: [{file_name, size_bytes}]` for the whole batch → `upload_ticket` (a short-lived single-batch capability; it necessarily passes through this conversation once — never log it elsewhere).
   - Write the ticket with no trailing-newline issues, pipe it on stdin (never in argv), delete the file:
     ```bash
     cd <project>/capcut_work && printf '%s\n' '<ticket>' > ticket.tmp
     node ~/.claude/skills/capcut/official/capcut-upload/scripts/capcut-upload.mjs \
       --files '[{"client_id":"c1","file":"D:/proj/a.mp4"},{"client_id":"c2","file":"D:/proj/b.mp3"}]' \
       --upload-ticket-stdin --json < ticket.tmp > upload_result.json 2> upload_stderr.txt; rm -f ticket.tmp
     ```
     (single file: `--file <path> --client-id c1`; progress → stderr, JSON → stdout.)
   - Success = non-empty `vid` **and** `setPublic.success:true`. Save a `name → {vid, duration}` map (`upload_map.json`); never re-upload items that already have a vid. Tickets expire in ~1 h.
2. **Session**: `start_stdraft_session` once per draft; keep `session_id`. Before each edit round call `check_stdraft_state(session_id, local_package_id)`:
   - brand-new draft: pass `""`; expect `server_package_id:""` → build from scratch and push with `base_package_id:""`;
   - otherwise follow the baseline table in `official/web-collaborative-editing/SKILL.official.md` (stale → `get_stdraft_snapshot` first).
3. **Build locally** with the official atomic functions (Python ≥3.8, stdlib only, run with `python -B`, `sys.path.insert(0, "C:/Users/<user>/.claude/skills/capcut/official/capcut-stdraft-builder/scripts")`): `apply_video`, `apply_audio`, `apply_text`, `apply_text_template`, `apply_captions`, `apply_video_effect`, `apply_filter`, `apply_transition`, `update_material`, `update_placement`, `update_caption_text`, `remove_material`, `unset_attribute`. Chain `result["draft"]`. New draft root: `{"version":"0.1.0","segments":[{"id":"draft","type":"DRAFT","attributes":{"width":1920,"height":1080,"ratio_type":"16:9"}}]}`.
   - Mute a clip: `apply_video(..., volume=0.0)`. Times are integer ms.
   - `SOURCE_RANGE_UNVERIFIED` is raised for every vid/sid source — expected. Check it yourself: `source_start_ms + duration_ms × speed` must not exceed the source length (from `upload_map.json`, or `duration_ms` in the music search result).
   - Picking search results: prefer an item whose `duration_ms` covers the needed length and whose title/caption fits the mood; say which one you chose.
4. **Prepare the push**: `python -B ~/.claude/skills/capcut/scripts/draft_tool.py slim draft.json draft_slim.json` (short ids, one segment per line, re-validated, warns over ~60k chars). Read `draft_slim.json` and paste its full text verbatim as `stdraft_json` in `push_stdraft_snapshot` (this costs its size in tokens twice — keep drafts lean).
5. **After push**: if the result was saved to a file by the harness, run `draft_tool.py summary <file>` / `urls <file>`; if it came back inline, save it to `push_result.json` first (or pipe it: `... summary -`). Give the user `web_editor_url` as a Markdown link labelled with `web_editor_text` verbatim (server-localized, may be e.g. "Buksan sa CapCut"). Use the returned `stdraft_json`/`server_package_id` as the next baseline.
   - Normal server rewrites (not errors): `vid://` → `asset://<id>`; DRAFT gets a random id and loses `ratio_type`; layers are renumbered; `end.ms` is added everywhere; TEXT gets `font_color`/`line_max_width` and a `PATCH` child ("style copy"); VIDEO gets `crop`/`background.*` defaults; AUDIO `meta_type` becomes lowercase. Compare content, timing, volume, speed, transitions and keyframes — not ids or layer numbers.
6. Optionally open `embed_editor_url` in the built-in browser to look; it only works if that browser is signed into the same CapCut account. Large projects take 30–60 s to load; text may only draw after a segment is selected.

### Push pitfalls (verified)
- **Timeout ≠ failure.** First push into a new account copies every media file and can exceed the client timeout while still succeeding. Never blindly re-push: `check_stdraft_state` first; if a version now exists, `get_stdraft_snapshot` (summarise via draft_tool) and continue from it. A blind re-push returns `STDRAFT_VERSION_CONFLICT`.
- A draft created by a timed-out push may not show in the Library and returns no URL; one more push on top of it (same content, correct base) returns the editor URLs.
- Size: ~55k chars pushed reliably; ~90k did not fit in one call. Keep pushes lean (drop optional keyframes/styles, add them in the web editor).

## 4. Verified capability boundaries

Works and survives cloud save: video clips (source in-point, duration, volume, speed), transitions (add/replace/remove; same layer, contiguous), music & sound effects (`sid://` from search or own `vid://`; volume; no auto-loop), filters with intensity, plain text (font, size, colour, position, border), font swap, text effects (`flower`), text templates (server adds an IN animation; slot count unverifiable), captions with word timing and `update_caption_text`, remove/unset, placement/layer/timing changes, `scale_*`/`alpha` keyframes **on clips with speed 1**.

Lost or broken on save:
- `VIDEO_EFFECT` segments (video effects and face effects) are **dropped entirely** — tell the user to add effects in the web editor.
- Keyframes on clips whose `speed ≠ 1` get their times rescaled by the speed and are mostly dropped.
- Anything the builder doesn't cover (masks, stickers, curves, grading) must be done in the web editor.
- Export/render is not available through the MCP: the user exports in the CapCut editor.

Materials search: `music`, `sound_effect`, `video_effect` honour the prompt; `font`, `text_effect`, `text_template`, `face_effect`, `transition`, `filter` return a **fixed curated list** (max 20) regardless of prompt — there is no plain cross-dissolve; curated fonts are Latin (Chinese falls back to the default font `vimo://7317175475195875841`, which renders CJK). Video footage/images are not searchable — upload them.

Automatic captions (`auto_caption_submit` / `auto_caption_query`): speech recognition only; Pro membership needed (free accounts get `PAYWALL_REQUIRED` — show `benefit_check_label` link verbatim). **Useless for song lyrics** (a whole song returned one garbage line) — use local Whisper + known lyrics for lyric timing instead.

Template search: `capcut_template_search` → poll `capcut_template_search_poll_v2` until terminal → `templates_preview_v2(search_id)` returns the template data (card not rendered; list title, duration, usage and `page_url` for the user). Relevance is loose; results persist 15 days; max 10.

AI rough cut (AI Lab): `capcut_ailab_start_edit(assets=[{resource_id: <vid>, file_name}], query)` → poll → a plan event arrives with status `loop_turn_completed`; relay the plan to the user, then `capcut_ailab_submit_plan_response` **without `card_id`** (the plan's event id is rejected as `plan_card_id_invalid`) and with the user's exact choice text. Music and final-video events follow (~2 min for a 10 s cut). Call `video_preview` with the final event's `context`/`resources` unchanged to get the result's **editable STDraft** (`stdraft` field) — import it into a draft session to keep editing. Audio-only assets are rejected (`unsupported_edit_file_name`). Do not use AI Lab for caption-only requests.

Image/video generation (Seedream / Seedance): spends credits. Cards don't render here, so: submit with `confirmed:false` (no `unique_key`) → on `CONFIRMATION_REQUIRED` tell the user the exact `credits_amount` → only after the user explicitly approves that amount in chat, retry with `confirmed:true` and the returned `unique_key`/same `generate_id`. Never confirm on the user's behalf. Poll `capcut_generation_poll` until `next_action=none`, then `generation_result(task_id)` and report `actual_credits`. (Not yet exercised end-to-end.)

## 5. Delivery rules

- Every successful push: summarise what changed and what the server dropped, then end with the `web_editor_url` link.
- State unverified things as unverified (e.g. "preview not checked visually").
- Keep upload maps, draft JSON and helper outputs in the project folder, not only in a temp dir, so later sessions can continue.
- Leftover test drafts live in the user's CapCut Library; mention them so the user can delete them.
