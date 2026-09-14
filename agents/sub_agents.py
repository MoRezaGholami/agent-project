from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from tools.pdf_tools import read_pdf

import os

model = ChatOpenAI(
    model = "gpt-4o-mini",
    base_url = os.environ.get("AI_BASE_URL" , "https://api.avalai.ir/v1"),
    api_key= os.environ["AI_API_KEY"],
    max_retries=8,
)


#sub_agent 1: extraction important points

extraction_subagent = create_react_agent(
    model = model,
    tools= [read_pdf],
    prompt = (
        "تو یک Sub-Agent تخصصی استخراج اطلاعات از اسناد هستی. "
        "وظیفه‌ات: فایل PDF داده‌شده رو بخون و نکات کلیدی، بندهای اصلی، "
        "و اطلاعات مهم (تاریخ‌ها، مبالغ، طرفین قرارداد) رو به‌صورت لیست ساخت‌یافته خلاصه کن. "
        "فقط استخراج کن، درباره‌ی ریسک یا کیفیت نظر نده — این کار Sub-Agent دیگریه."
    ),
)


# I will work on sub agent 2 after completing the first one.
