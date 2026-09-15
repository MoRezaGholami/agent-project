#i have to redesign orchestrator file for my new agent plan.
from pydantic import Field , BaseModel
from models.schemas import ProjectGoal , ProjectComplexity

#این کلاس واسه تسهیل در تصمیم گیری های orchestrator ساخته میشه.

class OrchestrationDecision(BaseModel):
    goal : ProjectGoal = Field(..., description="The parsed and structured project goal including constraints.")
    complexity: ProjectComplexity = Field(..., description="SIMPLE or COMPLEX based on the request.")
    reasoning: str = Field(..., description="Short explanation for why this complexity was chosen.")


class OrchestratorAgent:
