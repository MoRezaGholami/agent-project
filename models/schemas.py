from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# ==========================================
# Enums
# ==========================================
class TaskEffort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ReviewStatus(str, Enum):
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"

class ProjectComplexity(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"

# ==========================================
# Models
# ==========================================
class ProjectGoal(BaseModel):
    description: str = Field(..., description="The main description of the software project goal.")
    constraints: List[str] = Field(default_factory=list, description="Explicit constraints like specific technologies, budgets, or deadlines.")

class ArchitecturePlan(BaseModel):
    components: List[str] = Field(..., description="Core high-level components (e.g., API Gateway, Database, Frontend).")
    technologies: List[str] = Field(..., description="List of specific technologies and frameworks to be used.")
    modules: List[str] = Field(..., description="Major logical modules of the software.")
    architecture_decisions: List[str] = Field(..., description="Key architectural decisions made and the reasoning behind them.")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made by the architecture agent.")
    open_questions: List[str] = Field(default_factory=list, description="Any missing information that would help refine the architecture.")

class Task(BaseModel):
    task_id: str = Field(..., description="A unique identifier for the task, e.g., T01, T02.")
    title: str = Field(..., description="Short, descriptive title of the task.")
    description: str = Field(..., description="Detailed description of what needs to be done.")
    dependencies: List[str] = Field(default_factory=list, description="List of task_ids that must be completed before this task.")
    effort: TaskEffort = Field(..., description="Estimated effort required.")
    priority: TaskPriority = Field(..., description="Priority level of the task.")
    category: str = Field(..., description="Task category (e.g., Backend, Frontend, DevOps, DB).")

class TaskPlan(BaseModel):
    tasks: List[Task] = Field(..., description="A comprehensive list of all project tasks.")

class ReviewIssue(BaseModel):
    description: str = Field(..., description="Description of the issue found in the plan.")
    severity: TaskPriority = Field(..., description="Severity of the issue.")

class ReviewResult(BaseModel):
    status: ReviewStatus = Field(..., description="Whether the plan is approved or needs revision.")
    issues: List[ReviewIssue] = Field(default_factory=list, description="List of identified issues if any.")
    suggested_changes: List[str] = Field(default_factory=list, description="Actionable suggestions to fix the issues.")

class FinalReport(BaseModel):
    project_summary: str = Field(..., description="A brief summary of the final project plan.")
    architecture: Optional[ArchitecturePlan] = None
    tasks: List[Task] = Field(default_factory=list)
    validation_status: str = Field(..., description="Final status of the validation (e.g., Fully Validated, Partially Validated due to limits).")
    warnings: List[str] = Field(default_factory=list, description="Any warnings if the plan maxed out replanning rounds.")

# ==========================================
# State Model (For Context Engineering)
# ==========================================
class WorkflowState(BaseModel):
    """
    This model holds the state of our application. 
    It is passed through the Harness, but only specific parts are sent to each Sub-Agent.
    """
    goal: Optional[ProjectGoal] = None
    complexity: Optional[ProjectComplexity] = None
    architecture: Optional[ArchitecturePlan] = None
    task_plan: Optional[TaskPlan] = None
    review: Optional[ReviewResult] = None
    
    # Harness / Loop Engineering controls
    replan_rounds: int = Field(default=0, description="Tracks how many times we have replanned.")
    current_step: str = Field(default="init", description="Tracks the current agent or tool running.")
    is_finished: bool = Field(default=False, description="Flag to indicate the workflow has stopped.")