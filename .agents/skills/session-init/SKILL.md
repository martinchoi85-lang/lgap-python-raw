---
name: session-init
description: Bootstrap protocol to synchronize project context using ai_docs
triggers:
  - command: "/init"
  - intent: "Initialize or setup session context"
scope: workspace
---

# Session Bootstrap Protocol

You are tasked with initializing the development session context with minimal token usage.

## Instructions
1. **Targeted File Detection:** Check if `ai_docs/PRD.md` and `ai_docs/active_state.md` exist.
2. **Conditional Path:**
   - **IF THEY EXIST:** Read ONLY `ai_docs/PRD.md` and `ai_docs/active_state.md`. Do NOT read other files in `ai_docs/` unless specifically requested later.
   - **IF THEY DO NOT EXIST:** Perform a lightweight project inspection (`git status` or root dir listing) and prompt the user for starting goals.
3. **Session Handover Response:** Briefly summarize the current state from `active_state.md` in 2-3 lines and ask the user for the immediate next task.

## Constraints
- Do not log full diagnostic outputs.
- Keep the initial context payload lightweight.