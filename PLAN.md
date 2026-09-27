# PLAN.md - Production LangGraph Agent Execution Roadmap

## Objective
Build and deploy a scalable, stateful, human-in-the-loop (HITL) agent capable of safely executing side-effects with transactional rollbacks and durable state checkpointing.

## Architecture State Flow Diagram
[User Request] ──> [Reasoning Node] ──> {Requires High-Risk Tool?}
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          ▼ (Yes)                                     ▼ (No)
                [Pending Action Node]                       [Execute Standard Tool]
                          │                                           │
                [interrupt() Trigger]                                 └──> [Return Output]
                          │
            ===============================
            PAUSE: Awaiting Human Review
            ===============================
                          │
             [Resume via Command(resume=...)]
                          │
          ┌───────────────┴───────────────┐
          ▼ (Approved)                    ▼ (Rejected)
  [Execute Side-Effect]           [Cancel & Return Feedback]

## Implementation Milestones
- [x] **Step 1: Core Architecture & Strongly-Typed State Schema**
  - Define `ProductionAgentState` using `TypedDict` and `add_messages` reducer.
- [ ] **Step 2: Tool Definitions & Idempotent Side-Effects** *(Next Step)*
  - Create standard tools and isolate high-risk side-effects.
- [ ] **Step 3: Reasoning Node & In-Node `interrupt()` Logic**
  - Implement LLM decision node and human approval interrupt boundaries.
- [ ] **Step 4: Graph Compilation & Production Checkpointing**
  - Wire state graph with `PostgresSaver` checkpointer and state-machine transitions.
- [ ] **Step 5: Execution, Pause Inspection, & Resuming via `Command`**
  - Implement API endpoints for inspecting paused state and resuming graph execution.
