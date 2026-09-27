# AGENT.md - Operational Guidelines for AI Coding Agents

## Project Overview
Stateful, production-grade AI Agent built on LangGraph with PostgreSQL checkpointing, 
Model Context Protocol (MCP) tool integration, and human-in-the-loop (HITL) approval controls.

## Tech Stack & Runtime
- Python 3.11+
- Orchestration: LangGraph / LangChain Core
- State & Schema Validation: Pydantic v2 / TypedDict
- Database: PostgreSQL (with `langgraph-checkpoint-postgres`)
- Protocol: Model Context Protocol (MCP)

## Executable Development Commands
- Run Unit Tests: `pytest tests/unit -v`
- Run Integration Tests: `pytest tests/integration -v --cov=src`
- Linting & Formatting: `ruff check . --fix && ruff format .`
- Type Checking: `mypy src/ --strict`

## Architectural Boundaries & Guardrails
- **ALWAYS**: Use `TypedDict` with explicit reducers (e.g., `add_messages`) for internal graph state channels.
- **ALWAYS**: Validate external API & Tool payloads using strict `Pydantic` models before triggering nodes.
- **ASK FIRST**: Modifying database schemas, altering graph state keys, or changing checkpointer tables.
- **NEVER**: Store unencrypted API keys or runtime secrets in state channels or persistent checkpoints.
