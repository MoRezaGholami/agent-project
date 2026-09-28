import os
import json
from dotenv import load_dotenv


from mcp.server import MCPClient , MCPServer

from harness.runner import WorkflowRunner
from langchain_openai import ChatOpenAI


def print_final_report(report) :
    """ a function for print report in a better way """
    print("\n\n" + "="*60)
    print("🏆 FINAL PROJECT PLAN 🏆".center(60))
    print("="*60)

    print(f"\n📌 Project Summary: {report.project_summary}")
    print(f"✅ Validation Status: {report.validation_status}")
    
    if report.warnings:
        print("\n⚠️  Warnings:")
        for w in report.warnings:
            print(f"   - {w}")

    if report.architecture:
        print("\n🏗️  Architecture:")
        print(f"   - Components: {', '.join(report.architecture.components)}")
        print(f"   - Technologies: {', '.join(report.architecture.technologies)}")
        print(f"   - Modules: {', '.join(report.architecture.modules)}")
    
    print(f"\n📋 Tasks & Dependencies ({len(report.tasks)} tasks):")
    for t in report.tasks:
        deps = f"(Depends on: {', '.join(t.dependencies)})" if t.dependencies else "(No dependencies)"
        print(f"   [{t.task_id}] {t.title} - Effort: {t.effort.value.upper()} {deps}")
        task_resources = report.learning_resources.get(t.task_id, [])
        if task_resources:
            print("       📚 Suggested Resources (Live from Web):")
            for res in task_resources:
                
                short_title = res['title'][:60] + "..." if len(res['title']) > 60 else res['title']
                print(f"          🔗 {short_title}\n          └─ {res['href']}")
        print("") 

    print("="*60 + "\n")


def main():
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ Error: API Key is missing. Please set it in your .env file.")
        return

    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0.1,
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url="https://api.avalai.ir/v1" 
    )
    print("[SYSTEM] Booting up MCP Server...")
    mcp_server = MCPServer()
    mcp_client = MCPClient(mcp_server)



    runner = WorkflowRunner(llm=llm, mcp_client=mcp_client)


    #demo propmt. you can write everything you want.

    demo_prompt = (
        "Develop an internal employee performance review web tool. The frontend must be raw HTML and Vanilla JavaScript."
        " The backend must be Node.js.  STRICT CONSTRAINTS: You are absolutely forbidden from using any real database (No SQL/NoSQL). You MUST store all sensitive performance reviews in a local 'reviews.txt' file. Furthermore, we have no budget for authentication services, so employees will just type their name in a simple text box to submit a review. No passwords, no OAuth."
    )

    print("\n[USER INPUT]:", demo_prompt)


    final_report = runner.run(demo_prompt)

    print_final_report(final_report)

if __name__ == "__main__":
    main()