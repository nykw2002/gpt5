import requests
from typing import Dict, Any
from core.config import KGW_ENDPOINT, GPT_5_DEPLOYMENT, API_VERSION

class ResultSynthesizer:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager

    def synthesize_results(self, original_query: str, sub_results: Dict[str, Any]) -> str:
        synthesis_context = []
        for focus, result in sub_results.items():
            synthesis_context.append(f"=== {focus.upper()} ===")
            synthesis_context.append(f"Question: {result['query']}")
            synthesis_context.append(f"Answer: {result['answer']}")
            synthesis_context.append("")

        context_text = "\n".join(synthesis_context)

        synthesis_prompt = f"""
You are synthesizing multiple focused analysis results into a comprehensive response.

ORIGINAL COMPLEX QUERY:
{original_query}

FOCUSED ANALYSIS RESULTS:
{context_text}

SYNTHESIS INSTRUCTIONS:
1. Combine all the focused results to address every aspect of the original query
2. Follow the exact format and structure requested in the original query
3. Ensure all numbers, comparisons, and details from the focused analyses are included
4. Maintain professional formatting with proper capitalization and date formats
5. If any required information is missing from the focused results, note it clearly
6. Do not add information not present in the focused analysis results

COMPREHENSIVE RESPONSE:
"""

        if not self.auth_manager.ensure_authenticated():
            return "Error: Could not authenticate for synthesis"

        url = f"{KGW_ENDPOINT}/openai/deployments/{GPT_5_DEPLOYMENT}/chat/completions?api-version={API_VERSION}"

        headers = {
            'Authorization': f'Bearer {self.auth_manager.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert data analyst specializing in synthesizing multiple focused analyses into comprehensive reports. You maintain accuracy while ensuring all requirements of complex queries are addressed."
                },
                {
                    "role": "user",
                    "content": synthesis_prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 401:
                if self.auth_manager.get_access_token():
                    headers['Authorization'] = f'Bearer {self.auth_manager.access_token}'
                    response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"Synthesis failed: {response.status_code}")
                return f"Synthesis error: {response.status_code}"

        except Exception as e:
            print(f"Synthesis error: {e}")
            return f"Synthesis error: {str(e)}"