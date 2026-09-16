#i have to redesign orchestrator file for my new agent plan.
from pydantic import Field , BaseModel
from models.schemas import ProjectGoal , ProjectComplexity
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

#این کلاس واسه تسهیل در تصمیم گیری های orchestrator ساخته میشه.

class OrchestrationDecision(BaseModel):
    goal : ProjectGoal = Field(..., description="The parsed and structured project goal including constraints.")
    complexity: ProjectComplexity = Field(..., description="SIMPLE or COMPLEX based on the request.")
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
1. Extract the main goal and any explicit constraints (e.g., specific languages, deadlines, DBs).
2. Determine the project's complexity:
   - Choose 'SIMPLE' for basic scripts, single-file tools, small bug fixes, or trivial tasks that DO NOT need a software architecture design.
   - Choose 'COMPLEX' for web apps, systems with databases, APIs, authentication, microservices, or multi-module projects.
3. Provide a brief reasoning for your decision.

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