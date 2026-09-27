# Production Stateful Agent Sandbox

A production-grade, stateful AI agent template featuring durable execution, 
interrupt-based human-in-the-loop (HITL) approvals, and strict Pydantic/TypedDict state channels.

## System Capabilities
- **Automated Actions:** Read-only database queries, context retrieval, and draft generation.
- **Human-in-the-Loop Intercepts:** High-risk financial operations, database mutations, or external API execution pause for explicit approval via `interrupt()`.

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (for persistent graph checkpointing)

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install langgraph langchain-core pydantic ruff pytest

