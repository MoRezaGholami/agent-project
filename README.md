# 🤖 Autonomous Agentic Project Planner

An advanced, multi-agent AI system designed to autonomously plan, validate, and manage software development projects. Built with Python, LangChain, and Streamlit, this system acts as a virtual project manager that generates tasks, resolves dependencies, and strictly validates logic before persisting data.

---

## ✨ Key Features

* **Multi-Agent Architecture**: Utilizes specialized LLM agents (`Orchestrator`, `TaskPlanner`, `Reviewer`) to divide and conquer complex planning tasks.
* **Model Context Protocol (MCP)**: Implements a custom MCP Server to create a strict architectural boundary between the AI's reasoning and the deterministic file system/database.
* **Incremental Planning**: Supports updating existing projects dynamically. The system intelligently reads the current state, appends new tasks, and continues numbering seamlessly.
* **Deterministic Validation**: Before any plan is approved, pure Python deterministic tools run topological sorting (Kahn's Algorithm) and Cycle Detection (DFS) to ensure the dependency graph is mathematically valid.
* **Dual Interface**: Run the system either via a rich CLI for deep execution logs, or via a beautiful Streamlit UI for visual graph rendering.

---

## 🏗️ System Architecture

1. **Orchestrator Agent**: Parses the user's intent, identifies project constraints, and routes the workflow.
2. **Task Planner Agent**: Generates a dependency-aware list of tasks based on the user's requirements and the existing database context.
3. **Deterministic Tools**: Python functions that mathematically validate the proposed graph (Dependency Checker & Cycle Detector).
4. **Reviewer Agent**: The strict QA gatekeeper that reviews the plan and the deterministic tool outputs to either `APPROVE` or `REJECT` the workflow.
5. **MCP Server**: The single source of truth for saving and retrieving tasks from `project_db.json`.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* OpenAI API Key (or equivalent LLM provider)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/MoRezaGholami/agent-project.git
cd agent-project
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up your environment variables:

Create a `.env` file in the root directory and add your API key:

```env
OPENAI_API_KEY=your_api_key_here
```

---

## 🎮 Usage

This project supports two execution modes:

### Mode 1: CLI (Terminal Mode)

Best for seeing detailed execution logs, multi-agent reasoning steps, and deterministic validation outputs in real-time.

```bash
python main.py
```

*(To change the project request, edit the `demo_prompt` variable inside `main.py`.)*

### Mode 2: Streamlit Dashboard (UI Mode)

Best for presentations. It provides a visual dashboard to interact with the agents, view all projects in the database, and render beautiful Markdown/Mermaid dependency graphs.

```bash
streamlit run app.py
```

---

## 🗄️ Database

All project tasks and graphs are safely stored locally in `project_db.json`. If you want to perform a factory reset, simply delete this file; the MCP server will automatically regenerate a clean database on the next run.
