# FLOW-DIAGRAM

## Day 2 Goal
Implement a multi-agent orchestration pipeline for:

User Query
-> Planner
-> Parallel Worker Agents
-> Reflection Agent
-> Validator Agent
-> Final Answer

This matches the Day 2 planner-worker-validator flow, while also including the Reflection Agent required in the exercise.

## Architecture

### 1. Planner Agent
The Planner receives the user query and breaks it into 2 to 4 independent tasks.

Output format:
STEP N | role=<worker_role> | goal=<task>

This represents task graph generation.

### 2. Worker Agent Registry
The worker system uses a registry pattern:
- research
- analysis
- writer

A worker role is selected by the planner output, then instantiated using the same AutoGen AssistantAgent framework with a role-specific system prompt.

This is the agent registry pattern.

### 3. Parallel Workers
Each worker receives its own isolated task and runs independently.

Implementation uses parallel async execution:
- worker 1
- worker 2
- worker 3
- worker N

This is the executor layer of planner-executor architecture.

### 4. Reflection Agent
The Reflection Agent receives all worker outputs together and improves the draft:
- removes repetition
- combines useful information
- improves structure
- increases readability

### 5. Validator Agent
The Validator reviews the reflected draft and returns:
- STATUS
- ISSUES if needed
- FINAL_ANSWER

This provides the validator stage in the chain.

## Execution Tree

USER
└── PLANNER
    ├── WORKER_1 [research]
    ├── WORKER_2 [analysis]
    └── WORKER_3 [writer]
        ↓
    REFLECTION
        ↓
    VALIDATOR
        ↓
    FINAL ANSWER

## DAG Interpretation
This is a simple DAG-style execution structure:

Planner -> Worker_1
Planner -> Worker_2
Planner -> Worker_3
Worker_1 -> Reflection
Worker_2 -> Reflection
Worker_3 -> Reflection
Reflection -> Validator
Validator -> Final Answer

The workers are sibling nodes and can execute in parallel.

## Why this satisfies Day 2
- multi-agent hierarchy
- delegation logic
- planner-executor pattern
- task graph generation
- agent registry pattern
- parallel worker execution
- execution tree display
- reflection step
- validator step

## Notes
- All agents are built using AutoGen AssistantAgent.
- Local inference is done through LM Studio's OpenAI-compatible endpoint.
- No tools are used yet because tool calling belongs to Day 3.
