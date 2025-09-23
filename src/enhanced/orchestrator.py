import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, Any
from general_purpose_rag_new import GeneralPurposeRAG
from .decomposition import QueryDecomposer
from .execution import SubQueryExecutor
from .synthesis import ResultSynthesizer

class EnhancedRAG(GeneralPurposeRAG):
    def __init__(self, cache_dir: str = "./embeddings_cache", progress_callback=None):
        super().__init__(cache_dir)
        self.decomposer = QueryDecomposer()
        self.executor = SubQueryExecutor(self, progress_callback)
        self.synthesizer = ResultSynthesizer(self.auth_manager)
        self.progress_callback = progress_callback
        print("Enhanced RAG System with Prompt Decomposition initialized")

    def _send_progress(self, step: str, status: str, detail: str = ""):
        if self.progress_callback:
            self.progress_callback({
                'step': step,
                'status': status,
                'detail': detail
            })

    def enhanced_query(self, question: str) -> Dict[str, Any]:
        print(f"\nEnhanced Query: {question}")
        print("=" * 60)

        self._send_progress('analysis', 'active', 'Evaluating query structure and complexity...')
        query_complexity = self.decomposer.assess_query_complexity(question)

        if query_complexity < 3:
            print("Simple query detected - using standard processing")
            self._send_progress('analysis', 'completed', f'Complexity: {query_complexity} (Low) - Using standard processing')
            return super().query(question)

        print(f"Complex query detected (complexity: {query_complexity}) - using decomposition")
        self._send_progress('analysis', 'completed', f'Complexity: {query_complexity} (High) - Multi-part analytical query detected')

        self._send_progress('decomposition', 'active', 'Breaking query into focused components...')
        sub_queries = self.decomposer.decompose_complex_query(question)
        self._send_progress('decomposition', 'completed', f'{len(sub_queries)} focused sub-queries generated successfully')

        sub_results = self.executor.execute_sub_queries(sub_queries)

        print(f"\nSynthesizing {len(sub_results)} focused results...")
        self._send_progress('synthesis', 'active', 'Integrating all analysis components...')
        final_answer = self.synthesizer.synthesize_results(question, sub_results)
        self._send_progress('synthesis', 'completed', 'Comprehensive response generated')

        self._send_progress('complete', 'active', 'Validating response quality and formatting...')
        self._send_progress('complete', 'completed', 'Enhanced RAG analysis complete - Response ready')

        return {
            "question": question,
            "answer": final_answer,
            "approach": "decomposition",
            "sub_queries_count": len(sub_queries),
            "sub_results": sub_results,
            "complexity": query_complexity
        }


def main():
    rag = EnhancedRAG()

    print("Enhanced RAG System with Prompt Decomposition")
    print("=" * 60)

    test_file = "test.txt"
    if not os.path.exists(test_file):
        print(f"Test file '{test_file}' not found.")
        return

    if not rag.load_and_process_document(test_file):
        print("Failed to load document.")
        return

    print("\nSystem ready!")

    complex_query = """Analyze the overall complaint numbers by stating total substantiated and unsubstantiated complaints, compare to previous review period using "increased/decreased/remained same", include CAPA details if negative trends exist. Summarize main complaint reasons describing core issues and CAPA status as "in place/ongoing" or "not required". State Israel local market complaint numbers or note "No market-specific trends identified" if none, skip if centralized product. Summarize any significant market-specific trends or patterns. Confirm CAPA status for negative trends or incidents. Conclude using "No adverse trend identified" or "No CAPA required" where applicable."""

    print(f"\n{'='*80}")
    print("TESTING COMPLEX QUERY:")
    print(complex_query)
    print(f"{'='*80}")

    result = rag.enhanced_query(complex_query)

    print(f"\nFINAL COMPREHENSIVE ANSWER:")
    print("=" * 40)
    print(result['answer'])
    print("=" * 40)
    print(f"Approach: {result['approach']}")
    print(f"Sub-queries executed: {result['sub_queries_count']}")
    print(f"Query complexity: {result['complexity']}")


if __name__ == "__main__":
    main()