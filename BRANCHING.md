# Branching and Workflow Strategy

## Branch Strategy

This project follows Git Flow branching model with adjustments for ticket-based development.

### Branches

```
main          → Deployable releases only (production-ready)
  ↑
develop       → Integration branch for features
  ↑
feature/      → Feature branches for tickets
  ├─ feature/01-setup-project-structure
  ├─ feature/02-base-agent-framework
  ├─ feature/03-expand-confidence-module
  └─ ...
```

### Branch Purpose

**main**
- Production-ready releases only
- Never contains in-progress work
- Protected branch (merge via PR only)
- Deployed to production after successful CI

**develop**
- Integration branch for all features
- Receives merged feature branches
- Temporary branch that gets reset between releases
- Used as base for feature branches

**feature/<ticket-XX>**
- Short-lived branch for individual tickets
- Created from develop
- Work-in-progress only
- Merged back to develop (not main) via PR
- Named after ticket number for traceability

### Branch Naming Convention

- Feature branches: `feature/<ticket-XX>-<feature-name>`
- Release branches: `release/<major>.<minor>`
- Hotfix branches: `hotfix/<issue-ID>-<summary>`
- Development branch: `develop`

Examples:
- `feature/04-migrate-first-batch-evidence`
- `feature/05-contract-old-evidence-storage`

## Commit Message Convention

Follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, no logic)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

### Examples

```
feat(backend): implement base agent framework

- Add AgentBase class with lifecycle methods
- Add ToolBase class with timeout enforcement
- Implement registry pattern for discovery
- Create SYNINT agent wrapper

Ticket 02: Base Agent and Tool Framework

[verified] independent review passed
```

## Pull Request Workflow

### PR Template

```markdown
## Description
Brief description of changes

## Ticket
Closes #<ticket-number>

## Changes
- [ ] ...
- [ ] ...

## Testing
- [ ] Tests pass
- [ ] Manual testing completed
- [ ] Security scan passed

## Checklist
- [ ] Code follows project conventions (AGENTS.md)
- [ ] No hardcoded secrets or credentials
- [ ] Self-review checklist completed
- [ ] Tests added for new functionality
```

### PR Review Process

1. **Author creates PR** from `feature/<ticket-XX>` to `develop`
2. **Self-review**: Author completes self-review checklist
3. **Reviewer assignment**: Assign maintainer or automated reviewer
4. **Review**: Reviewer provides feedback
5. **Comments resolved**: Author addresses all comments
6. **Approvals**: Required approvals from at least 1 reviewer
7. **Status checks**: CI must pass
8. **Merge**: Merge to develop

## Merge Strategy

### Merge Types

**Merge (Squash and Merge)**
- Best for feature branches
- Creates single commit on target branch
- Cleans up commit history
- Recommended for most cases

**Merge (Rebase)**
- Fast-forward merges
- Maintains linear history
- Good for develop branch integration
- Use with caution

### Merge Workflow

1. PR has approvals
2. CI/CD passes
3. Review comments resolved
4. Squash and merge to target branch
5. PR automatically closes

## Self-Review Checklist

Before creating PR:

- [ ] Code follows AGENTS.md conventions
- [ ] No hardcoded secrets, API keys, or credentials
- [ ] Input validation on user-provided data
- [ ] SQL queries use parameterized statements
- [ ] File operations validate paths (no traversal)
- [ ] External calls have error handling (try/catch)
- [ ] No debug print/console.log left behind
- [ ] No commented-out code
- [ ] New code has tests (if test suite exists)
- [ ] Tests pass (local or CI)
- [ ] Static security scan passed
- [ ] Commit message follows Conventional Commits

## Branch Protection Rules

**main branch:**
- Protected (merge via PR only)
- Require 1 approval
- Require status checks to pass
- Block force pushes
- Require branch clean (no open PRs)

**develop branch:**
- Protected (merge via PR only)
- Require 1 approval
- Require status checks to pass
- Require branch clean (no conflicting changes)

## Creating a New Feature Branch

```bash
# From main
git checkout main
git pull origin main
git checkout -b feature/04-migrate-first-batch-evidence

# From develop (recommended)
git checkout develop
git pull origin develop
git checkout -b feature/04-migrate-first-batch-evidence
```

## Workflow Example

```
1. Create feature branch
   git checkout -b feature/04-migrate-first-batch-evidence

2. Make commits
   git add .
   git commit -m "feat(evidence): migrate to new storage schema"

3. Push branch
   git push origin feature/04-migrate-first-batch-evidence

4. Create PR
   # Via GitHub UI or CLI
   gh pr create --base develop --head feature/04-migrate-first-batch-evidence

5. Self-review
   # Run verification pipeline
   git push

6. Update PR
   # Address reviewer comments

7. Merge PR
   # Squash and merge to develop
   gh pr merge --squash

8. Delete feature branch
   gh pr close --delete-branch
```

## CI/CD Integration

- Branch-specific workflows
- PR status checks
- Automated security scanning
- Test execution on every PR
- Deploy preview on develop branches

## Issue/Work Item Tracking

- Issues linked to tickets in code
- PR references issue numbers
- Tickets contain acceptance criteria
- Completion marked in ticket status

## Escalation

If PR review fails after 3 attempts:
1. Escalate to maintainer
2. Request manual intervention
3. Document blocking issues
4. Consider reverting merge if necessary
