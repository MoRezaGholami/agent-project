from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

from models.schemas import (
    ProjectGoal,
    ArchitecturePlan,
    TaskPlan,
    ReviewResult

)

class ArchitectureAgent:
    """
    Role: Senior Software Architect
    Responsibility: Translate a high-level goal into a structured system architecture.
    """

    def __init__(self , llm : BaseChatModel):
        self.llm_with_structure = llm.with_structured_output(ArchitecturePlan)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Software Architect. 
            Your ONLY job is to analyze the user's project goal and output a structured high-level architecture.
            DO NOT write essays. DO NOT write code. 
            Focus on identifying major components, technologies, and system modules.
            If there are strict constraints, you MUST respect them."""),
                        ("human", """Project Goal: {goal_description}
            Constraints: {constraints}

            Generate the architecture plan.""")
        ])


    def invoke(self , goal : ProjectGoal) -> ArchitecturePlan :
        print("[AGENT] Architecture agent started...")
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "goal_description": goal.description,
            "constraints": "\n".join(goal.constraints) if goal.constraints else "None"
        })

class TaskPlannerAgent:
    """
    Role: Technical Project Manager
    Responsibility: Break down the architecture into a dependency graph of actionable tasks.
    """

    def __init__(self , llm : BaseChatModel):
        self.llm_with_structure = llm.with_structured_output(TaskPlan)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Technical Project Manager.
Your job is to break down a software architecture into a logical sequence of tasks.
Rules:
1. Each task must have a unique ID (e.g., T01, T02).
2. 'dependencies' must only contain IDs of tasks that MUST be completed before the task can start.
3. Be granular but avoid micro-management (aim for 5-15 major tasks).
4. Pay attention to 'Existing System Context'. Do not recreate tasks that already exist in the external system.
Output strictly in the requested JSON format."""),
            ("human", """Project Goal: {goal_description}

Approved Architecture:
Components: {components}
Technologies: {technologies}

Existing System Context (from MCP):
{mcp_context}

Generate the Task Plan graph.""")
        ])

    def invoke(self , goal : ProjectGoal , architecture: ArchitecturePlan, mcp_context: str = "None") -> TaskPlan:
        print("[AGENT] Task Planner Agent started...")
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "goal_description": goal.description,
            "components": ", ".join(architecture.components),
            "technologies": ", ".join(architecture.technologies),
            "mcp_context": mcp_context
        })


        
        




class ReviewerAgent:
    """
    Role: Strict Technical Reviewer
    Responsibility: Evaluate the task plan, architecture, and deterministic validation results to approve or reject the plan.
    """


    def __init__(self , llm : BaseChatModel):
        self.llm_with_structure = llm.with_structured_output(ReviewResult)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strict, detail-oriented Technical Reviewer.
Your job is to review a proposed Project Plan.
You will be provided with the Architecture, the Task List, and the output of 'Deterministic Validation Tools' (e.g., cycle detectors).

Rules for approval:
1. If 'Validation Tool Errors' is not empty, you MUST set status to 'needs_revision' and include those errors in your issues.
2. Check if the task order makes logical sense (e.g., Database must exist before API).
3. If tasks are missing for core components (e.g., no testing, no deployment), flag them.
4. If the plan is solid, set status to 'approved'.
Do NOT blindly approve everything."""),
            ("human", """Architecture Components: {components}

Proposed Task List:
{tasks}

Validation Tool Errors (Deterministic):
{tool_errors}

Review the plan and provide your structured verdict.""")
        ])



    def invoke(self, architecture: ArchitecturePlan, task_plan: TaskPlan, tool_errors: list[str]) -> ReviewResult:
        print("[AGENT] Reviewer Agent started...")
        # Format tasks for the prompt
        formatted_tasks = "\n".join(
            [f"[{t.task_id}] {t.title} (Deps: {t.dependencies})" for t in task_plan.tasks]
        )
        formatted_errors = "\n".join(tool_errors) if tool_errors else "No logic errors found by tools."
        
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "components": ", ".join(architecture.components),
            "tasks": formatted_tasks,
            "tool_errors": formatted_errors
        })



