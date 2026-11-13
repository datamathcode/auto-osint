## Description
A brief description of the changes being made.

## Related Issue/Closed Ticket
Closes #<ticket-number>

## Changes
- [ ] Feature implementation
- [ ] Bug fix
- [ ] Code refactoring
- [ ] Documentation updates
- [ ] Security improvement
- [ ] Performance optimization

## Testing
- [ ] All tests pass (run locally with `pytest` or `npm test`)
- [ ] Manual testing completed
- [ ] Edge cases covered
- [ ] Integration tests passing
- [ ] No new warnings or errors

## Self-Review Checklist
- [ ] Code follows AGENTS.md conventions
- [ ] No hardcoded secrets, API keys, or credentials
- [ ] Input validation on user-provided data
- [ ] SQL queries use parameterized statements (no string formatting)
- [ ] File operations validate paths (no path traversal)
- [ ] External calls have error handling (try/catch)
- [ ] No debug print/console.log left behind
- [ ] No commented-out code
- [ ] New code has tests (if test suite exists)
- [ ] Existing functionality not broken
- [ ] Commit message follows Conventional Commits format

## Security Scans
- [ ] Static security scan passed
- [ ] No vulnerabilities found (checked with `bandit` and `safety`)
- [ ] No secrets committed
- [ ] Input sanitization applied where needed

## Testing Instructions
### For Backend Changes
```bash
# Run tests
python -m pytest tests/ -v

# Run linter
ruff check src/python/

# Run type checker
mypy src/python/ --ignore-missing-imports
```

### For Frontend Changes
```bash
# Run tests
npm test

# Run linter
npm run lint

# Build
npm run build
```

## Screenshots
If this change affects the UI, add screenshots here.

## Additional Context
Any additional information, notes, or breaking changes.
