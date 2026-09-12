# approval-notifier 🔔

**Never miss a dangerous-command approval prompt in [Hermes Agent](https://github.com/NousResearch/hermes-agent) again — and never have to decipher raw shell to answer one.**

Windows Toast alerts + repeating alarm + plain-language Chinese explanations:
when Hermes flags a command as dangerous, this plugin immediately pops a
notification with the risk translated into Chinese (e.g. 「递归删除目录」),
then follows up seconds later with an LLM-written two-line breakdown of what
the command *actually does* and what could go wrong — using **your currently
active model**, no extra API key.

为 Hermes Agent 打造的审批提醒插件：危险命令弹窗出现的那一刻，Windows
通知中心立即弹出「人话版」风险提示（内置 60 条规则的中文映射表，零延迟），
几秒后再推送一条由你当前主模型生成的中文解读——这条命令到底做了什么、
批准后可能的后果。不需要额外 API Key。

---

## Why / 为什么

Hermes asks for confirmation before running destructive commands — a good
default. But two things go wrong in practice:

1. **You miss the prompt.** Background the terminal and the prompt sits
   there; at the default 60s timeout the command auto-denies and the agent
   marks your task as "user refused". You come back to a broken workflow
   and no idea anything happened.
2. **You can't read the prompt.** It's a raw shell command plus an English
   rule name like `recursive delete` / `pipe remote content to shell`.
   If you're not fluent in shell, "approve" becomes a coin flip — which is
   exactly when the safety prompt stops being safe.

approval-notifier fixes both:

```
┌──────────────────────────────┐   ← Stage 1, instant, works offline
│ ⏰ Hermes 审批请求            │
│ ⚠ 递归删除目录                │
│ 命令: rm -rf "D:/data/cache"  │
└──────────────────────────────┘
        +  looping alarm sound  +  console beeps every 15s

┌──────────────────────────────┐   ← Stage 2, ~3–10s later, via your model
│ 📖 Hermes 命令解读            │
│ 做什么: 递归删除 D:/data/cache │
│ 缓存目录及其所有内容。        │
│ 风险: 高危。文件将被永久删除， │
│ 无法恢复。                    │
└──────────────────────────────┘
```

Stage 1 is a deterministic EN→CN map of **all 60** built-in
`DANGEROUS_PATTERNS` / `HARDLINE_PATTERNS` rule names — instant, no network.
Stage 2 asks your active main model (freshly read from `config.yaml`, so
model switches are honored) for a concrete explanation of *this* command.
If the LLM fails or times out, stage 2 is silently skipped — stage 1 has
already fired and the alarm keeps going until you resolve the prompt.

## Features

- 🚨 **Toast + alarm + 15s beep loop** until the approval is resolved — impossible to miss
- 🈶 **Instant Chinese risk labels** — static map, zero latency, works with any/offline model
- 🧠 **Plain-language command breakdown** from your active model — what it does, what it risks
- 🪡 **Observer-only by design** — never touches the approval decision itself, never blocks the agent thread
- 🔄 **Model-switch proof** — reads `config.yaml` model section per call
- 🧯 **Fail-silent** — toast failure, LLM failure, PowerShell hang: the agent keeps running
- 🔒 **No dependencies** — pure stdlib + Windows WinRT (built into Windows 10/11)

## Requirements

- Windows 10/11 (the Toast layer degrades to console bells elsewhere; core logic is portable)
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) with plugin support (`pre_approval_request` hook)

## Install

```bash
# 1. Clone into your Hermes plugins dir
git clone https://github.com/play1216/hermes-approval-notifier \
  "$LOCALAPPDATA/hermes/plugins/approval-notifier"

# 2. Enable it
hermes plugins enable approval-notifier

# 3. Restart Hermes (plugins load at startup)
```

<details>
<summary>Manual install / 手动安装</summary>

Copy `__init__.py` and `plugin.yaml` into
`%LOCALAPPDATA%\hermes\plugins\approval-notifier\` (Linux/macOS:
`~/.hermes/plugins/approval-notifier/`), add `approval-notifier` to
`plugins.enabled` in `config.yaml`, restart Hermes.

</details>

## Try it (demo)

From your Hermes home directory (the one with `config.yaml` — on Windows
that's `%LOCALAPPDATA%\hermes`):

```bash
python plugins/approval-notifier/verify.py
```

You'll get the stage-1 toast (alarm beeps too), then the stage-2
explanation toast a few seconds later. Close the sticky toast to stop the
looping alarm. Or just ask your agent to run `rm -rf ./some-test-dir` and
watch the real flow.

## Configuration

All tunables are constants at the top of `__init__.py`:

| Constant | Default | Meaning |
|---|---|---|
| `_BELL_INTERVAL_S` | 15.0 | Console beep repeat interval while a prompt is pending |
| `_BELL_MAX_S` | 900 | Hard stop for the beep loop (15 min) |
| `_LLM_TIMEOUT_S` | 25 | Stage-2 explanation budget; skipped on failure |
| `_LLM_MAX_INPUT_CHARS` | 2000 | Command truncation before it reaches the model |

Recommended companion setting: give yourself time to read the toasts
before the prompt auto-denies:

```bash
hermes config set approvals.timeout 300
```

## How it works

- Hooks `pre_approval_request` / `post_approval_response` (both CLI and gateway surfaces).
- The hooks only *observe* — return values are ignored by Hermes, so this plugin cannot approve or deny anything. Your decision still happens with y/n in the terminal.
- Toasts are fired through `powershell.exe -EncodedCommand` (base64 UTF-16LE) so arbitrary command text can never break quoting, and the toast XML itself is escaped (`<`/`&` in commands are safe).
- Why not patch the built-in prompt text? Plugins must not patch core files — and you keep upstream updates. The toasts carry the translation layer.

## Known limitations

- **y/n stays in the terminal.** Approving from the toast itself (action buttons + IPC) is possible but out of scope for v1 — open an issue if you want it.
- Stage-1 labels map **Hermes' current English rule names**; if upstream renames/adds rules, new ones fall through untranslated (stage 2 still explains them).
- Stage 2 needs your configured model endpoint to be reachable; b.ai-style relays occasionally read-timeout (the OpenAI client's internal retry usually recovers).
- Windows Focus Assist (专注助手) can silently swallow toasts — check it if you see beeps but no popups.

## Related

- Sister project: [hermes-session-scribe](https://github.com/play1216/hermes-session-scribe) — ChatGPT-style auto-titling for Hermes conversations
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research

## License

MIT — © 2026 WHW ([@play1216](https://github.com/play1216))
