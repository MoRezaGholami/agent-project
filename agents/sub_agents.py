from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

from models.schemas import (
    ProjectGoal,
    ArchitecturePlan,
    TaskPlan,
    ReviewResult,
    ClarificationResult,
    TaskImplementation

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

CRITICAL RULES FOR CONFLICTS:
1. You must normally try to resolve 'SECURITY FEEDBACK' by adding modern security practices (encryption, auth, HTTPS).
2. 🛑 UNBREAKABLE LIMITS: You CANNOT violate strict physical, hardware, or absolute financial constraints explicitly set by the user (e.g., "hardware physically cannot process SSL", "budget is absolutely $0"). 
3. If the Security Agent demands something that violates an UNBREAKABLE LIMIT, you MUST hold your ground! Do not magically upgrade hardware or invent budget. Keep the architecture within the user's physical limits and state this constraint clearly in your 'architecture_decisions'.

Focus on identifying major components, technologies, and system modules."""),
            ("human", """Project Goal: {goal_description}
Constraints & Context: {constraints}

Generate the architecture plan.""")
        ])


    def invoke(self , goal : ProjectGoal , security_feedback: str = "" ) -> ArchitecturePlan :
        print("[AGENT] Architecture agent started...")
        
        
        context = "\n".join(goal.constraints) if goal.constraints else "None"
        if security_feedback:
            context += f"\n\n🚨 CRITICAL SECURITY FEEDBACK FROM PREVIOUS ROUND (YOU MUST FIX THESE):\n{security_feedback}"
            
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "goal_description": goal.description,
            "constraints": context
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
2. If the architecture is insecure, set status to 'needs_revision', list the issues, and provide actionable suggested_changes.
3. If it looks solid and secure, set status to 'approved'.
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



class TechLeadAgent :
    """
    Role: Chief Technology Officer (CTO) / Tech Lead
    Responsibility: Resolves deadlocks between Architecture Agent and Security Agent by making pragmatic trade-offs.
    """

    def __init__(self , llm : BaseChatModel) :
        self.llm_with_structure = llm.with_structured_output(ArchitecturePlan)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Chief Technology Officer (CTO).
The Architecture Agent and Security Agent have reached a DEADLOCK. They cannot agree on a design that satisfies both the User's constraints and strict Security standards.

Your job is to act as the Mediator and make the FINAL executive decision.
Rules:
1. Make pragmatic trade-offs: Balance business reality (cost, performance, user constraints) with acceptable security.
2. If the security demands are unrealistic for the project scope (e.g., Enterprise security on a $0 budget), explicitly downgrade the security to a "good enough" standard.
3. If the user's constraints are fundamentally illegal/dangerous, enforce basic security but keep it as lightweight as possible.
4. Output the FINAL, compromised Architecture Plan."""),
            ("human", """Project Goal & User Constraints:
{goal}

Last Proposed Architecture (by Architect):
{arch_plan}

Unresolved Security Issues (by Security Agent):
{security_issues}

As the CTO, resolve this conflict and output the final practical architecture.""")
        ])



    def invoke(self , goal : ProjectGoal , architecture: ArchitecturePlan, security_issues: list) -> ArchitecturePlan :
        print("[AGENT] Tech Lead Agent (CTO) is analyzing the deadlock...")


        issues_text = "\n".join([f"- {iss.description}" for iss in security_issues])
        
        
        arch_text = f"Components: {architecture.components}\nTech: {architecture.technologies}"
        
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "goal": goal.description,
            "arch_plan": arch_text,
            "security_issues": issues_text
        })



class ClarifierAgent:
    """
    Role: Product Manager
    Responsibility: Analyzes the initial request to ensure it's actionable and not too ambiguous before planning starts.
    """

    def __init__(self, llm):
        
        self.llm_with_structure = llm.with_structured_output(ClarificationResult)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Product Manager. Your job is to review the user's software project request.
If the request is too vague (e.g., "build a store app" or "make a game"), set 'is_clear' to False and ask 1 to 3 targeted technical questions (e.g., target platforms, database preference, budget).
If the request is already detailed enough to derive components and constraints, set 'is_clear' to True.
DO NOT ask questions if the user has provided a reasonable amount of constraints. Be pragmatic."""),
            ("human", "User Request: {user_request}")
        ])

    def invoke(self, user_request: str) -> ClarificationResult:
        print("[AGENT] Clarifier Agent (Product Manager) is evaluating the request...")
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({"user_request": user_request})



class ImplementationTutorAgent:
    """
    Role: Senior Developer / Tutor
    Responsibility: Generates starter code or tutorial files for complex tasks.
    """

    def __init__(self, llm: BaseChatModel):
        self.llm_with_structure = llm.with_structured_output(TaskImplementation)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Senior Developer bootstrapping a project.
For the given task, generate EITHER starter code OR a detailed text tutorial.

CRITICAL RULES:
1. You MUST STRICTLY adhere to the Approved Architecture Stack. 
2. Do NOT use or suggest technologies outside the approved stack.
3. Provide a logical filename with the correct extension (e.g., .py, .js, .txt, .md)."""),
            ("human", """Approved Architecture Stack: {tech_stack}
Task Title: {task_title}

{error_context}

Generate the implementation file.""")
        ])

    def invoke(self, task_title: str, tech_stack: str, error_feedback: str = "") -> TaskImplementation:
        print(f"\n[TUTOR] 🧑‍💻 Writing implementation for task: '{task_title}'...")
        error_context = ""
        if error_feedback:
            error_context = f"🚨 PREVIOUS ATTEMPT FAILED. FIX THIS ERROR:\n{error_feedback}"

        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "tech_stack": tech_stack, 
            "task_title": task_title, 
            "error_context": error_context
        })





