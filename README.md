# 🤖 Autonomous Software Planning & Orchestration System

An advanced, multi-agent AI system designed to autonomously plan, architect, validate, and scaffold software projects from high-level user requirements.

Built with **LangChain** and **Pydantic**.

---

## ✨ Key Features

This system goes beyond basic text generation by implementing complex workflow logic, graph validation, and state management.

* **👥 Multi-Agent Collaboration**
  Utilizes specialized AI agents with distinct roles (Product Manager, Architect, Security Expert, CTO, Project Manager, Reviewer, and Tutor) to tackle different phases of project planning.

* **🗣️ Agent-to-Agent Debate & Resolution**
  The *Architecture Agent* and *Security Agent* debate structural decisions. If a deadlock occurs (e.g., security demands exceed budget constraints), the *Tech Lead (CTO) Agent* steps in to make executive trade-offs.

* **🧠 Hybrid Validation System**

  * **AI Review:** Subjective review of architecture and logic.
  * **Deterministic Tools:** Uses formal graph algorithms to validate task dependencies, detect circular dependencies (DFS), calculate execution order (Topological Sort / Kahn's Algorithm), and estimate project duration (Critical Path).

* **🏗️ Autonomous Code Scaffolding**
  Automatically generates foundational project files (boilerplate/skeleton code) based on the approved architecture stack, safely writing them to the local OS via the `WorkspaceManager`.

* **🩹 Self-Healing & Bounded Replanning**
  Captures generation or validation errors and feeds them back to the LLM for self-correction. Uses a controlled replanning loop (`MAX_REPLAN_ROUNDS`) to prevent infinite generation cycles.

* **🛑 Human-in-the-Loop (HITL)**

The system supports Human-in-the-Loop (HITL) interactions at different stages of the workflow:

* Clarification:
  If the **Clarifier Agent** determines that the user's request is too vague or lacks essential requirements, the workflow pauses and asks the user for additional information before planning begins.

* High-Risk Decisions:
  If the **Reviewer Agent** detects a potentially destructive or high-risk operation, such as deleting an existing database, the workflow pauses and asks the user to either approve the operation or request a replan.

  If the user requests a replan, their feedback is passed to the **Task Planner Agent** as an error or additional constraint. The Task Planner then generates a revised task plan based on the user's feedback, which goes through the validation and review process again before execution continues.


* **🔌 Simulated MCP (Model Context Protocol)**
  Uses a mock MCP Server and Client to strictly manage external state, database interactions (saving tasks), and external tool execution (like fetching live web tutorials).

---

## 🧩 The Virtual Team

1. **Clarifier Agent (PM)**
   Evaluates user input for vagueness and asks clarifying questions before starting.

2. **Orchestrator Agent**
   Extracts core constraints, determines complexity (`SIMPLE` vs. `COMPLEX`), and sets the execution mode.

3. **Architecture Agent**
   Drafts the initial system architecture, tech stack, and module breakdown.

4. **Security Agent**
   Reviews the architecture for vulnerabilities and demands fixes.

5. **Tech Lead Agent (CTO)**
   Resolves disputes between Architecture and Security agents.

6. **Task Planner Agent**
   Breaks down the approved architecture into a granular, dependency-linked task graph.

7. **Reviewer Agent**
   Strict evaluator that checks the task plan against constraints and deterministic tool errors.

8. **Implementation Tutor Agent**
   Generates the actual skeleton code files based on the task list and tech stack.

---

## ⚙️ System Workflow

1. **Pre-Planning:** Clarifier ensures the prompt is actionable.
2. **Orchestration:** Extracts constraints and determines project complexity.
3. **Architecture Debate:** For complex projects, Architect and Security agents iterate on a design. CTO resolves deadlocks.
4. **Planning Loop:** Task Planner generates tasks → Validation Tools check for cycles/errors → Reviewer approves or rejects. The process loops until valid or the maximum retry limit is reached.
5. **Scaffolding Phase:** Generates physical files (`.py`, `.js`, etc.) into the `project_workspaces/` directory.
6. **Finalization:** Generates a comprehensive `README.md` for the generated project and prints a detailed terminal report, including web resources fetched via MCP.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* An OpenAI API Key (or compatible endpoint like Avalai)

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install the required dependencies:

```bash
pip install langchain-core langchain-openai pydantic python-dotenv google
```

> **Note:** Ensure all dependencies imported in the codebase are installed.

3. Create a `.env` file in the root directory and add your API key:

```env
OPENAI_API_KEY=your_api_key_here
```

### Usage

Run the main execution file:

```bash
python main.py
```

By default, `main.py` uses a demo prompt:

> "Create a new project exactly named 'weather_cli_app'..."

You can modify the `demo_prompt` variable in `main.py` to test different software requests, complexities, and constraints.

---

## 📁 Project Structure

| File                        | Description                                                                                    |
| --------------------------- | ---------------------------------------------------------------------------------------------- |
| `main.py`                   | Entry point. Initializes the LLM, MCP Server/Client, and triggers the WorkflowRunner.          |
| `harness/runner.py`         | Core workflow engine managing state transitions, loops, error boundaries, and agent execution. |
| `agents/orchestrator.py`    | Contains the initial planning and routing agent.                                               |
| `agents/sub_agents.py`      | Contains all specialized role-playing agents (Architect, Security, TaskPlanner, etc.).         |
| `mcp/server.py`             | Simulates the Model Context Protocol, handling local JSON database I/O and web search tools.   |
| `tools/validation_tools.py` | Deterministic algorithms (DFS, Kahn's Algorithm) for graph and dependency validation.          |
| `tools/utils.py`            | OS-level operations (`WorkspaceManager`) for safely writing generated code files.              |
| `models/schemas.py`         | Pydantic models enforcing strict input/output structures for LLM structured outputs.           |

---

## 🛡️ Error Handling & Limits

* **API Rate Limits:** Built-in `429` error detection and graceful sleep/retry logic (`MAX_API_RETRIES`).

* **Graceful Degradation:** If an agent repeatedly fails or hallucinates technologies outside the approved stack, the system logs the error and halts gracefully rather than crashing.

