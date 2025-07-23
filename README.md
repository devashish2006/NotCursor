# 🤖 NotCursor — AI-Powered Agentic Coding Assistant

**CodeAgent** is an advanced AI developer assistant that combines powerful LLMs, agentic workflows, and real-time context management to help developers write, debug, refactor, and understand code — just like having an AI pair programmer.

---

## 🧠 Core Capabilities

- ✨ **Context-Aware Code Editing** — Smart code suggestions, completions, and inline explanations.
- 🔁 **Agentic Pipeline** — Multi-agent reasoning system handles tasks like bug detection, test generation, and documentation.
- 💡 **Auto Refactor** — Detects inefficiencies and suggests structured improvements.
- 📚 **Context Memory** — Retains project-wide context using **Mem0** + **QuadrantDB** for relevant suggestions.
- 📎 **Codebase Navigation** — Jump between functions, references, and files with vector-powered search.
- 🧩 **Interactive Chat Window** — Conversational coding experience with live file access.
- 🔍 **Explain / Debug Any Snippet** — Ask "What does this do?" or "Fix this bug" on any code block.

---

## 🧬 Agent Architecture

> Uses an agent-based planning system for handling developer queries with modular reasoning units.

### Agent Pipeline

```mermaid
graph LR
A[User Prompt] --> B[Intent Classifier Agent]
B --> C[Retriever Agent (Mem0 + QuadrantDB)]
C --> D[Planner Agent]
D --> E[Execution Agent (LLM - GPT-4)]
E --> F[Code Output / Action]
