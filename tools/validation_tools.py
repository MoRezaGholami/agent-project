
from models.schemas import Task , TaskEffort
from typing import List, Dict, Tuple

def validate_dependencies(tasks: List[Task]) -> List[str]:
    """
    Checks if all dependencies declared by tasks actually exist in the task list.
    """
    errors = []
    task_ids = {task.task_id for task in tasks}
    
    for task in tasks:
        for dep in task.dependencies:
            if dep not in task_ids:
                errors.append(f"Task {task.task_id} depends on unknown task: {dep}")
                
    return errors


def detect_cycles(tasks : List[Task]) -> List[str] :
    """
    Uses Depth-First Search (DFS) to detect circular dependencies (cycles) in the task graph.
    """

    adj_list: Dict[str, List[str]] = {task.task_id: task.dependencies for task in tasks}
    visited = set()
    rec_stack = set()
    errors = []


    def dfs(node : str , path : set):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in adj_list.get(node , []) :
            if neighbor not in visited:
                dfs(neighbor , path)

            elif neighbor in rec_stack :
                errors.append(f"Circular dependency detected involving: {neighbor}")

        rec_stack.remove(node)

    for task in tasks :
        if task.task_id not in visited :
            dfs(task.task_id , set())


    return list(set(errors))




