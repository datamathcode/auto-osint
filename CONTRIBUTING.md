# Contributing

## Before you start

Read `docs/legal.md`. This project performs open-source intelligence collection;
contributions must not add features whose primary purpose is surveillance of
private individuals, evasion of platform terms of service, or collection of
data about minors.

## Development setup

```bash
git clone https://github.com/datamathcode/auto-osint.git
cd auto-osint
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
npm install
cp .env.example .env   # fill in what you need; leave keys blank if unused
python -m src.python.scripts.setup_database
```

## Checks that must pass

```bash
ruff check src/python/ tests/
python -m pytest tests/ -q
npx tsc --noEmit
npx next build
```

CI runs the same commands on Python 3.10 and 3.11, plus the frontend build.
A pull request that leaves any of them red is not ready to merge.

## Branching

Work happens on `feature/<ticket>-<slug>` and merges to `develop`. `main` only
receives release merges from `develop`. See `BRANCHING.md`.

## Adding a tool client

1. Subclass `OpenOSINTClient` in `src/python/tools/clients/`.
2. Return the shared envelope: `status`, `tool`, `target`, `source`, `data`,
   `error`.
3. Keep the timeout and rate limit from the base class; do not bypass them.
4. Register it in `src/python/tools/config.json`.
5. Add tests that cover success, empty result, timeout, and upstream error.

## Adding a playbook section

Add the section to `src/python/research_playbook.mdx` front matter with
`suggested_tools`, `strategies`, and any thresholds, then extend the claim-type
keywords in `src/python/orchestrator.py`. Tests in `tests/test_research_playbook.py`
guard the file's front matter.

## Reporting problems

Open an issue with the command you ran, the output, and the commit SHA. Do not
paste API keys, tokens, or personal data into issues.
