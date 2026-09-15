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


class ReviewerAgent:
    """
    Role: Strict Technical Reviewer
    Responsibility: Evaluate the task plan, architecture, and deterministic validation results to approve or reject the plan.
    """


