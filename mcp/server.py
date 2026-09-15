import json
import os
from typing import Dict , Any , List


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



class MCPClient:
    """
    The Client that the Agents use to talk to the MCP Server.
    It formats requests and handles transport logic.
    """
    def __init__(self , server:MCPServer):
        self.server = server


    