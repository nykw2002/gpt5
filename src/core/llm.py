import requests
from typing import List
from .config import KGW_ENDPOINT, API_VERSION

class LLMService:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager

    def query_gpt5_with_cot(self, query: str, context_chunks: List[str], query_type: str, model: str = None) -> str:
        from .config import GPT_5_DEPLOYMENT
        model = GPT_5_DEPLOYMENT
        if not self.auth_manager.ensure_authenticated():
            return "Authentication failed"

        context = "\n\n".join([f"Data Block {i+1}:\n{chunk}" for i, chunk in enumerate(context_chunks)])

        if query_type == 'counting':
            system_prompt = """You are an expert data analyst. When counting items, use Chain of Thought reasoning:
1. First, identify all relevant items in each data block
2. Count them systematically
3. Double-check your count
4. Provide the final total with confidence

Be thorough and accurate. Show your reasoning process."""

        elif query_type == 'analysis':
            system_prompt = """You are an expert data analyst. When analyzing data:
1. First, examine the data structure and patterns
2. Identify key insights and relationships
3. Synthesize findings into clear conclusions
4. Support your analysis with specific evidence

Provide comprehensive analysis with clear reasoning."""

        else:
            system_prompt = """You are an expert assistant. Analyze the provided data carefully and answer the question thoroughly with supporting evidence."""

        prompt = f"""{system_prompt}

DATA:
{context}

QUESTION: {query}

ANSWER:"""

        url = f"{KGW_ENDPOINT}/openai/deployments/{model}/chat/completions?api-version={API_VERSION}"

        headers = {
            'Authorization': f'Bearer {self.auth_manager.access_token}',
            'Content-Type': 'application/json'
        }

        reasoning_effort = "medium" if query_type in ['counting', 'analysis'] else "minimal"

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": 3000,
            "reasoning_effort": reasoning_effort
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)

            if response.status_code == 401:
                if self.auth_manager.get_access_token():
                    headers['Authorization'] = f'Bearer {self.auth_manager.access_token}'
                    response = requests.post(url, headers=headers, json=payload, timeout=90)

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']

                usage = result.get('usage', {})
                completion_details = usage.get('completion_tokens_details', {})
                reasoning_tokens = completion_details.get('reasoning_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0) - reasoning_tokens

                print(f"GPT-5 tokens: {reasoning_tokens} reasoning + {output_tokens} output = {usage.get('total_tokens', 0)} total")

                return content if content else "No response generated"
            else:
                return f"GPT-5 request failed: {response.status_code}"

        except Exception as e:
            return f"GPT-5 error: {e}"