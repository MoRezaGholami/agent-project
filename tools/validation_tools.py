
from models.schemas import Task , TaskEffort
from typing import List, Dict, Tuple


def validate_dependencies(tasks: List[Task], existing_task_ids: List[str] = None) -> List[str]:
    """
    Checks if all dependencies declared by tasks actually exist in the NEW task list OR the EXISTING DB.
    """
    if existing_task_ids is None:
        existing_task_ids = []
        
    errors = []
    task_ids = {task.task_id for task in tasks}
    
    valid_targets = task_ids.union(set(existing_task_ids)) 
    
    for task in tasks:
        for dep in task.dependencies:
            if dep not in valid_targets:
                errors.append(f"Task {task.task_id} depends on unknown task: {dep}")
                
    return errors




def detect_cycles(tasks: List[Task]) -> List[str]:
    """
    Uses Depth-First Search (DFS) to detect circular dependencies (cycles) in the task graph.
    """
    task_ids = {task.task_id for task in tasks}
    
    
    adj_list: Dict[str, List[str]] = {
        task.task_id: [d for d in task.dependencies if d in task_ids] 
        for task in tasks
    }
    
    visited = set()
    rec_stack = set()
    errors = []

    def dfs(node: str, path: set):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in adj_list.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path)
            elif neighbor in rec_stack:
                errors.append(f"Circular dependency detected involving: {neighbor}")
                
        rec_stack.remove(node)

    for task in tasks:
        if task.task_id not in visited:
            dfs(task.task_id, set())
            
    return list(set(errors))


def calculate_task_order(tasks: List[Task]) -> Tuple[List[str], List[str]]:
    """
    Performs Topological Sorting (Kahn's Algorithm) to determine execution order.
    Returns: (ordered_task_ids, errors)
    """

    in_degree = {task.task_id: 0 for task in tasks}
    adj_list = {task.task_id: [] for task in tasks}

    for task in tasks:
            for dep in task.dependencies:
                if dep in in_degree:
                    adj_list[dep].append(task.task_id)
                    in_degree[task.task_id] += 1


    queue = [t_id for t_id in in_degree if in_degree[t_id] == 0]
    ordered_tasks = []

    while queue :
        current = queue.pop(0)
        ordered_tasks.append(current)


        for neighbor in adj_list.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)


    if len(ordered_tasks) != len(tasks) :
        return [], ["Cannot calculate order due to missing dependencies or cycles."]

    return ordered_tasks, []


def estimate_project_duration(tasks: List[Task]) -> int:
    """
    Estimates the critical path duration of the project.
    We assign arbitrary numeric values to TaskEffort for calculation.
    """
    effort_days = {
        TaskEffort.LOW: 2,
        TaskEffort.MEDIUM: 5,
        TaskEffort.HIGH: 10
    }
    
    
    earliest_start = {task.task_id: 0 for task in tasks}
    ordered_tasks, errors = calculate_task_order(tasks)
    
    if errors:
        return -1 # Cannot calculate
        
    task_map = {task.task_id: task for task in tasks}
    
    for t_id in ordered_tasks:
        task = task_map[t_id]
        duration = effort_days[task.effort]
        
        finish_time = earliest_start[t_id] + duration
        
        
        for neighbor in tasks:
            if t_id in neighbor.dependencies:
                earliest_start[neighbor.task_id] = max(earliest_start[neighbor.task_id], finish_time)
                
    
    max_duration = 0
    for task in tasks:
        duration = effort_days[task.effort]
        max_duration = max(max_duration, earliest_start[task.task_id] + duration)
        
    return max_duration

