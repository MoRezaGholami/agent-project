import json
import os
from typing import Dict , Any , List
#from duckduckgo_search import DDGS
from googlesearch import search


DB_FILE = "project_db.json"

class MCPServer:
    """
    A simulated MCP (Model Context Protocol) Server.
    In a production environment, this would be a separate microservice running via HTTP or Stdio.
    Here, it acts as a strict architectural boundary saving state to a local JSON file.
    """

    def __init__(self):
        self._initialize_db()


    def _read_db(self) -> Dict[str, Any]:
        with open(DB_FILE, 'r') as f:
            return json.load(f)

    def _write_db(self, data: Dict[str, Any]):
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)



    def _initialize_db(self):
        """Creates an empty mock database if it doesn't exist."""
        if not os.path.exists(DB_FILE):
            default_state = {
                "project_info": {},
                "tasks": []
            }
            with open(DB_FILE, 'w') as f:
                json.dump(default_state, f, indent=4)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str , Any] :
        """
        The only entry point for the MCP Client. 
        Enforces the boundary by strictly accepting and returning JSON-serializable dicts.
        """

        #defining tools :
        tools = {
            "get_project" : self._get_project ,
            "get_tasks" : self._get_tasks ,
            "create_task": self._create_task,
            "update_project": self._update_project,
            "search_web": self._search_web
        }

        if tool_name not in tools :
            return {"status": "error", "message": f"Tool '{tool_name}' not found in MCP Server."}

        try :
            result = tools[tool_name](**arguments)
            return {"status": "success", "data": result}
        except Exception as e :
            return {"status": "error", "message": str(e)}

        
    def _get_project(self) -> Dict[str , Any]:
        """Returns current high-level project information."""
        db = self._read_db()
        return db.get("project_info" , {})

    def _update_project(self , name: str , description: str) -> str :
        """Update project metadata"""
        db = self._read_db()
        db["project_info"] = {"name": name, "description": description}
        self._write_db(db)
        return "project updated!"

    def _get_tasks(self, project_name: str = None) -> List[Dict[str, Any]]:
        """Returns tasks, optionally filtered by project_name."""
        db = self._read_db()
        tasks = db.get("tasks", [])
        if project_name:
            
            return [t for t in tasks if t.get("project_name") == project_name]
        return tasks

    def _create_task(self, task_id: str, title: str, status: str = "todo", dependencies: list = None, project_name: str = "default") -> str:
        """Creates a new task tagged with a specific project_name."""
        if dependencies is None:
            dependencies = []
            
        db = self._read_db()
        
        
        for task in db["tasks"]:
            if task.get("task_id") == task_id and task.get("project_name") == project_name:
                raise ValueError(f"Task {task_id} already exists in project {project_name}.")
                
        db["tasks"].append({
            "task_id": task_id,
            "title": title,
            "status": status,
            "dependencies": dependencies,
            "project_name": project_name  
        })
        self._write_db(db)
        return f"Task {task_id} created successfully."

    def _search_web(self, query: str, max_results: int = 2) -> list:
        """
        Generates direct search URLs instead of scraping to bypass network blocks.
        Zero token usage, zero network failure.
        """
        import urllib.parse
        
        if not query:
            return []
            
       
        encoded_query = urllib.parse.quote(query)
        
        results = [
            {
                "title": f"🔍 Google Search: {query}",
                "href": f"https://www.google.com/search?q={encoded_query}"
            },
            {
                "title": f"📺 YouTube Tutorials: {query}",
                "href": f"https://www.youtube.com/results?search_query={encoded_query}"
            }
        ]
        
        return results

    


    

class MCPClient:
    """
    The Client that the Agents use to talk to the MCP Server.
    It formats requests and handles transport logic.
    """
    def __init__(self , server:MCPServer):
        self.server = server

    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Simulates an RPC call to the MCP server.
        """
        # In real MCP, this would serialize to JSON and send over Stdio/HTTP.
        print(f"[MCP_REQUEST] Tool: {tool_name} | Args: {kwargs}")
        response = self.server.execute_tool(tool_name, kwargs)
        print(f"[MCP_RESPONSE] Status: {response['status']}")
        return response


    