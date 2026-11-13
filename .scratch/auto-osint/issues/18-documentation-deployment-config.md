# 18: Documentation and Deployment Configuration

**What to build:** Complete README with setup instructions, configuration guide, and usage examples. Deployment configuration (Dockerfile, Vercel deployment settings, environment variable documentation). Setup script to initialize PostgreSQL database and create default research playbook. Legal disclaimer and usage guidelines (pre-built safeguards documented).

**Blocked by:** 17: End-to-End Investigation with Synthetic Claim

**Status:** ready-for-agent

- [ ] README.md with sections:
  - Project overview (what is auto-osint?)
  - Goals and constraints
  - Prerequisites (Python, Node.js, PostgreSQL, OSINT tools)
  - Quick start guide (5-minute setup)
  - Configuration guide (all environment variables, API keys)
  - Usage examples (step-by-step investigations)
  - Development workflow (running agents, debugging)
  - Troubleshooting common issues
  - Legal disclaimer (ToS compliance, responsible use)
- [ ] Configuration guide:
  - LLM provider setup (Anthropic, OpenAI, Ollama)
  - OpenOSINT tool setup (installing binaries, obtaining API keys)
  - SYNINT setup (installing SYNINT, configuring agents)
  - PostgreSQL setup (creating database, migration scripts)
  - Environment variable reference
- [ ] Deployment configuration:
  - Dockerfile for containerized deployment
  - Vercel deployment settings (build, deploy, environment)
  - CI/CD configuration (GitHub Actions for testing and deployment)
  - Environment variable template (.env.example)
- [ ] Setup script:
  - `scripts/setup.sh` to initialize PostgreSQL schema
  - `scripts/init-playbook.sh` to create default research playbook
  - `scripts/verify-installation.sh` to check prerequisites
- [ ] Legal disclaimer and usage guidelines:
  - Pre-built safeguards documented (scope config, rate limiting, warnings)
  - Responsible use guidelines (only authorized investigations)
  - ToS compliance reminders
  - Chain-of-custody logging explanation
- [ ] License file (MIT, as in mattpocock/skills)
- [ ] Contributing guidelines (if opensourced)

**Technical notes:**
- README should be copy-paste friendly for new users
- Configuration guide should include screenshots or CLI examples
- Setup scripts should be idempotent (can run multiple times safely)
- Deployment configuration should match the tech stack (Next.js + FastAPI + PostgreSQL)
- Legal disclaimer should be prominent in README and UI
