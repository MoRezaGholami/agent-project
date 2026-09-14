from pypdf import PdfReader
from langchain_core.tools import tool

@tool
def read_pdf(file_path: str) -> str :
    try :
        reader = PdfReader(file_path)
        text_parts = []
        for i, page in enumerate(reader.pages) :
            page_text = page.extract_text() or ""
            text_parts.append(f"[صفحه {i + 1}]\n{page_text}")
        full_text = "\n\n".join(text_parts)

        if not full_text.strip():
            return "هیچ متنی از این فایل استخراج نشد . احتمالا فایل نیاز به اسکن دارد."

        return full_text
    except Exception as e :
        return f"خطا در خواندن فایل {str(e)}"
    