import logging
from dotenv import load_dotenv


load_dotenv()


logging.basicConfig(
    level=logging.INFO , 
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("agent_app")



