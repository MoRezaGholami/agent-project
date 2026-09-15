from langchain_core.language_models.chat_models import BaseChatModel

from mcp.server import MCPClient

from models.schemas import WorkflowState, FinalReport, ProjectComplexity, ReviewStatus, ArchitecturePlan
from agents.orchestrator import OrchestratorAgent
from agents.sub_agents import ArchitectureAgent, TaskPlannerAgent, ReviewerAgent

class WorkflowRunner :
    """
    The Harness Layer.
    Controls execution state, error handling, bounded loops, and orchestrates the Sub-Agents.
    """

    def __init__(self , llm : BaseChatModel , mcp_client : MCPClient):
        self.llm = llm
        self.mcp_client = mcp_client
        self.state = WorkflowState()


        #Initialize agents

        self.orchestrator = OrchestratorAgent(llm)
        self.architecture_agent = ArchitectureAgent(llm)
        self.task_planner = TaskPlannerAgent(llm)
        self.reviewer = ReviewerAgent(llm)


        


    