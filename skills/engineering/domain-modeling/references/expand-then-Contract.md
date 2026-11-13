# Expand-Then-Contract Pattern

When implementing a feature incrementally, use expand-then-Contract to avoid premature optimization and simplify migration.

## When to Use

- New feature or subsystem that hasn't been implemented yet
- Unclear what the minimal interface or API should be
- Multiple stakeholders and perspectives on requirements
- Need to avoid refactoring later due to design mistakes

## How It Works

### Expand Phase

1. **Broadly implement:** Start with a comprehensive, flexible implementation that covers all edge cases and scenarios.
2. **Make it explicit:** Define all interfaces, parameters, and behaviors openly. No hidden magic or clever tricks.
3. **Document thoroughly:** Write extensive comments and documentation explaining the full surface area.
4. **Add tests for all paths:** Coverage for happy paths and failure modes.

### Contract Phase

1. **Identify actual usage:** Run the system in production or realistic usage scenarios.
2. **Extract minimal API:** Review what was actually called and needed. Remove unused parameters and behaviors.
3. **Simplify internals:** Clean up the implementation now that usage is clear.
4. **Update documentation:** Reflect the new, simpler surface area.

## Example: Confidence Module

**Expand:**
- Add confidence scoring at the evidence, claim, and dossier levels
- Support multiple scoring models (Bayesian, heuristic, empirical)
- Allow per-source weighting
- Provide visualization of confidence distribution

**Contract:**
- Keep only Bayesian confidence scoring as the implemented model
- Remove multi-model support (keep one reliable approach)
- Simplify weighting to a single uniform weight
- Reduce visualization to key charts only

## Benefits

- **Lower initial cognitive load:** Implement fully first, then simplify.
- **Fewer refactoring cycles:** Expand once, contract once.
- **Discovery-driven:** Actual usage reveals what's truly needed.
- **Safe exploration:** Broad implementation doesn't commit to narrow design.

## Contract Checkpoints

Before starting Contract:

- At least one full-pass trial or realistic test run
- User or stakeholder review of expanded behavior
- Concrete evidence of which features are used vs. unused

## After Contract

- Update all documentation to reflect the new surface area
- Update tests to match the contracted API
- Remove unused code paths from the implementation
- Archive old branches or commits documenting the expansion
