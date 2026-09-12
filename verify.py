"""verify.py — demo smoke test for approval-notifier.

Run from your Hermes home directory (the one containing config.yaml;
on Windows: %LOCALAPPDATA%\\hermes):

    python "$LOCALAPPDATA/hermes/plugins/approval-notifier/verify.py"
    # or from a checkout:  python path/to/this/repo/verify.py  (still run from Hermes home)

Pops the stage-1 toast (alarm beeps too), then the stage-2 explanation
toast a few seconds later. Dismiss the sticky toast to stop the looping
alarm; the console beeps stop automatically at the end.
"""
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.getcwd()  # run from Hermes home

# hermes-agent package dir (for the stage-2 LLM import); common layouts:
for cand in ("hermes-agent",
             os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "hermes-agent"),
             os.path.expanduser("~/.hermes/hermes-agent")):
    if cand and os.path.isdir(cand):
        sys.path.insert(0, os.path.abspath(cand))
        break

spec = importlib.util.spec_from_file_location(
    "approval_notifier", os.path.join(HERE, "__init__.py"))
an = importlib.util.module_from_spec(spec)
spec.loader.exec_module(an)

# Print the stage-2 result to stdout as well, so the demo is verifiable
# even if you miss a toast.
_orig = an._explain_command
def _logged(command, reason_cn):
    pair = _orig(command, reason_cn)
    print("stage-2 LLM result:", pair or "(skipped — LLM unavailable)", flush=True)
    return pair
an._explain_command = _logged

CMD = 'rm -rf "D:/some/dir/that/does/not/exist" && echo done'
print("firing a fake approval request (expect toast #1 immediately)...", flush=True)
an.on_pre_approval_request(command=CMD, description="recursive delete",
                           session_key="verify", surface="cli")
time.sleep(40)
an.on_post_approval_response(choice="deny", session_key="verify")
print("done — beeps halted. If you saw two toasts, the plugin works.", flush=True)
