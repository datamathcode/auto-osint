# Legal disclaimer and responsible use

auto-osint automates open-source intelligence collection. It does not grant you
permission to collect anything. Responsibility for each investigation rests with
the person who runs it.

## Intended use

- Investigative journalism on matters of public interest.
- Research on organisations, companies, and public figures acting in a public
  capacity.
- Due diligence and verification, using sources you are entitled to access.

## Not intended for

- Surveillance or profiling of private individuals.
- Collecting data about minors.
- Stalking, harassment, doxxing, or "doxxing by aggregation" (combining public
  data points into a private profile).
- Circumventing authentication, paywalls, robots.txt, or platform terms of
  service.
- Any use that would violate GDPR, CCPA, the Computer Fraud and Abuse Act, or
  equivalent law in your jurisdiction.

## Platform terms of service

Every client in this repository talks to a third-party service. You are
responsible for complying with each service's terms: rate limits, acceptable-use
policies, and licensing of returned data. The Have I Been Pwned API, for example,
requires an API key and forbids redistribution of breach data.

## Privacy and data minimisation

- Collect only what the claim requires. The scope fields (date range, platforms,
  data types, time budget) exist to bound collection.
- Do not store special-category data (health, ethnicity, religion, sexuality,
  political opinions) unless the investigation genuinely requires it and you
  have a lawful basis.
- Delete investigation data when the work is finished.

## Built-in safeguards

| Safeguard | Where | What it does |
|---|---|---|
| Scope configuration | `/investigate`, `Investigation.scope` | Bounds date range, platforms, data types and run time |
| Per-tool timeout | `ToolBase.timeout_seconds` (60s) | Kills hung collection |
| Rate limiting | `ToolBase._check_rate_limit` (10/min/proc default) | Reduces load on third parties |
| Parallelism cap | `Orchestrator(max_concurrent=8)` | Bounds request volume |
| Confidence scoring | `AgentBase.store_evidence`, `audit.py` | Flags weak conclusions instead of asserting them |
| Gap detection | `audit.py` | Names missing sources and unanswered questions |
| Counter-evidence section | dossier viewer | Surfaces contradicting evidence next to supporting evidence |
| Chain of custody | `Evidence.chain_of_custody`, `raw_text` | Records what ran, when, and the raw output |
| API-key confinement | `/api/config/defaults` | Never returns secret values |

These safeguards reduce harm; they do not make an unlawful investigation lawful.

## Chain of custody

Every evidence row stores its source, timestamp, links, the raw tool output
(`raw_text`), and a `chain_of_custody` log with the command and observation
records. This exists so a reader can audit how a claim was produced and so a
mistake can be traced rather than hidden.

## No warranty

The software is provided under the MIT licence, without warranty. Findings are
machine-generated leads, not verified facts. Verify before publishing.
