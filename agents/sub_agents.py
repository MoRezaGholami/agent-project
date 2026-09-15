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

    
