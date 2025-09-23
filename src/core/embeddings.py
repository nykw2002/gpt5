import requests
import numpy as np
from typing import List
from .config import KGW_ENDPOINT, EMBEDDING_MODEL, API_VERSION

class EmbeddingService:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager

    def get_embedding(self, text: str) -> List[float]:
        if not self.auth_manager.ensure_authenticated():
            return []

        url = f"{KGW_ENDPOINT}/openai/deployments/{EMBEDDING_MODEL}/embeddings?api-version={API_VERSION}"

        headers = {
            'Authorization': f'Bearer {self.auth_manager.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {"input": text}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 401:
                if self.auth_manager.get_access_token():
                    headers['Authorization'] = f'Bearer {self.auth_manager.access_token}'
                    response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result['data'][0]['embedding']
            else:
                print(f"Embedding failed: {response.status_code}")
                return []

        except Exception as e:
            print(f"Embedding error: {e}")
            return []

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0

        return dot_product / (norm1 * norm2)