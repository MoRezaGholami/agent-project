import logging
from dotenv import load_dotenv


load_dotenv()


logging.basicConfig(
    level=logging.INFO , 
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("agent_app")


from agents.orchestrator import orchestrator
def analyze_document(file_path: str) -> str:
    logger.info(f"شروع تحلیل سند: {file_path}")
    user_request = f"سند PDFتحلیلت هم به زبان انگلیسی ارائه بده.زیر رو تحلیل کن و گزارش نهایی بده: {file_path}"
    final_state = orchestrator.invoke(
        {"messages": [{"role": "user", "content": user_request}]}
    )

    logger.info("تحلیل سند به پابان رسید")
    return final_state["messages"][-1].content


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2 :
        print("لطفا ادرس فایل را به ارگومان ورودی پاس بدهید")
        sys.exit(1)

    report = analyze_document(sys.argv[1])

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("=== گزارش نهایی ===\n\n")
        f.write(report)

    print("گزارش در output.txt ذخیره شد.")
