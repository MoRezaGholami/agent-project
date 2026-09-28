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
Your ONLY job is to transform the user's project goal and constraints into a practical, high-level architecture.

RULES:
1. REQUIREMENTS FIRST:
   - Preserve the user's explicit functional requirements and constraints.
   - Derive only the components, technologies, and modules needed to satisfy those requirements.
   - Do not add features, infrastructure, or technologies merely because they are common best practices.

2. HARD CONSTRAINTS HAVE PRIORITY:
   - Never violate explicit physical, hardware, platform, legal, or absolute financial constraints.
   - Never invent missing hardware, budget, services, or infrastructure.
   - If a requirement conflicts with a hard constraint, keep the constraint and record the limitation clearly in architecture_decisions.

3. SECURITY FEEDBACK IS ADVISORY:
   - Treat SECURITY FEEDBACK as expert input, not an unconditional instruction.
   - Apply a security recommendation only when it is relevant to the project's actual exposure, data, trust boundaries, or requirements.
   - Do not automatically add authentication, encryption, HTTPS, or other controls when the project context does not justify them.
   - If security feedback conflicts with a hard user constraint, preserve the user constraint and explain the trade-off.

4. NO HALLUCINATED REQUIREMENTS:
   - Do not assume databases, cloud deployment, multi-user access, authentication, APIs, or other infrastructure unless supported by the goal, constraints, or existing context.

5. ARCHITECTURE DECISIONS:
   - Record important choices and the reason they satisfy the requirements or constraints.
   - When information is missing but a reasonable assumption is safe, make the smallest necessary assumption and document it.

Focus on major components, responsibilities, technologies, dependencies, and system boundaries."""),
            ("human", """Project Goal: {goal_description}
Constraints & Context: {constraints}

SECURITY FEEDBACK (if any):
{security_feedback}

Generate the architecture plan based on the project goal and constraints. Evaluate security feedback in context rather than accepting it blindly.""")
        ])


    def invoke(self , goal : ProjectGoal , security_feedback: str = "" ) -> ArchitecturePlan :
        print("[AGENT] Architecture agent started...")
        
        
        context = "\n".join(goal.constraints) if goal.constraints else "None"
        feedback = security_feedback if security_feedback else "None"

        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "goal_description": goal.description,
            "constraints": context,
            "security_feedback": feedback
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
Your job is to convert the approved architecture into an actionable dependency graph of implementation tasks.

RULES:
1. REQUIREMENT COVERAGE:
   - Every proposed task must contribute directly to an explicit project requirement or an architecture component needed to satisfy one.
   - Do not invent unrelated features or infrastructure.

2. TASK GRANULARITY:
   - Make tasks independently understandable and implementable.
   - Avoid both giant vague tasks and unnecessary micro-tasks.
   - There is no fixed task count. Use only as many tasks as the project actually requires.

3. EXISTING WORK:
   - Read the Existing System Context carefully.
   - Do not recreate work that already exists.
   - For an update, output only the new or changed tasks required by the request.
   - Existing task IDs may be used as dependencies.

4. DEPENDENCIES:
   - A dependency is a real prerequisite: the referenced task must be completed before this task can reasonably start.
   - Do not add dependencies merely because tasks are related or happen to be implemented in a common order.
   - Avoid circular dependencies.

5. TASK QUALITY:
   - Prefer clear task titles that identify the concrete deliverable.
   - Keep the task descriptions and other fields aligned with the approved architecture and user goal.

6. NUMBERING:
   - The first new task ID MUST use {next_task_num}, formatted as TXX.
   - Continue sequentially from there.
   - Do not restart from T01 unless {next_task_num} is 1.

Output only the requested structured TaskPlan."""),
            ("human", """Project Goal: {goal_description}

Approved Architecture:
Components: {components}
Technologies: {technologies}

Existing System Context (from MCP):
{mcp_context}

Create the smallest complete set of NEW tasks required to implement the goal according to the approved architecture. The first new task ID must be based on {next_task_num}.""")
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
            ("system", """You are a strict Technical Reviewer evaluating whether a proposed task plan is consistent with the user's request and the approved architecture.

Use evidence from the provided context. Do not reject a plan merely because you would personally design it differently.

REVIEW PRIORITY:
1. HUMAN REVIEW:
   Set status to 'human_review' when the proposed plan contains destructive or difficult-to-reverse actions (for example data deletion, destructive migrations, replacement of major working subsystems), or when a high-impact security/architectural decision cannot be evaluated safely from the provided information.
   Explain exactly what the human must verify.

2. DETERMINISTIC VALIDATION:
   If Validation Tool Errors are present and no higher-priority human-review condition applies, set status to 'needs_revision' and include the errors.

3. REQUIREMENT AND ARCHITECTURE CONSISTENCY:
   Check whether the tasks collectively address the user's explicit goal and required architecture components.
   Flag missing work only when it is required by the user request or directly necessary to satisfy an approved architecture decision.
   Do not require optional best practices that were not requested.

4. DEPENDENCIES:
   - Dependencies must refer only to real prerequisite tasks.
   - Existing task IDs are valid dependencies.
   - Do not reject a plan merely because it depends on an existing task.
   - Look for missing prerequisites and circular dependencies.

5. LOGICAL ORDER:
   Ensure the order is broadly workable, but do not enforce arbitrary stylistic ordering.
   Normal implementation flexibility and reasonable DevOps ordering are acceptable.

6. APPROVAL:
   If there is no human-review trigger, no deterministic validation error, and no material requirement/architecture/dependency problem, set status to 'approved'.

Never reject a valid plan based only on subjective architectural preferences."""),
            ("human", """User Project Goal:
{goal_description}

Project Constraints:
{constraints}

Approved Architecture:
Components: {components}
Technologies: {technologies}
Decisions: {decisions}

Existing Tasks (From DB):
{mcp_context}

Proposed Task List:
{tasks}

Validation Tool Errors (Deterministic):
{tool_errors}

Review the proposed plan against the user's actual requirements and the approved architecture. Provide the structured verdict and concrete reasons.""")
        ])



    def invoke(self, goal: ProjectGoal, architecture: ArchitecturePlan, task_plan: TaskPlan, tool_errors: list[str], mcp_context: str = "None") -> ReviewResult:
        print("[AGENT] Reviewer Agent started...")
        formatted_tasks = "\n".join(
            [f"[{t.task_id}] {t.title} (Deps: {t.dependencies})" for t in task_plan.tasks]
        )
        formatted_errors = "\n".join(tool_errors) if tool_errors else "No validation errors found by tools."
        constraints = "\n".join(goal.constraints) if goal.constraints else "None"
        decisions = "\n".join(architecture.architecture_decisions) if architecture.architecture_decisions else "None"

        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "goal_description": goal.description,
            "constraints": constraints,
            "components": ", ".join(architecture.components),
            "technologies": ", ".join(architecture.technologies),
            "decisions": decisions,
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
            ("system", """You are a Cybersecurity Expert reviewing an application's proposed architecture.
Your ONLY responsibility is architectural security.

RULES:
1. REVIEW IN CONTEXT:
   - Use the project goal, constraints, technologies, components, and architecture decisions.
   - Consider the actual attack surface, trust boundaries, data sensitivity, network exposure, authentication/authorization needs, external integrations, and deployment context when those are known.

2. DO NOT USE A GENERIC CHECKLIST AS A REJECTION RULE:
   - The absence of authentication, encryption, HTTPS, or another common control is not automatically a vulnerability.
   - Recommend a control only when the project context creates a meaningful security requirement or risk.

3. DISTINGUISH RISK FROM PREFERENCE:
   - Flag concrete or strongly justified vulnerabilities.
   - Do not request enterprise-grade controls for a small/local project without evidence that they are necessary.
   - Do not invent threat actors, sensitive data, public exposure, or compliance requirements.

4. CONSTRAINTS:
   - Respect explicit user constraints.
   - If a security improvement conflicts with a hard constraint, describe the risk and the feasible mitigation rather than pretending the constraint does not exist.

5. VERDICT:
   - If a material architectural security problem exists, set status to 'needs_revision', list the issue, and provide actionable suggested_changes.
   - If no material security problem is identified from the provided evidence, set status to 'approved'.
   - Do not evaluate task ordering, implementation quality, or non-security architecture preferences."""),
            ("human", """Project Goal: {goal_description}
Project Constraints: {constraints}

Proposed Architecture:
Components: {components}
Technologies: {technologies}
Decisions: {decisions}

Review this architecture for material security vulnerabilities and risks. Base every finding on the provided project context.""")
        ])


    def invoke(self, goal: ProjectGoal, architecture: ArchitecturePlan) -> ReviewResult:
        print("[AGENT] Security Agent is reviewing the architecture...")
        constraints = "\n".join(goal.constraints) if goal.constraints else "None"
        decisions = "\n".join(architecture.architecture_decisions) if architecture.architecture_decisions else "None"
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "goal_description": goal.description,
            "constraints": constraints,
            "components": ", ".join(architecture.components),
            "technologies": ", ".join(architecture.technologies),
            "decisions": decisions
        })



class TechLeadAgent :
    """
    Role: Chief Technology Officer (CTO) / Tech Lead
    Responsibility: Resolves deadlocks between Architecture Agent and Security Agent by making pragmatic trade-offs.
    """

    def __init__(self , llm : BaseChatModel) :
        self.llm_with_structure = llm.with_structured_output(ArchitecturePlan)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the CTO / Tech Lead resolving a disagreement between the Architecture Agent and Security Agent.

Your job is to produce the final architecture that best satisfies the user's actual requirements while addressing material security risks that are feasible within the stated constraints.

RULES:
1. USER REQUIREMENTS AND HARD CONSTRAINTS:
   - Preserve explicit functional requirements and hard constraints.
   - Never invent budget, hardware, services, infrastructure, or capabilities.

2. SECURITY MUST BE PROPORTIONAL:
   - Do not blindly accept or reject Security Agent recommendations.
   - Choose controls based on actual risk, project exposure, data sensitivity, and scope.
   - Do not use vague standards such as "good enough" without explaining the concrete trade-off.

3. CONFLICT RESOLUTION:
   - For each unresolved issue, choose the simplest feasible design that addresses the material risk without violating hard constraints.
   - If a desired security control is infeasible, retain the constraint, document the residual risk, and use the strongest practical mitigation available within the project limits.

4. NO SCOPE CREEP:
   - Do not add unrelated features or enterprise infrastructure just to make the architecture look more complete.

5. FINAL OUTPUT:
   - Return a coherent architecture, not a debate.
   - Record important trade-offs and limitations in architecture_decisions."""),
            ("human", """Project Goal:
{goal}

Project Constraints:
{constraints}

Last Proposed Architecture (by Architect):
{arch_plan}

Unresolved Security Issues (by Security Agent):
{security_issues}

Resolve the disagreement using the user's requirements and constraints. Produce the final practical architecture and document any important security trade-offs or residual risks.""")
        ])


    def invoke(self , goal : ProjectGoal , architecture: ArchitecturePlan, security_issues: list) -> ArchitecturePlan :
        print("[AGENT] Tech Lead Agent (CTO) is analyzing the deadlock...")


        issues_text = "\n".join([f"- {iss.description}" for iss in security_issues]) if security_issues else "None"
        arch_text = (
            f"Components: {architecture.components}\n"
            f"Technologies: {architecture.technologies}\n"
            f"Decisions: {architecture.architecture_decisions}"
        )
        constraints = "\n".join(goal.constraints) if goal.constraints else "None"

        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "goal": goal.description,
            "constraints": constraints,
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
            ("system", """You are an expert Product Manager reviewing a software project request for planning readiness.

Your goal is NOT to collect every possible detail. Your goal is to identify only missing information that materially prevents a reasonable architecture or task plan.

RULES:
1. Set 'is_clear' to True when the request contains enough information to make a reasonable plan without risky or major assumptions.
2. Set 'is_clear' to False only when a missing detail could materially change the architecture, technology choice, implementation scope, or a hard constraint.
3. Ask at most 3 targeted questions, ordered by importance.
4. Ask questions only about information that cannot reasonably be inferred or safely deferred.
5. Do not ask generic questions just because they are common. For example, do not ask about budget, database, deployment, or platform unless that specific detail materially affects this project.
6. Prefer concrete questions tied to the user's actual request.
7. Do not invent assumptions when an unanswered question could cause a major architectural difference."""),
            ("human", "User Request: {user_request}")
        ])

    def invoke(self, user_request: str) -> ClarificationResult:
        print("[AGENT] Clarifier Agent (Product Manager) is evaluating the request...")
        chain = self.prompt | self.llm_with_structure
        return chain.invoke({"user_request": user_request})



class ImplementationTutorAgent:
    """
    Role: Senior Software Architect
    Responsibility: Generates SKELETON code and boilerplate to demonstrate architecture and dependencies, avoiding full business logic implementation.
    """
    def __init__(self, llm):
        self.llm_with_structure = llm.with_structured_output(TaskImplementation)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Senior Software Architect generating a SKELETON source file for an implementation task.

Your goal is to demonstrate the intended project structure, interfaces, and dependencies without implementing full business logic.

RULES:
1. APPROVED STACK:
   - Use only technologies and libraries supported by the Approved Architecture Stack.
   - Do not introduce new frameworks, libraries, or runtimes unless they already appear in the approved stack or existing codebase.

2. LANGUAGE AND SYNTAX:
   - Generate syntactically valid code for the target language implied by the approved stack and project structure.
   - Follow the conventions of that language.
   - Never mix syntax, comment styles, placeholder syntax, or documentation conventions from another language.
   - Use documentation only when it is idiomatic for the target language; do not use Python docstrings in non-Python files.

3. SKELETON SCOPE:
   - Define the required classes, functions, methods, interfaces, types, and imports.
   - Demonstrate architectural relationships and dependency usage.
   - Do not implement complete business logic, algorithms, persistence behavior, networking behavior, or external integrations unless a minimal stub is necessary to show the interface.
   - Use placeholders that are legal in the target language.

4. EXISTING CODEBASE:
   - Treat the Existing Codebase as the source of truth for existing files, symbols, modules, and dependencies.
   - Only import or reference classes/functions that are actually present in the provided codebase or are standard parts of the selected language/runtime.
   - Do not invent filenames, classes, functions, packages, or APIs and pretend they already exist.
   - If a required dependency is missing, represent the dependency conservatively and do not fabricate an existing implementation.

5. FILENAME:
   - Choose a logical filename and the correct extension for the target language.
   - Keep naming consistent with the existing project structure when that information is available.

6. VALID SOURCE:
   - The generated `code` must be valid source code for the target language even though it is only a skeleton.
   - Do not rely on invalid placeholders.
   - Do not wrap the source code in Markdown fences.

7. OUTPUT:
   - Return only the requested structured TaskImplementation."""),
            ("human", """Approved Architecture Stack: {tech_stack}
Task Title: {task_title}

=== Existing Codebase ===
{existing_codebase}
=========================

{error_context}

Generate the skeleton code file.""")
        ])

    def invoke(self, task_title: str, tech_stack: str, existing_codebase: str, error_feedback: str = "") -> TaskImplementation:
        print(f"\n[TUTOR] 🏗️ Generating skeleton code for task: '{task_title}'...")
        error_context = ""
        if error_feedback:
            error_context = f"🚨 PREVIOUS ATTEMPT FAILED. FIX THIS ERROR:\n{error_feedback}"

        chain = self.prompt | self.llm_with_structure
        return chain.invoke({
            "tech_stack": tech_stack, 
            "task_title": task_title, 
            "existing_codebase": existing_codebase if existing_codebase else "No files created yet.",
            "error_context": error_context
        })





