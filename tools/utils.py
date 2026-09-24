import os
import re

class WorkspaceManager:
    """
    Handles physical file generation with OS-level safety and reliability.
    """
    def __init__(self, base_dir="project_workspaces"):
        
        self.base_dir = os.path.join(os.getcwd(), base_dir)
        
    def _sanitize_filename(self, filename: str) -> str:
        
        safe_name = re.sub(r'[^\w\-_\.]', '_', filename)
        return safe_name

    def write_file(self, project_name: str, filename: str, content: str) -> bool:
        try:
            
            project_dir = os.path.join(self.base_dir, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            safe_filename = self._sanitize_filename(filename)
            file_path = os.path.join(project_dir, safe_filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            print(f"      💾 [WORKSPACE] Successfully created: {project_name}/{safe_filename}")
            return True
            
        except PermissionError:
            raise PermissionError(f"OS denied permission to write '{filename}'. Try a different name.")
        except Exception as e:
            raise OSError(f"File system error when writing '{filename}': {str(e)}")