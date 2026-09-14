
"""
Orchestrator: مغز اصلی سیستم.
هر دو Sub-Agent رو به‌عنوان Tool می‌بینه و تصمیم می‌گیره
با چه ترتیبی صداشون بزنه تا به یک گزارش نهایی برسه.
"""


import logging
from langchain_core.tools import tool

from langgraph.prebuilt import create_react_agent
from agents.sub_agents import extraction_subagent , model


logger = logging.getLogger("agent_app")


@tool
def run_extraction(document_path: str) -> str:
    """درخواست استخراج اطلاعات از یک سند PDF را به Sub-Agent مربوطه می‌سپارد.""" 
    logger.info(f"Orchestrator -> Extraction sub-agent (file = {document_path})")
    result = extraction_subagent.invoke(
        {"messages": [{"role": "user", "content": f"این فایل رو تحلیل کن: {document_path}"}]}

    )
    return result["messages"][-1].content


orchestrator = create_react_agent(
    model=model,
    tools=[run_extraction],
        prompt=(
        "تو Orchestrator یک سیستم تحلیل اسناد هستی. "
        "روند کار: اول با run_extraction نکات کلیدی سند رو دربیار. "
        "بعد نتیجه رو به run_risk_analysis بده تا ریسک‌ها شناسایی بشن. "
        "در نهایت یک گزارش نهایی منسجم (نکات کلیدی + ریسک‌ها) برای کاربر بنویس. "
        "اگه در هر مرحله خطایی برگشت، به کاربر توضیح بده چی اشتباه پیش رفته."
    ),
)

