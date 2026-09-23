import time
import logging
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel

from models.schemas import WorkflowState, FinalReport, ProjectComplexity, ReviewStatus, ArchitecturePlan , ExecutionMode , ReviewResult
from agents.orchestrator import OrchestratorAgent
from agents.sub_agents import ArchitectureAgent, TaskPlannerAgent, ReviewerAgent, SecurityAgent
from tools.validation_tools import validate_dependencies, detect_cycles, calculate_task_order, estimate_project_duration
from mcp.server import MCPClient

MAX_REPLAN_ROUNDS = 2
MAX_API_RETRIES = 1  # limit error handling.

class WorkflowRunner:
    """
    The Harness Layer.
    Controls execution state, error handling, bounded loops, and orchestrates the Sub-Agents.
    """
    def __init__(self, llm: BaseChatModel, mcp_client: MCPClient):
        self.llm = llm
        self.mcp_client = mcp_client
        self.state = WorkflowState()
        
        # Initialize Agents
        self.orchestrator = OrchestratorAgent(llm)
        self.architecture_agent = ArchitectureAgent(llm)
        self.task_planner = TaskPlannerAgent(llm)
        self.reviewer = ReviewerAgent(llm)
        self.security_agent = SecurityAgent(llm)


    def _safe_invoke(self, agent_method, *args, **kwargs):
        """
        Safely invokes an LLM agent with a strict boundary on API errors (like 429).
        If it fails, it does NOT retry indefinitely.
        """
        retries = 0
        while retries <= MAX_API_RETRIES:
            try:
                return agent_method(*args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate limit" in error_msg:
                    print(f"[HARNESS ERROR] 429 Rate Limit hit. Retry {retries}/{MAX_API_RETRIES} after short sleep...")
                    time.sleep(2)
                    retries += 1
                else:
                    print(f"[HARNESS ERROR] Unexpected LLM failure: {e}")
                    break 
        return None

    def run(self, user_request: str) -> FinalReport:
        print("\n==================================================")
        print("[HARNESS] Starting Autonomous Planning Workflow")
        print("==================================================\n")

        # 1. ORCHESTRATION STEP
        self.state.current_step = "orchestration"
        decision = self._safe_invoke(self.orchestrator.invoke, user_request)
        if not decision:
            return self._abort_workflow("Failed to parse user request due to API error.")
        
        self.state.goal = decision.goal
        self.state.complexity = decision.complexity
        self.state.project_name = decision.project_name
        self.state.mode = decision.mode



        # 2. ARCHITECTURE STEP (Conditional Execution)
        if self.state.complexity == ProjectComplexity.COMPLEX:
            self.state.current_step = "architecture_debate"
            print("[HARNESS] Complex project detected. Starting Agent-to-Agent Debate (Architect vs Security).")
            
            debate_rounds = 0
            max_debate_rounds = 2
            security_feedback = "" 
            
            while debate_rounds <= max_debate_rounds:
                print(f"\n   [DEBATE ROUND {debate_rounds}] Architect generating plan...")
                
                
                arch_plan = self._safe_invoke(self.architecture_agent.invoke, self.state.goal, security_feedback)
                
                if not arch_plan:
                    return self._abort_workflow("Architecture Agent failed.")

                print(f"   -> Architect's Tech Stack: {', '.join(arch_plan.technologies)}")
                print(f"   -> Architect's Decisions: {arch_plan.architecture_decisions[0]} ...")
                
                sec_review = self._safe_invoke(self.security_agent.invoke, arch_plan)
                if not sec_review:
                     return self._abort_workflow("Security Agent failed.")
                     
                
                if sec_review.status == ReviewStatus.APPROVED:
                    print("   ✅ [AGENT DEBATE] Security Agent APPROVED the architecture.")
                    self.state.architecture = arch_plan
                    break
                else:
                    issues_list = [iss.description for iss in sec_review.issues]
                    print(f"   ❌ [AGENT DEBATE] Security Agent REJECTED. Issues: {issues_list}")
                    
                    if debate_rounds == max_debate_rounds:
                        print("   ⚠️ [AGENT DEBATE] Max rounds reached. Proceeding with current architecture anyway.")
                        self.state.architecture = arch_plan
                        break
                        
                    
                    print("   -> Forcing Architect to redesign based on security feedback...")
                    security_feedback = "\n".join([f"- {c}" for c in sec_review.suggested_changes])
                    debate_rounds += 1
        else:
            print("[HARNESS] Simple project detected. Skipping Architecture Agent.")
            # Create a dummy architecture for simple projects to keep types consistent
            self.state.architecture = ArchitecturePlan(
                components=["Main Script"], technologies=["Python"], 
                modules=["Core"], architecture_decisions=["Single-file script preferred"],
                assumptions=[], open_questions=[]
            )

        # 3. REPLANNING LOOP (Task Planning -> Validation -> Review)
        self.state.replan_rounds = 0
        review_feedback_for_planner = ""
        
        while self.state.replan_rounds <= MAX_REPLAN_ROUNDS:
            self.state.current_step = f"planning_loop_round_{self.state.replan_rounds}"
            print(f"\n--- [LOOP] Starting Planning Round {self.state.replan_rounds} ---")
            
            # --- A. Fetch MCP Context ---
            print("[HARNESS] Fetching external state from MCP...")
            try:
                mcp_resp = self.mcp_client.call_tool("get_tasks", project_name=self.state.project_name)
                mcp_data = mcp_resp.get('data', [])
                print(f"   [DEBUG] Looking for exactly: '{self.state.project_name}'")
                print(f"   [DEBUG] Found {len(mcp_data)} existing tasks in DB for this name.")
                mcp_context = f"Existing Tasks: {mcp_data}\n"
                
                # --- NEW: Calculate next task ID deterministically ---
                next_task_num = 1
                if mcp_data:
                    try:
                        
                        existing_ids = [int(t['task_id'].replace('T', '')) for t in mcp_data if str(t.get('task_id', '')).startswith('T')]
                        if existing_ids:
                            next_task_num = max(existing_ids) + 1
                    except Exception as e:
                        print(f"[HARNESS WARNING] Could not parse existing task IDs: {e}")
                # ---------------------------------------------------
                
                if review_feedback_for_planner:
                    mcp_context += f"CRITICAL - PREVIOUS REVIEW FEEDBACK TO FIX:\n{review_feedback_for_planner}"
            except Exception as e:
                print(f"[HARNESS ERROR] MCP Failure: {e}")
                mcp_context = "External system unavailable."
                next_task_num = 1

            # --- B. Task Planner ---
            task_plan = self._safe_invoke(
                self.task_planner.invoke, 
                self.state.goal, 
                self.state.architecture, 
                mcp_context,
                next_task_num 
            )
            if not task_plan:
                return self._abort_workflow("Task Planner failed to generate a plan.")
            self.state.task_plan = task_plan


            print("[HARNESS] Running deterministic Python tools on Task Plan...")
            
            
            db_resp = self.mcp_client.call_tool("get_tasks", project_name=self.state.project_name)
            existing_tasks = db_resp.get("data", [])
            existing_ids = [t.get("task_id") for t in existing_tasks]
            
            tool_errors = []
            
            tool_errors.extend(validate_dependencies(task_plan.tasks, existing_task_ids=existing_ids))
            
            
            tool_errors.extend(detect_cycles(task_plan.tasks))
            _, order_errors = calculate_task_order(task_plan.tasks)
            tool_errors.extend(order_errors)

            if tool_errors:
                print(f"[HARNESS WARNING] Tools found {len(tool_errors)} logic errors.")

            # --- D. Reviewer ---
            
            if self.state.mode == ExecutionMode.FAST and not tool_errors :
                print("[HARNESS - FAST MODE] Bypassing AI Reviewer for speed. Auto-approving...")
            
                review = ReviewResult(status=ReviewStatus.APPROVED, issues=[], suggested_changes=[])
                
            else :
                review = self._safe_invoke(self.reviewer.invoke, self.state.architecture, self.state.task_plan, tool_errors , mcp_context)
            if not review:
                # If reviewer fails, we break the loop and return what we have (Graceful Degradation)
                print("[HARNESS ERROR] Reviewer Agent failed. Stopping validation loop.")
                break
            
            self.state.review = review
            print(f"[HARNESS] Reviewer verdict: {review.status.value.upper()}")

            # --- E. Loop Decision ---
            if review.status == ReviewStatus.APPROVED:
                print("[LOOP] Plan approved by Reviewer. Breaking loop.")
                print("[HARNESS] Saving approved tasks to MCP Database...")
                for task in self.state.task_plan.tasks:
                    try:
                        resp = self.mcp_client.call_tool(
                            "create_task", 
                            task_id=task.task_id, 
                            title=task.title, 
                            status="todo",
                            dependencies=task.dependencies,
                            project_name=self.state.project_name
                        )

                        if resp.get("status") != "success":
                            print(f"   [ERROR] Failed to save {task.task_id}: {resp.get('message')}")
                    except ValueError:
                        pass 
                
                break

            elif review.status == ReviewStatus.HUMAN_REVIEW :
                print("\n" + "⚠️"*20)
                print("[HUMAN REQUIRED] The AI Reviewer is unsure and requests your input!")
                print(f"Reason: {review.issues}")
                print("⚠️"*20)

                user_feedback = input("\n👉 Type 'y' to forcefully APPROVE, or type feedback to REVISE the plan: ").strip()
                if user_feedback.lower() == 'y' :
                    print("[HUMAN] Plan forcefully approved. Saving to Database...")
                    print("[HARNESS] Saving approved tasks to MCP Database...")
                    for task in self.state.task_plan.tasks:
                        try:
                            resp = self.mcp_client.call_tool(
                                "create_task", 
                                task_id=task.task_id, 
                                title=task.title, 
                                status="todo",
                                dependencies=task.dependencies,
                                project_name=self.state.project_name
                            )
    
                            if resp.get("status") != "success":
                                print(f"   [ERROR] Failed to save {task.task_id}: {resp.get('message')}")
                        except ValueError:
                            pass 
                    
                    break
                else :
                    print(f"\n[HUMAN] Revision requested: '{user_feedback}'")
                    review.status = ReviewStatus.NEEDS_REVISION
                    review_feedback_for_planner = f"HUMAN OVERRIDE FEEDBACK: {user_feedback}. You MUST update the plan to satisfy this."


            elif review.status == ReviewStatus.NEEDS_REVISION :
                self.state.replan_rounds += 1

                current_max_rounds = 4 if self.state.mode == ExecutionMode.THOROUGH else MAX_REPLAN_ROUNDS
                if self.state.replan_rounds > current_max_rounds:
                    print("[LOOP LIMIT] Maximum replanning rounds reached! Forcing stop.")
                    break

                print(f"   [REVIEWER FEEDBACK]: {review.issues}")
                
                print("[LOOP] Plan rejected. Generating feedback for next round...")
                issues_text = "\n".join([f"- {iss.description} ({iss.severity})" for iss in review.issues])
                changes_text = "\n".join([f"- {c}" for c in review.suggested_changes])
                review_feedback_for_planner = f"Issues:\n{issues_text}\nSuggestions:\n{changes_text}"
        
        # 4. FINALIZE (Build Final Report)
        return self._build_final_report()



    def _abort_workflow(self, reason: str) -> FinalReport:
        """Graceful degradation in case of fatal error."""
        self.state.is_finished = True
        print(f"\n[FATAL ERROR] {reason}")
        return FinalReport(
            project_summary="WORKFLOW ABORTED",
            validation_status="FAILED",
            warnings=[reason]
        )


    def _build_final_report(self) -> FinalReport:
        self.state.is_finished = True
        
        # FETCHING WEB RESOURCES VIA MCP ---
        resources = {}
        if self.state.task_plan:
            print("\n[HARNESS] 🌐 Fetching live learning resources from the Web via MCP...")
            for task in self.state.task_plan.tasks:
                if task.search_keywords and task.search_keywords.strip():
                    try:
                        print(f"  -> Searching for: '{task.search_keywords}' (Task {task.task_id})")
                        resp = self.mcp_client.call_tool("search_web", query=task.search_keywords)
                        if resp.get("status") == "success" and resp.get("data"):
                            resources[task.task_id] = resp["data"]
                            print(f"     ✅ Found {len(resp['data'])} links.") 
                        else:
                            print(f"     ❌ No valid results returned from MCP.")
                    except Exception as e:
                        print(f"     ⚠️ Search tool error: {e}")
        
        est_duration = -1
        if self.state.task_plan:
             est_duration = estimate_project_duration(self.state.task_plan.tasks)
             
        status = "Fully Validated & Approved"
        warnings = []
        
        if self.state.review and self.state.review.status != ReviewStatus.APPROVED:
            status = "Partially Validated (Max Replan Rounds Reached)"
            warnings = ["The plan still has unresolved issues raised by the Reviewer or Tools."]
            
        summary = f"Generated {len(self.state.task_plan.tasks) if self.state.task_plan else 0} tasks. "
        summary += f"Estimated Duration: {est_duration} units."
        
        print("\n==================================================")
        print(f"[FINAL] Workflow Completed. Status: {status}")
        print("==================================================\n")
        
        return FinalReport(
            project_summary=summary,
            architecture=self.state.architecture,
            tasks=self.state.task_plan.tasks if self.state.task_plan else [],
            validation_status=status,
            warnings=warnings,
            learning_resources=resources 
        )





    