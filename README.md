# auto-osint

Agentic recursive OSINT research with data journalism rigor.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

auto-osint is an autonomous OSINT research agent that recursively investigates claims about public figures, produces comprehensive dossiers with evidence and counter-evidence, and maintains methodological rigor throughout.

### Key Features

- **Recursive Research Agent**: Automatically plans, executes, adapts, and refines investigations
- **Data Journalism Rigor**: Quantifies confidence in every finding, detects patterns across time, visualizes relationships
- **Recursive Self-Improvement**: Learns from completed investigations and refines methods over time
- **Verifiable Output**: Every finding links to specific sources with confidence scores
- **Extensible**: Pluggable OSINT collection engines following SYNINT/OpenOSINT patterns

## Quick Start

1. **Clone and install dependencies**:
   ```bash
   git clone https://github.com/datamathcode/auto-osint.git
   cd auto-osint
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Initialize database**:
   ```bash
   ./scripts/setup.sh
   ```

4. **Start the application**:
   ```bash
   # Backend
   uv run dev
   
   # Frontend
   npm run dev
   ```

5. **Run an investigation**:
   - Open http://localhost:3000 in your browser
   - Enter a target name and claim to investigate
   - Configure your scope and API keys
   - Start the investigation

## Documentation

- [Design Document](docs/superpowers/specs/2026-11-12-auto-osint-design.md)
- [Setup Guide](docs/setup.md)
- [Configuration Guide](docs/configuration.md)
- [API Reference](docs/api.md)

## Tech Stack

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS, D3.js, React Flow
- **Backend**: FastAPI, Python, LangChain, asyncio
- **Database**: PostgreSQL
- **OSINT Integration**: SYNINT, OpenOSINT tools
- **LLM Providers**: Anthropic, OpenAI, Ollama

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- SynINT binary
- OpenOSINT tools (optional)
- LLM API keys (Anthropic, OpenAI, or local Ollama)

## Contributing

This project is in early development. Check out the [GitHub Issues](../../issues) for pending tickets and roadmap.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and authorized research purposes only. Users are solely responsible for compliance with applicable laws and platform Terms of Service. The developers are not liable for any misuse of this software.
