# CLAUDE.md
> Based on Andrej Karpathy's four principles for AI coding agents.

## 1. Think Before Coding
- Don't assume. Don't hide confusion. Surface tradeoffs.
- State your understanding of the task before starting. If something is unclear — ask.
- Present multiple interpretations instead of silently picking one.
- Suggest a simpler approach if you see one.

## 2. Simplicity First
- Minimum code that solves the problem. Nothing speculative.
- No unrequested features, no unnecessary abstractions, no defensive error handling for scenarios that can't happen.
- Favor lean, direct solutions over clever ones.

## 3. Surgical Changes
- Touch only what you must. Clean up only your own mess.
- Don't refactor adjacent code, rename unrelated things, or reformat files you're not editing.
- Match the existing style and naming conventions of the file.
- Only remove code that your changes made obsolete.

## 4. Goal-Driven Execution
- Define success criteria before starting. Loop until verified.
- For multi-step tasks — create a brief plan and confirm it first.
- After completing, check against the original request to make sure nothing is missing.
- Effectiveness is measured by: fewer unnecessary changes, fewer rewrites, clarifying questions asked before implementation.
