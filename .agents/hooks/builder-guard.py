#!/usr/bin/env python3
"""PreToolUse guard for Antigravity Builder dispatches.

Reads a hook payload on stdin, writes an allow/deny decision on stdout.

Policy, per AGENTS.md sections 15 and 22: the Builder may read, edit, and run
tests freely, but every commit, push, history rewrite, and branch/worktree
mutation stays with the human. Denials are hard blocks, so they hold even when
the dispatch runs with --dangerously-skip-permissions.
"""
import json
import re
import sys

# Matched against the whole command line, so chained commands
# (`pytest && git push`) are caught too, not just the leading word.
DENY = [
    (r"\bgit\s+(commit|push|revert|cherry-pick)\b", "commits/pushes are the human's call"),
    (r"\bgit\s+(reset|rebase|merge|clean)\b", "history or working-tree rewrite"),
    (r"\bgit\s+(checkout|switch)\b", "branch switching is the human's call"),
    (r"\bgit\s+branch\b.*\s-[dDM]\b", "branch deletion/rename"),
    (r"\bgit\s+tag\b.*\s-d\b", "tag deletion"),
    (r"\bgit\s+worktree\s+(remove|prune)\b", "worktree deletion"),
    (r"\bgit\s+(filter-branch|reflog\s+expire)\b", "history rewrite"),
    (r"\bgit\s+push\b.*(--force|-f)\b", "force push"),
    (r"\bgh\s+(pr|release)\s+(create|merge|close)\b", "PR/release actions need approval"),
    (r"\brm\s+-[rRf]*[rRf]", "recursive/forced delete"),
    (r"\bsudo\b", "privilege escalation"),
    (r">\s*/dev/(sd|disk)", "raw device write"),
    (r"\b(shutdown|reboot|mkfs|diskutil)\b", "destructive system command"),
    (r"\bpip\s+install\b.*--break-system-packages", "environment damage"),
    (r"\balembic\s+downgrade\b", "schema downgrade needs approval"),
    (r"\bdropdb\b|\bDROP\s+DATABASE\b", "database destruction"),
]


def decide(payload):
    call = payload.get("toolCall") or {}
    name = (call.get("name") or "").lower()
    args = call.get("args") or {}

    # Only shell execution is gated; reads and file edits pass through.
    if name not in ("run_command", "command"):
        return {"decision": "allow"}

    cmd = args.get("CommandLine") or args.get("commandLine") or ""
    if not isinstance(cmd, str):
        cmd = str(cmd)

    for pattern, why in DENY:
        if re.search(pattern, cmd, re.IGNORECASE):
            return {
                "decision": "deny",
                "reason": (
                    f"Blocked by .agents/hooks/builder-guard.py: {why}. "
                    "Report the intended change and let the human run it."
                ),
            }
    return {"decision": "allow"}


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Never fail open on a malformed payload for a command we cannot read.
        print(json.dumps({"decision": "ask", "reason": "guard could not parse hook payload"}))
        return
    print(json.dumps(decide(payload)))


if __name__ == "__main__":
    main()
