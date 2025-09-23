import os
from dotenv import load_dotenv

load_dotenv()

PING_FED_URL = os.getenv('PING_FED_URL')
KGW_CLIENT_ID = os.getenv('KGW_CLIENT_ID')
KGW_CLIENT_SECRET = os.getenv('KGW_CLIENT_SECRET')
KGW_ENDPOINT = os.getenv('KGW_ENDPOINT')
API_VERSION = os.getenv('AOAI_API_VERSION')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL_DEPLOYMENT_NAME')

GPT_5_DEPLOYMENT = os.getenv('GPT_5_DEPLOYMENT_NAME', 'gpt-5')
CHAT_MODEL_DEPLOYMENT = GPT_5_DEPLOYMENT

CHUNK_SIZES = {
    'structured_data': 25,
    'tabular': 15,
    'header': 50,
    'text': 30,
    'empty': 0
}

COUNTING_PATTERNS = [
    'how many', 'count', 'number of', 'total', 'sum of',
    'quantity', 'amount of', 'frequency'
]

ANALYSIS_PATTERNS = [
    'analyze', 'compare', 'relationship', 'pattern', 'trend',
    'correlation', 'summary', 'overview', 'insights'
]

SEARCH_PATTERNS = [
    'find', 'search', 'locate', 'where', 'which', 'what is',
    'show me', 'list', 'identify'
]