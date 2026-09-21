#i have to redesign orchestrator file for my new agent plan.
from pydantic import Field , BaseModel
from models.schemas import ProjectGoal , ProjectComplexity , ExecutionMode
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

#این کلاس واسه تسهیل در تصمیم گیری های orchestrator ساخته میشه.

class OrchestrationDecision(BaseModel):
    goal : ProjectGoal = Field(..., description="The parsed and structured project goal including constraints.")
    complexity: ProjectComplexity = Field(..., description="SIMPLE or COMPLEX based on the request.")
    mode: ExecutionMode = Field(..., description="Execution mode: FAST, STANDARD, or THOROUGH.")
    project_name: str = Field(..., description="A short, snake_case identifier for this specific project (e.g., 'django_api', 'merge_sort').")
    reasoning: str = Field(..., description="Short explanation for why this complexity was chosen.")


class OrchestratorAgent:
    """
    Role: Lead Project Director (Orchestrator)
    Responsibility: Understand user intent, extract constraints, and determine the workflow path.
    """

    def __init__(self , llm : BaseChatModel):
        self.llm_with_structure = llm.with_structured_output(OrchestrationDecision)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Lead Project Director of an Autonomous Software Planning System.
Your job is to analyze the user's initial request.

Rules:
1. Extract the main goal and constraints.
2. Determine complexity (SIMPLE or COMPLEX).
3. Determine execution mode (FAST, STANDARD, THOROUGH):
   - FAST: Quick scripts, minor updates, user asks for rapid results.
   - STANDARD: Normal development workflows.
   - THOROUGH: Enterprise architecture, security-critical features, high reliability needs.
4. Provide reasoning.
5. Generate a short, snake_case 'project_name'. CRITICAL: If the user is asking to UPDATE or ADD features to an existing project, you MUST guess the original base project name and use it exactly (e.g., use 'django_course_management' DO NOT add words like '_update' or '_new').

Do not write tasks or architecture here. Just route the request."""),
            ("human", "User Request: {user_request}")
        ])


    def invoke(self , user_request : str) -> OrchestrationDecision :
        print(f"[ORCHESTRATOR] Analyzing user request: '{user_request[:50]}...'")
        chain = self.prompt | self.llm_with_structure
        result = chain.invoke({"user_request": user_request})
        
        print(f"[ORCHESTRATOR] Goal Parsed. Constraints found: {len(result.goal.constraints)}")
        print(f"[ORCHESTRATOR] Routing Decision: {result.complexity.value.upper()} ({result.reasoning})")
        
        return result