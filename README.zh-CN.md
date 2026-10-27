# 适用于 Claude Code 的 CapCut 技能

[English](README.md) | 简体中文

这是一个 [Claude Code](https://claude.com/claude-code) 技能，让 Claude 能通过 CapCut 官方的 MCP 服务编辑 **CapCut（剪映国际版）云端草稿**。它可以上传本地素材，创建和编辑草稿（片段、音乐、音效、文字、字幕、滤镜、转场、文字模板），搜索素材和模板，也能做自动字幕、AI 粗剪，以及 AI 生图、生视频。

CapCut 发布的 MCP 插件是给 OpenAI Codex 用的。本技能把它适配到 Claude，内容包括：怎么连接；Codex 流程里哪些部分在这里不适用；以及实测发现的实际边界（云端保存时哪些会保留、哪些会丢，推送时的坑，账号和登录的行为）。

> 非官方项目，与 CapCut 和字节跳动无关。本仓库**不包含** CapCut 自己的插件文件，由 `scripts/fetch_official.py` 从 CapCut 的 CDN 下载。

## 安装

要求：Claude 桌面版（Windows 或 macOS）、Python 3.8+、Node.js 14+（`npx` 和官方上传器要用到）、一个 CapCut 账号。自动字幕需要 Pro 会员；AI 生成会消耗积分。

```bash
git clone https://github.com/Altergom/capcut-claude-skill ~/.claude/skills/capcut
python ~/.claude/skills/capcut/scripts/fetch_official.py
```

然后打开一个 Claude Code 会话，说一句类似"帮我接入 CapCut 并测试一下"的话，技能会带着 Claude 完成剩下的步骤。你只需要在浏览器里登录一次 CapCut，再重启一次 Claude。

### 连接方式（概要）

CapCut 必须在 `claude_desktop_config.json` 里**通过 `mcp-remote` 添加为本地 MCP 服务**。把它添加成 claude.ai 的自定义连接器是行不通的：CapCut 的 OAuth 服务会拒绝注册。

```json
"capcut":          {"command": "cmd", "args": ["/c", "npx", "-y", "mcp-remote", "https://www.capcut.com/api/external_mcp"]},
"capcut_resource": {"command": "cmd", "args": ["/c", "npx", "-y", "mcp-remote", "https://www.capcut.com/api/external_mcp/resource"]}
```

（macOS 上写成 `"command": "npx", "args": ["-y", "mcp-remote", "<url>"]`。）

## 目录结构

| 路径 | 内容 |
| --- | --- |
| `SKILL.md` | 技能本体：连接方式、工作流、已验证的边界和坑 |
| `scripts/draft_tool.py` | 校验草稿、精简推送内容、汇总服务器回读结果、提取编辑器链接 |
| `scripts/fetch_official.py` | 把 CapCut 官方插件包下载到 `official/`（该目录被 git 忽略） |
| `official/` | 由下载脚本生成：CapCut 的技能文档、STDraft 构建脚本、Node 上传器 |

## 已知限制（已验证）

- 草稿保存到云端时，视频特效、人物特效会被丢掉。
- 变速片段上的关键帧会被按速度缩放，而且大部分会丢失。
- 自动字幕是语音识别，对歌曲歌词无效。
- 字体、花字、文字模板、转场、滤镜和人物特效都只有一份固定的精选列表。
- 交互卡片在 Code 标签页里不会显示，Claude 会改为用文字展示数据。
- 导出要在 CapCut 网页编辑器里完成，MCP 没有导出接口。

## 许可

本仓库中的文件（`SKILL.md`、`README.md`、`README.zh-CN.md`、`scripts/`）采用 MIT 许可。下载到 `official/` 的 CapCut 插件资料仍归 CapCut 所有，适用其自身的条款。
