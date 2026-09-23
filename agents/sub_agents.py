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
1. 'dependencies' must only contain IDs of tasks that MUST be completed before the task can start.
2. Be granular but avoid micro-management (aim for 5-15 major tasks).
3. Do not recreate tasks that already exist in the 'Existing System Context'. ONLY output the NEW tasks required for the update.
4. CRITICAL NUMBERING RULE: You MUST start your task numbering strictly using the number {next_task_num} (formatted as TXX, e.g., if {next_task_num} is 12, start with T12, then T13). Do NOT start from T01 unless {next_task_num} is 1.

Output strictly in the requested JSON format."""),
            ("human", """Project Goal: {goal_description}

Approved Architecture:
Components: {components}
Technologies: {technologies}

Existing System Context (from MCP):
{mcp_context}

Generate the Task Plan graph. The first new task ID must be based on {next_task_num}.""")
        ])

    def invoke(self, goal: ProjectGoal, architecture: ArchitecturePlan, mcp_context: str = "None", next_task_num: int = 1) -> TaskPlan:
        print(f"[AGENT] Task Planner Agent started... (Starting Task ID: T{next_task_num:02d})")
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "goal_description": goal.description,
            "components": ", ".join(architecture.components),
            "technologies": ", ".join(architecture.technologies),
            "mcp_context": mcp_context,
            "next_task_num": next_task_num
        })


        
        




class ReviewerAgent:
    """
    Role: Strict Technical Reviewer
    Responsibility: Evaluate the task plan, architecture, and deterministic validation results to approve or reject the plan.
    """


    def __init__(self , llm : BaseChatModel):
        self.llm_with_structure = llm.with_structured_output(ReviewResult)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Technical Reviewer evaluating a proposed Project Plan.
You will be provided with the Architecture, the Task List, Existing Tasks (from DB), and 'Deterministic Validation Tools' output.

Rules for approval (STRICTLY FOLLOW THESE):
1. If 'Validation Tool Errors' is not empty, you MUST set status to 'needs_revision' and list the errors.
2. Check if the task order makes basic logical sense. HOWEVER, do not be overly pedantic about DevOps task ordering (e.g., CI/CD setup depending on testing setup is perfectly valid and standard).
3. ONLY flag missing tasks (like deployment or testing) if they were explicitly requested in the user's prompt but are completely absent from both Existing Tasks and Proposed Tasks. Do not force them if not requested.
4. CRITICAL: Tasks can depend on IDs from 'Existing Tasks'. This is 100% valid.
5. 🚨 CRITICAL HUMAN REVIEW TRIGGER: If the proposed plan involves destructive actions (e.g., deleting data, major refactoring), OR if you are highly uncertain about a security/architectural decision, you MUST set status to 'human_review' and explain what you need the human to verify.
6. If the proposed plan solves the user's goal and has NO Validation Tool Errors, you MUST set status to 'approved'. Do not reject valid plans based on subjective architectural opinions."""),
            ("human", """Architecture Components: {components}

Existing Tasks (From DB):
{mcp_context}

Proposed Task List:
{tasks}

Validation Tool Errors (Deterministic):
{tool_errors}

Review the plan and provide your structured verdict.""")
        ])



    def invoke(self, architecture: ArchitecturePlan, task_plan: TaskPlan, tool_errors: list[str], mcp_context: str = "None") -> ReviewResult:
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
            "tool_errors": formatted_errors,
            "mcp_context": mcp_context  
        })


class SecurityAgent:
    """
    Role: Cybersecurity Analyst
    Responsibility: Agent-to-Agent debate. Critiques the Architecture Plan for vulnerabilities.
    """

    def __init__(self , llm : BaseChatModel):
        self.llm_with_structure = llm.with_structured_output(ReviewResult)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Cybersecurity Expert. 
Your ONLY job is to review the proposed Architecture Plan from the Architecture Agent.
Rules:
1. Look for glaring security holes (e.g., missing authentication, no encryption, plaintext data, HTTP instead of HTTPS).
2. If the architecture is insecure, set status to 'revise', list the issues, and provide actionable suggested_changes.
3. If it looks solid and secure, set status to 'approve'.
4. Do NOT complain about missing DevOps tasks or task ordering; focus ONLY on architectural security."""),
            ("human", """Proposed Architecture:
Components: {components}
Technologies: {technologies}
Decisions: {decisions}

Review this architecture for security vulnerabilities.""")
        ])


    def invoke(self, architecture: ArchitecturePlan) -> ReviewResult:
        print("[AGENT] Security Agent is reviewing the architecture...")
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "components": ", ".join(architecture.components),
            "technologies": ", ".join(architecture.technologies),
            "decisions": "\n".join(architecture.architecture_decisions)
        })


    




