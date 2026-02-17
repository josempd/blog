---
allowed-tools: Bash(gh:*)
argument-hint: <issue-number>
description: Download a GitHub issue to markdown
---

Download GitHub issue #$ARGUMENTS to a markdown file.

1. Use `gh issue view $ARGUMENTS --json title,body,number,state,author,createdAt,labels,comments` to fetch the issue
2. Format it as a proper markdown file with:
   - Title as H1 with issue number
   - Metadata (state, author, date, labels)
   - Body content
   - Comments section if any exist
3. Save to `issue-$ARGUMENTS.md` in the current directory
4. Confirm the file was created
```

**Usage:**
```
/github-issue 333