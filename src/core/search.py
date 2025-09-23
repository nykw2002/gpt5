from typing import List
from .config import COUNTING_PATTERNS, ANALYSIS_PATTERNS, SEARCH_PATTERNS

class SearchService:
    def __init__(self, embedding_service):
        self.embedding_service = embedding_service

    @staticmethod
    def classify_query(query: str) -> str:
        query_lower = query.lower()

        if any(pattern in query_lower for pattern in COUNTING_PATTERNS):
            return 'counting'
        elif any(pattern in query_lower for pattern in ANALYSIS_PATTERNS):
            return 'analysis'
        elif any(pattern in query_lower for pattern in SEARCH_PATTERNS):
            return 'search'
        else:
            return 'general'

    def adaptive_search(self, query: str, query_type: str, chunk_embeddings: list, chunk_metadata: list) -> List[int]:
        print(f"Running adaptive search for {query_type} query...")

        query_embedding = self.embedding_service.get_embedding(query)
        if not query_embedding:
            return []

        similarities = []
        for i, chunk_embedding in enumerate(chunk_embeddings):
            similarity = self.embedding_service.cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((i, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)

        if query_type == 'counting':
            selected = []
            for chunk_idx, similarity in similarities:
                metadata = chunk_metadata[chunk_idx]
                if metadata['type'] == 'structured_data' and similarity >= 0.3:
                    selected.append(chunk_idx)
                elif similarity >= 0.6:
                    selected.append(chunk_idx)
                if len(selected) >= 15:
                    break

        elif query_type == 'analysis':
            selected = []
            seen_types = set()
            for chunk_idx, similarity in similarities:
                metadata = chunk_metadata[chunk_idx]
                if similarity >= 0.5:
                    selected.append(chunk_idx)
                    seen_types.add(metadata['type'])
                if len(selected) >= 10:
                    break

        else:
            selected = [chunk_idx for chunk_idx, similarity in similarities[:8] if similarity >= 0.7]

        print(f"  Selected {len(selected)} chunks")
        return selected