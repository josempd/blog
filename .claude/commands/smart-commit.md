---
description: Analyze uncommitted changes and create logical, well-structured git commits with conventional commit messages
---

# Smart Commit

Analyze uncommitted changes and create logical, well-structured git commits with conventional commit messages, no footer, no author.

## Your Task

1. Analyze the repository state:
   - Run git status to see all changes
   - Run git diff for unstaged changes
   - Run git diff --cached for staged changes
   - Identify untracked files

2. Group changes logically:
   - Group by layer (infrastructure → features → docs)
   - Group by component (related files together)
   - Follow dependency order (foundational changes first)
   - Separate concerns (don't mix features and fixes)

3. Generate conventional commit messages:
   - Format: type(scope): description
   - Types: feat, fix, docs, chore, refactor, test, style
   - Scopes: project, repository, backend, all, or feature-specific (e.g. blog, content)
   - Max 100 characters
   - Lowercase, no period at end
   - Present tense ("add" not "added")
   - Descriptive but concise

4. Create commits in order:
   - Stage files for each logical group
   - Commit with generated message using heredoc format:
          git commit -m "$(cat <<'EOF'
     type(scope): commit message here
     EOF
     )"

   - Repeat for each group

5. Show results:
   - Display final commit history with git log --oneline --decorate
   - Show commit stats with git log --stat --oneline

## Commit Ordering Rules

Follow this priority order:
1. Project setup (pyproject.toml, dependencies, .gitignore)
2. Core infrastructure (logging, config, utilities)
3. Application code (main features, components)
4. Tests (if any)
5. Documentation (README, architecture docs)

## Quality Guidelines

- Each commit should be buildable and testable
- Commits tell a story of how the project was built
- No "WIP" or "fix" commits - make them meaningful
- Don't mix unrelated changes
- Respect dependencies (don't commit app before infrastructure)

## Example Workflow

For a typical feature branch, you might create:
1. chore(project): add project dependencies
2. feat(backend): add authentication service
3. feat(backend): add user registration endpoint
4. test(backend): add auth service tests
5. docs(project): update API documentation

Now analyze the current repository and create appropriate commits!