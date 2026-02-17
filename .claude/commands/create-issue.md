---
allowed-tools: Bash(gh:*)
argument-hint: [path-to-file.md]
description: Create a GitHub issue from context or markdown file
---

Create a GitHub issue from the current session context or a markdown file.

## Available Labels

Choose appropriate labels from:
- `feature` - New feature or request
- `bug` - Something isn't working
- `security` - Security oriented changes
- `refactor` - Changes that only refactor code

## Workflow

1. If $ARGUMENTS is provided, read the markdown file for issue content
2. Otherwise, summarize the current session context into an issue
3. Generate a clear, concise title (max 72 chars)
4. Write a well-structured body with:
   - Problem/motivation
   - Proposed solution (if applicable)
   - Acceptance criteria (if applicable)
5. Select appropriate label(s) based on content
6. Use `gh issue create --title "..." --body "..." --label "..."`
7. Return the created issue URL
