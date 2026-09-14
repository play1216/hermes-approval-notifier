# approval-notifier 🔔

**Never miss a dangerous-command approval prompt in [Hermes Agent](https://github.com/NousResearch/hermes-agent) again — and never have to decipher raw shell to answer one.**

Windows Toast alerts + repeating alarm + plain-language Chinese explanations:
when Hermes flags a command as dangerous, this plugin immediately pops a
notification with the risk translated into Chinese (e.g. 「递归删除目录」),
then follows up seconds later with an LLM-written two-line breakdown of what
the command *actually does* and what could go wrong — using **your currently
active model**, no extra API key.

为 Hermes Agent 打造的审批提醒插件：危险命令弹窗出现的那一刻，Windows
通知中心立即弹出「人话版」风险提示（内置全部 80 条安全规则的中文映射表，零延迟），
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
终端里（每次审批都打印，v1.2）:

╔══ ⚠ 审批请求 ══════════════════════════════════════════════╗
║ 风险类型: 递归删除目录                                      ║
║ 命令: rm -rf "D:/data/cache"                                ║
║ AI 正在解读命令，几秒后显示在下方…                          ║
╚════════════════════════════════════════════════════════════╝
        +  your alert sound loops  +  Toast (stage 1)  +  15s beeps

╔══ 📖 AI 解读（仅供参考，决定权在你） ══════════════════════╗
║ 对象: F:/STOCK 目录下的所有 CSV 行情文件                    ║
║ 动作: 递归删除该目录及全部子目录内容                        ║
║ 后果: 30个币种两年半的K线数据永久丢失                       ║
║ 可逆性: 不可撤销。需重新下载约40GB                          ║
║ 建议: 拒绝。该数据盘被标记为只读                            ║
╚════════════════════════════════════════════════════════════╝
```

Stage 1 is a deterministic EN→CN map of **all 80** built-in
`DANGEROUS_PATTERNS` / `HARDLINE_PATTERNS` rule names (incl. PowerShell /
Windows / Docker rules) — plain language, not jargon, instant, no network.
Stage 2 walks your active main model (freshly read from `config.yaml`, so
model switches are honored) through a **fixed 5-field thought path**:
对象(what it touches) → 动作(what happens) → 后果(worst case) →
可逆性(can it be undone) → 建议(放行/拒绝/请人工确认). Missing fields get
one follow-up pass; anything still missing renders as
"(模型未给出,按最坏情况对待)". If the LLM is down entirely, the terminal
says "AI 解读暂不可用" — stage 1 has already fired and the alarm keeps
going until you resolve the prompt.

## Features

- 🚨 **Toast + alarm + 15s beep loop** until the approval is resolved — impossible to miss
- 📖 **Fixed 5-field AI breakdown printed IN the terminal** (对象/动作/后果/可逆性/建议) — read it where you answer the prompt
- 🔊 **Your own alert sound** — drop in an `approval.wav` (e.g. an F1 radio
  chime) and it loops instead of the built-in alarm, stopping the moment
  you resolve the prompt
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

If the AI breakdown is too slow behind your main model's endpoint, pin a
faster/free model for explanations (falls back to the main model when unset):

```yaml
# config.yaml
auxiliary:
  approval:
    model: glm-4-flash
    base_url: https://api.z.ai/api/paas/v4
    api_key: <your key>
```

### Custom alert sound / 自定义提示音

默认警报是蜂鸣+系统铃声。想换成任何你喜欢的铃声（比如 F1 电台提示音）：

```bash
# mp3 → wav 尾部垫静音（pad_dur 控制响铃间隔：铃声~0.7s + 静音29.3s ≈ 30秒一响）
ffmpeg -i your-ringtone.mp3 -af "apad=pad_dur=29.3" -ac 1 -ar 44100 approval.wav
```

把 `approval.wav` 放到插件目录（与 `__init__.py` 同级）即可，无需重启以外的
任何配置；也可以用环境变量 `APPROVAL_NOTIFIER_SOUND` 指向任意 wav 路径。
文件不存在或非 Windows 平台时自动回退到内置蜂鸣警报。声音在审批被
解决（批准/拒绝/超时）的瞬间停止。
The WAV loops while a prompt is pending and stops the instant it is
resolved. `approval.wav` is git-ignored on purpose — bring your own ringtone.

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
