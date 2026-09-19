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


def draw_task_graph(tasks):
    if not tasks:
        return
    
    mermaid_code = "graph TD;\n"
    for task in tasks:
        task_id = task['task_id']
        
        mermaid_code += f'    {task_id}["[{task_id}] {task.get("title", "")}"]\n'
        
        for dep in task.get("dependencies", []):
            mermaid_code += f'    {dep} --> {task_id}\n'
            
    st.markdown(f"```mermaid\n{mermaid_code}\n```")


with st.sidebar:
    st.header("💾 Database State")
    db_path = "project_db.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)
            tasks = db_data.get("tasks", [])
            st.success(f"Connected! {len(tasks)} tasks found.")
            
            
            if tasks:
                task_summaries = [{"ID": t["task_id"], "Title": t["title"], "Status": t["status"]} for t in tasks]
                st.dataframe(task_summaries, use_container_width=True)
    else:
        st.warning("Database is empty. Run a prompt to generate tasks.")
        tasks = []


prompt = st.text_area("✍️ Describe your project or update request:", height=100, 
                     placeholder="e.g., Build a Django course management system...")

if st.button("🚀 Run Autonomous Planning", type="primary"):
    if prompt:
        load_dotenv()
        
        
        with st.status("🧠 Agents are thinking... Please wait.", expanded=True) as status:
            st.write("Booting up MCP Server...")
            
            llm = ChatOpenAI(
                model="gpt-4o-mini", 
                temperature=0.1,
                api_key=os.environ.get("OPENAI_API_KEY"),
                base_url="https://api.avalai.ir/v1" 
            )
            mcp_server = MCPServer()
            mcp_client = MCPClient(mcp_server)
            runner = WorkflowRunner(llm=llm, mcp_client=mcp_client)
            
            st.write("Running Workflow Runner...")
            
            final_report = runner.run(prompt)
            
            status.update(label="✅ Planning Complete!", state="complete", expanded=False)

        
        st.subheader("📊 Architecture Dependency Graph")
        with open(db_path, "r", encoding="utf-8") as f:
             updated_tasks = json.load(f).get("tasks", [])
        draw_task_graph(updated_tasks)
        
    else:
        st.error("Please enter a prompt first!")