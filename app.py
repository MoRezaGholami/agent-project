import streamlit as st
import json
import os
from dotenv import load_dotenv

from mcp.server import MCPServer, MCPClient
from harness.runner import WorkflowRunner
from langchain_openai import ChatOpenAI

st.set_page_config(page_title="AI Project Planner", page_icon="🤖", layout="wide")
st.title("🤖 Autonomous Agentic Project Planner")
st.markdown("---")


def read_db_safely(db_path):
    """ reading database safley if it is empty"""
    if not os.path.exists(db_path):
        return {"tasks": []}
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            if not data or "tasks" not in data:
                return {"tasks": []}
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {"tasks": []}

def draw_task_graph(tasks):
    if not tasks:
        st.info("No tasks to display. Run a prompt to generate the plan.")
        return
    
    mermaid_code = "graph TD;\n"
    for task in tasks:
        task_id = task['task_id']
        
        clean_title = task.get("title", "").replace('"', "'")
        mermaid_code += f'    {task_id}["[{task_id}] {clean_title}"]\n'
        for dep in task.get("dependencies", []):
            mermaid_code += f'    {dep} --> {task_id}\n'
            
    st.markdown(f"```mermaid\n{mermaid_code}\n```")


db_path = "project_db.json"
db_data = read_db_safely(db_path)
all_tasks = db_data.get("tasks", [])


project_names = list(set([t.get("project_name", "default") for t in all_tasks]))


with st.sidebar:
    st.header("📂 Projects Dashboard")
    
    if not project_names:
        st.warning("Database is empty. No projects found.")
        selected_project = None
        filtered_tasks = []
    else:
        
        selected_project = st.selectbox("📌 Select a Project:", project_names)
        
        
        filtered_tasks = [t for t in all_tasks if t.get("project_name") == selected_project]
        st.success(f"Loaded {len(filtered_tasks)} tasks for '{selected_project}'.")
        
        
        if filtered_tasks:
            task_summaries = [{"ID": t["task_id"], "Title": t["title"], "Status": t["status"]} for t in filtered_tasks]
            st.dataframe(task_summaries, use_container_width=True, hide_index=True)


st.subheader("🛠️ Autonomous Planner")
prompt = st.text_area("Describe your new project or update request:", height=100, 
                     placeholder="e.g., Build a Django course management system...")

if st.button("🚀 Run Planning Agents", type="primary"):
    if prompt:
        load_dotenv()
        
        with st.status("🧠 Agents are thinking... (Detailed logs are in your VS Code terminal)", expanded=True) as status:
            st.write("Booting up MCP Server & Agents...")
            
            llm = ChatOpenAI(
                model="gpt-4o-mini", 
                temperature=0.1,
                api_key=os.environ.get("OPENAI_API_KEY"),
                base_url="https://api.avalai.ir/v1" 
            )
            mcp_server = MCPServer()
            mcp_client = MCPClient(mcp_server)
            runner = WorkflowRunner(llm=llm, mcp_client=mcp_client)
            
            st.write("Generating graph and validating constraints...")
            # اجرای هارنس
            runner.run(prompt)
            
            status.update(label="✅ Planning Complete!", state="complete", expanded=False)

        
        st.rerun()
    else:
        st.error("Please enter a prompt first!")


st.markdown("---")
if selected_project:
    st.subheader(f"📊 Architecture Graph: {selected_project}")
    draw_task_graph(filtered_tasks)
else:
    st.subheader("📊 Architecture Graph")
    draw_task_graph([])