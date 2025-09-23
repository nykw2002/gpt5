import os
from typing import List, Dict, Any
from core import AuthManager, EmbeddingService, ChunkingService, SearchService, LLMService, QualityEvaluator

class GeneralPurposeRAG:
    def __init__(self, cache_dir: str = "./embeddings_cache"):
        self.auth_manager = AuthManager()
        self.embedding_service = EmbeddingService(self.auth_manager)
        self.chunking_service = ChunkingService(self.embedding_service, cache_dir)
        self.search_service = SearchService(self.embedding_service)
        self.llm_service = LLMService(self.auth_manager)
        self.quality_evaluator = QualityEvaluator(self.auth_manager)

        self.chunks = []
        self.chunk_embeddings = []
        self.chunk_metadata = []

        print("General Purpose RAG System initialized")

    def load_and_process_document(self, file_path: str) -> bool:
        result = self.chunking_service.load_and_process_document(file_path)
        if result[0] is None:
            return False

        self.chunks, self.chunk_embeddings, self.chunk_metadata = result
        return True

    def query(self, question: str) -> Dict[str, Any]:
        print(f"\nQuery: {question}")
        print("=" * 50)

        query_type = self.search_service.classify_query(question)
        print(f"Query type: {query_type}")

        relevant_chunk_indices = self.search_service.adaptive_search(
            question, query_type, self.chunk_embeddings, self.chunk_metadata
        )

        if not relevant_chunk_indices:
            return {
                "question": question,
                "answer": "No relevant chunks found",
                "query_type": query_type,
                "chunks_analyzed": 0
            }

        relevant_chunks = [self.chunks[i] for i in relevant_chunk_indices]

        chunk_types = {}
        for idx in relevant_chunk_indices:
            chunk_type = self.chunk_metadata[idx]['type']
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        print(f"Sending {len(relevant_chunks)} chunks to GPT-5:")
        for chunk_type, count in chunk_types.items():
            print(f"  {chunk_type}: {count} chunks")

        answer = self.llm_service.query_gpt5_with_cot(question, relevant_chunks, query_type)

        quality_metrics = self.quality_evaluator.evaluate_answer_quality(question, answer, relevant_chunks)

        return {
            "question": question,
            "answer": answer,
            "query_type": query_type,
            "chunks_analyzed": len(relevant_chunks),
            "chunk_types": chunk_types,
            "quality_metrics": quality_metrics,
            "relevant_chunk_indices": relevant_chunk_indices
        }


def main():
    rag = GeneralPurposeRAG()

    print("General Purpose RAG System - GPT-5 Optimized")
    print("=" * 50)

    test_file = "test.txt"
    if not os.path.exists(test_file):
        print(f"Test file '{test_file}' not found. Please ensure it exists.")
        return

    if not rag.load_and_process_document(test_file):
        print("Failed to load document.")
        return

    print("\nSystem ready!")

    test_queries = [
        "How many complaints are from Israel?",
        "Analyze the distribution of complaints by country",
        "Find all entries with batch code QE-"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        result = rag.query(query)
        print(f"Answer: {result['answer']}")
        print(f"Query type: {result['query_type']}")
        print(f"Chunks analyzed: {result['chunks_analyzed']}")

    print(f"\n{'='*60}")
    choice = input("Continue with interactive mode? (y/n): ").strip().lower()

    if choice in ['y', 'yes']:
        print("Type 'quit' to exit")

        while True:
            try:
                question = input("\nYour question: ").strip()

                if question.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break

                if not question:
                    continue

                result = rag.query(question)
                print(f"\nAnswer: {result['answer']}")
                print(f"Query type: {result['query_type']}")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()