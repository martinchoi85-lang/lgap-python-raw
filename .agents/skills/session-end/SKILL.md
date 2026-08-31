---
name: session-end
description: Wrap-up protocol to update active state, regenerate structure, and prepare handover package
triggers:
  - command: "/end"
  - intent: "Terminate session or wrap up development"
scope: workspace
---

# Session Wrap-up Protocol

You are tasked with finalizing the current development session. Execute the following automation and documentation steps without conversational filler.

## Instructions
<!-- 1. **Inspect Workspace Changes:** Execute `git status` and `git diff --stat` to verify actual modified and created files. -->
2. **Update Active State File:** Automatically call your file writing tool to overwrite `ai_docs/active_state.md` with:
   - Current project status & completed tasks in this session.
   - Remaining TODO items for the next session.
   - Key architectural decisions or modified key files.
3. **Commit Message Generation:** Generate a concise Git commit message adhering strictly to Conventional Commits.

## Constraints
- Do NOT output verbose text in chat. Perform file modifications directly.
- Ensure `ai_docs/active_state.md` is updated on the filesystem before concluding.