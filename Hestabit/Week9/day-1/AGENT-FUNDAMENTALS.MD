l# AGENT-FUNDAMENTALS

## What is an AI Agent?
An AI agent is a role-driven software component that receives input, reasons within its assigned responsibility, and produces an output. Unlike a basic chatbot, an agent is usually designed with a specific function, boundary, and behavior.

## Agent vs Chatbot vs Pipeline
- A chatbot is usually one assistant handling everything in one place.
- A pipeline is a fixed sequence of processing steps.
- An agent system assigns specialized responsibilities to separate intelligent units.

In this Day 1 setup, we use three agents:
1. Research Agent
2. Summarizer Agent
3. Answer Agent

Each agent performs one isolated responsibility.

## Day 1 Goal
Build a message-based communication flow:

User -> Research Agent -> Summarizer Agent -> Answer Agent

This demonstrates:
- role isolation
- message passing
- system prompt control
- multi-step response generation

## Agent Architecture Used
This project uses AutoGen's built-in `AssistantAgent` for all three agents.

Each agent contains:
- a unique name
- a shared local model client
- a unique system prompt
- a buffered context window of 10 messages

## Memory Window = 10
Each agent uses:
`BufferedChatCompletionContext(buffer_size=10)`

This means the agent can only see the last 10 messages in its own visible chat context. This satisfies the Day 1 requirement for a memory window of 10.

## Strict Job Separation
Strict job separation is enforced through system prompts.

### Research Agent
- collects facts
- does not produce final user answer
- does not compress too much

### Summarizer Agent
- compresses research
- does not perform final response formatting
- does not behave as a researcher

### Answer Agent
- produces polished final answer
- does not output raw research notes
- does not re-run research behavior

## Message-Based Communication
The system passes outputs step by step:

1. User query goes to Research Agent
2. Research output goes to Summarizer Agent
3. Summary goes to Answer Agent
4. Answer Agent produces final answer

This is a simple multi-agent communication protocol where each agent receives the previous stage's message as its input.

## Why This Matters
This pattern shows the foundation of larger agent systems:
- specialization
- isolation
- modularity
- easier debugging
- easier scaling into planner-worker-validator systems later

## Local-Only Design
The model is hosted locally through LM Studio.
AutoGen connects to LM Studio through its OpenAI-compatible API endpoint.

This keeps the setup:
- fully local
- compatible with the Week 9 constraints
- independent of paid APIs

## Conclusion
This Day 1 implementation is the base for the rest of the week.
Later days can extend this into:
- orchestration
- tool calling
- memory systems
- reflection loops
- validation flows