import requests
import json
from typing import List, Dict, Any
from .config import KGW_ENDPOINT, CHAT_MODEL_DEPLOYMENT, API_VERSION

class QualityEvaluator:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager

    def evaluate_answer_quality(self, question: str, answer: str, source_chunks: List[str]) -> Dict[str, Any]:
        if not self.auth_manager.ensure_authenticated():
            return self.default_metrics()

        source_context = "\n\n".join([f"Source {i+1}:\n{chunk}" for i, chunk in enumerate(source_chunks)])

        prompt = f"""You are an AI Quality Evaluator. Evaluate the following AI response across three critical metrics.

EVALUATION CRITERIA:

1. GROUNDEDNESS (0-100):
   - Are the facts and claims in the answer directly supported by the provided source data?
   - Is the answer based on verifiable information from the sources?
   - Score: 100 = fully grounded in sources, 0 = no source support

2. ACCURACY (0-100):
   - Are the facts, numbers, and statements in the answer correct?
   - Are calculations, counts, and data interpretations accurate?
   - Score: 100 = completely accurate, 0 = major errors

3. RELEVANCE (0-100):
   - Does the answer directly address the user's question?
   - Is the information provided pertinent to what was asked?
   - Score: 100 = perfectly relevant, 0 = completely off-topic

ORIGINAL QUESTION: {question}

AI ANSWER TO EVALUATE:
{answer}

SOURCE DATA USED:
{source_context}

REQUIRED RESPONSE FORMAT (JSON):
{{
    "groundedness": {{
        "score": [0-100],
        "reasoning": "Brief explanation of score",
        "evidence": ["Key supporting facts from sources"]
    }},
    "accuracy": {{
        "score": [0-100],
        "reasoning": "Brief explanation of score",
        "issues": ["Any accuracy concerns found"]
    }},
    "relevance": {{
        "score": [0-100],
        "reasoning": "Brief explanation of score",
        "alignment": "How well answer matches question intent"
    }},
    "overall_assessment": {{
        "average_score": [calculated average],
        "acceptable": [true if average >= 80],
        "summary": "Brief overall quality assessment"
    }}
}}

Respond ONLY with the JSON object:"""

        url = f"{KGW_ENDPOINT}/openai/deployments/{CHAT_MODEL_DEPLOYMENT}/chat/completions?api-version={API_VERSION}"

        headers = {
            'Authorization': f'Bearer {self.auth_manager.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": 1000,
            "reasoning_effort": "minimal"
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 401:
                if self.auth_manager.get_access_token():
                    headers['Authorization'] = f'Bearer {self.auth_manager.access_token}'
                    response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']

                if content:
                    try:
                        metrics_data = json.loads(content.strip())
                        formatted_metrics = self.format_metrics_response(metrics_data)
                        print(f"Quality Metrics - Ground: {formatted_metrics['groundedness']['score']}%, Accuracy: {formatted_metrics['accuracy']['score']}%, Relevance: {formatted_metrics['relevance']['score']}%, Overall: {formatted_metrics['overall_assessment']['average_score']:.1f}%")
                        return formatted_metrics

                    except json.JSONDecodeError as e:
                        print(f"Failed to parse metrics JSON: {e}")
                        return self.default_metrics()

            print("Quality evaluation failed, using default metrics")
            return self.default_metrics()

        except Exception as e:
            print(f"Quality evaluation error: {e}")
            return self.default_metrics()

    def format_metrics_response(self, raw_metrics: Dict) -> Dict[str, Any]:
        try:
            groundedness = raw_metrics.get('groundedness', {})
            accuracy = raw_metrics.get('accuracy', {})
            relevance = raw_metrics.get('relevance', {})

            scores = [
                groundedness.get('score', 0),
                accuracy.get('score', 0),
                relevance.get('score', 0)
            ]
            average = sum(scores) / len(scores) if scores else 0

            return {
                'groundedness': {
                    'score': max(0, min(100, groundedness.get('score', 0))),
                    'reasoning': groundedness.get('reasoning', 'No evaluation available'),
                    'evidence': groundedness.get('evidence', [])
                },
                'accuracy': {
                    'score': max(0, min(100, accuracy.get('score', 0))),
                    'reasoning': accuracy.get('reasoning', 'No evaluation available'),
                    'issues': accuracy.get('issues', [])
                },
                'relevance': {
                    'score': max(0, min(100, relevance.get('score', 0))),
                    'reasoning': relevance.get('reasoning', 'No evaluation available'),
                    'alignment': relevance.get('alignment', 'No assessment available')
                },
                'overall_assessment': {
                    'average_score': round(average, 1),
                    'acceptable': average >= 80,
                    'summary': raw_metrics.get('overall_assessment', {}).get('summary', 'Quality assessment completed'),
                    'needs_review': average < 80
                }
            }

        except Exception as e:
            print(f"Error formatting metrics: {e}")
            return self.default_metrics()

    def default_metrics(self) -> Dict[str, Any]:
        return {
            'groundedness': {'score': 0, 'reasoning': 'Evaluation unavailable', 'evidence': []},
            'accuracy': {'score': 0, 'reasoning': 'Evaluation unavailable', 'issues': []},
            'relevance': {'score': 0, 'reasoning': 'Evaluation unavailable', 'alignment': 'Unknown'},
            'overall_assessment': {
                'average_score': 0,
                'acceptable': False,
                'summary': 'Quality metrics evaluation failed',
                'needs_review': True
            }
        }