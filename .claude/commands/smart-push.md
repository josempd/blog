---
description: Push branch and create a well-structured GitHub pull request with auto-generated description
---

# Smart Push

Push the current branch and create a GitHub pull request with a well-structured title and description based on commit history.

## Your Task

1. Verify prerequisites:
   - Check if gh CLI is installed: `which gh`
   - Check if authenticated: `gh auth status`
   - Check current branch: `git branch --show-current`
   - Ensure not on main/master: abort if so

2. Analyze the branch:
   - Get commits not in main: `git log main..HEAD --oneline`
   - Get detailed changes: `git log main..HEAD --stat`
   - Get the full diff for context: `git diff main..HEAD --stat`

3. Generate PR title:
   - If single commit: use commit message as title
   - If multiple commits: summarize the feature/change
   - Format: type: description (conventional commit style)
   - Max 72 characters
   - Lowercase, no period at end

4. Generate PR description:
   - Use this structure:
```
     ## Summary
     Brief description of what this PR accomplishes.

     ## Changes
     - Key change 1
     - Key change 2
     - Key change 3

     ## Notes
     Any additional context, breaking changes, or migration notes.
```

5. Determine labels from commits:
   - Analyze ALL commit prefixes (feat:, fix:, docs:, etc.)
   - Map to labels (only use labels that exist in the repo):
     - `feat:` → feature
     - `fix:` → bug
     - `perf:` → bug
     - `docs:` → docs
     - `refactor:` → refactor
     - `ci:` → ci
     - `breaking:` → breaking
     - `security:` → security
     - `deps:` → dependencies
   - Skip commit types without a matching label (test:, chore:, style:, etc.)
   - Add ALL labels that match commit types present in the branch
   - Primary label (for PR title type) = dominant commit type
   - Example: commits with feat:, docs: → add labels: feature,docs

6. Push and create PR:
   - Push the branch: `git push -u origin HEAD`
   - Create PR with assignee and all matching labels:
```bash
     gh pr create \
       --title "type: title here" \
       --assignee @me \
       --label "feature,docs" \
       --body "$(cat <<'EOF'
     ## Summary
     Description here.

     ## Changes
     - Change 1
     - Change 2

     ## Notes
     Additional context.
     EOF
     )"
```

7. Show results:
   - Display PR URL
   - Show PR status: `gh pr view`

## PR Title Rules

Derive type from commits:
- Multiple `feat:` commits → `feat: <feature summary>`
- Multiple `fix:` commits → `fix: <fix summary>`
- Mixed types → use the dominant type or `feat:` for new features
- Single commit → use that commit's message directly

## Label Mapping

| Commit Type | Label |
|-------------|-------|
| `feat:` | feature |
| `fix:` | bug |
| `perf:` | bug |
| `docs:` | docs |
| `refactor:` | refactor |
| `ci:` | ci |
| `breaking:` | breaking |
| `security:` | security |
| `deps:` | dependencies |

Note: `test:`, `chore:`, and `style:` commits don't have matching labels - skip them.

## Description Guidelines

- Summary: 1-2 sentences explaining the "why"
- Changes: bullet points of the "what" (not every commit, but key changes)
- Notes: optional section for breaking changes, deployment notes, or context
- Keep it scannable for reviewers
- Don't duplicate what's obvious from the diff

## Optional Flags

Support these options if specified by user:
- Draft PR: add `--draft` flag
- Specific base branch: add `--base <branch>` flag
- Add reviewers: add `--reviewer <user>` flag
- Additional labels: add extra `--label <label>` flags

## Example Output

For a branch with these commits:
- feat: add user authentication service
- feat: add login endpoint
- docs: add auth documentation

Generate:
- **Title:** `feat: add user authentication`
- **Labels:** `feature,docs`
- **Assignee:** @me
- **Body:**
```
  ## Summary
  Implements user authentication with login functionality.

  ## Changes
  - Add authentication service with JWT support
  - Add POST /login endpoint
  - Add API documentation for auth endpoints

  ## Notes
  Requires AUTH_SECRET environment variable to be set.
```

Now analyze the current branch and create an appropriate pull request!