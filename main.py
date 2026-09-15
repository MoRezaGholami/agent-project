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

    try:
        mcp_server.execute_tool("create_task", {"task_id": "T00", "title": "Setup Git Repository", "status": "done"})
    except ValueError:
        pass


    runner = WorkflowRunner(llm=llm, mcp_client=mcp_client)


    #demo propmt. you can write everything you want.

    demo_prompt = (
        "I want to build a Django-based university course management system "
        "with PostgreSQL, authentication, REST APIs, automated tests, and Docker deployment."
    )

    print("\n[USER INPUT]:", demo_prompt)


    final_report = runner.run(demo_prompt)

    print_final_report(final_report)

if __name__ == "__main__":
    main()