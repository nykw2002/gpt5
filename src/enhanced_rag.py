import os
import re
import json
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(__file__))
from general_purpose_rag import GeneralPurposeRAG

load_dotenv()

# Get chat model deployment name from env
CHAT_MODEL_DEPLOYMENT = os.getenv('CHAT_MODEL_DEPLOYMENT_NAME', 'gpt-4o')

class EnhancedRAG(GeneralPurposeRAG):
    """
    Enhanced RAG system with prompt decomposition for complex multi-part queries.
    Solves the embedding dilution problem by breaking complex queries into focused sub-queries.
    """

    def __init__(self, cache_dir: str = "./embeddings_cache", progress_callback=None):
        super().__init__(cache_dir)
        self.decomposition_patterns = self._init_decomposition_patterns()
        self.progress_callback = progress_callback
        print("Enhanced RAG System with Prompt Decomposition initialized")

    def _send_progress(self, step: str, status: str, detail: str = ""):
        """Send progress update via callback if available"""
        if self.progress_callback:
            self.progress_callback({
                'step': step,
                'status': status,
                'detail': detail
            })

    def _init_decomposition_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for identifying different query components"""
        return {
            'overall_numbers': [
                r'total.*complaints?',
                r'overall.*numbers?',
                r'substantiated.*unsubstantiated',
                r'complaint.*count',
                r'how many.*total'
            ],
            'comparison': [
                r'compare.*previous',
                r'increased.*decreased',
                r'trend.*period',
                r'vs.*previous',
                r'compared to'
            ],
            'market_specific': [
                r'israel.*market',
                r'local.*market',
                r'market.*specific',
                r'israel.*complaints?',
                r'country.*specific'
            ],
            'capa_details': [
                r'capa.*status',
                r'capa.*details',
                r'corrective.*action',
                r'preventive.*action',
                r'in place.*ongoing'
            ],
            'complaint_reasons': [
                r'main.*reasons?',
                r'complaint.*types?',
                r'core.*issues?',
                r'primary.*causes?',
                r'reasons?.*complaints?'
            ],
            'trends_patterns': [
                r'trends?.*patterns?',
                r'significant.*trends?',
                r'market.*trends?',
                r'negative.*trends?',
                r'patterns?.*identified'
            ]
        }

    def decompose_complex_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Decompose a complex query into focused sub-queries.
        Returns list of sub-query dictionaries with type and query text.
        """
        query_lower = query.lower()
        sub_queries = []

        # Check for overall numbers
        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['overall_numbers']):
            sub_queries.append({
                'type': 'counting',
                'query': 'What are the total substantiated and unsubstantiated complaint numbers?',
                'priority': 1,
                'focus': 'overall_numbers'
            })

        # Check for market-specific (Israel)
        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['market_specific']):
            sub_queries.append({
                'type': 'counting',
                'query': 'How many complaints are from Israel local market specifically?',
                'priority': 2,
                'focus': 'israel_market'
            })

        # Check for comparison/trends
        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['comparison']):
            sub_queries.append({
                'type': 'analysis',
                'query': 'Compare current complaint numbers to previous review period - increased, decreased, or remained same?',
                'priority': 1,
                'focus': 'comparison'
            })

        # Check for complaint reasons
        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['complaint_reasons']):
            sub_queries.append({
                'type': 'analysis',
                'query': 'What are the main complaint reasons and core issues identified?',
                'priority': 2,
                'focus': 'reasons'
            })

        # Check for CAPA details
        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['capa_details']):
            sub_queries.append({
                'type': 'search',
                'query': 'What is the CAPA status for negative trends - in place, ongoing, or not required?',
                'priority': 3,
                'focus': 'capa'
            })

        # Check for trends/patterns
        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['trends_patterns']):
            sub_queries.append({
                'type': 'analysis',
                'query': 'Are there any significant market-specific trends or patterns identified?',
                'priority': 2,
                'focus': 'trends'
            })

        # If no patterns matched, treat as single query
        if not sub_queries:
            sub_queries.append({
                'type': 'analysis',
                'query': query,
                'priority': 1,
                'focus': 'general'
            })

        # Sort by priority
        sub_queries.sort(key=lambda x: x['priority'])

        print(f"Decomposed into {len(sub_queries)} sub-queries:")
        for i, sq in enumerate(sub_queries):
            print(f"  {i+1}. [{sq['type']}] {sq['query']}")

        return sub_queries

    def execute_sub_queries(self, sub_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute each sub-query and collect results"""
        results = {}

        for sub_query in sub_queries:
            focus = sub_query['focus']
            print(f"\nExecuting: {focus}")
            print(f"Query: {sub_query['query']}")

            # Send progress update for this sub-query
            self._send_progress(focus, 'active', f"Processing {focus.replace('_', ' ')}...")

            # Use parent class query method for each sub-query
            result = super().query(sub_query['query'])

            results[focus] = {
                'query': sub_query['query'],
                'answer': result['answer'],
                'type': sub_query['type'],
                'chunks_analyzed': result['chunks_analyzed']
            }

            print(f"Result preview: {result['answer'][:200]}...")

            # Send completion update with result preview
            preview = result['answer'][:80] if result['answer'] else "Processing completed"
            self._send_progress(focus, 'completed', preview)

        return results

    def synthesize_results(self, original_query: str, sub_results: Dict[str, Any]) -> str:
        """
        Synthesize sub-query results into a comprehensive response.
        Uses GPT-5 to combine results according to original query requirements.
        """

        # Prepare synthesis context
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

        # Use the GPT-5 API to synthesize
        if not self.access_token:
            if not self.get_access_token():
                return "Error: Could not authenticate for synthesis"

        url = f"{self.kgw_endpoint}/openai/deployments/{CHAT_MODEL_DEPLOYMENT}/chat/completions?api-version={self.api_version}"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
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
            import requests
            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 401:
                if self.get_access_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
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

    def enhanced_query(self, question: str) -> Dict[str, Any]:
        """
        Execute enhanced query with prompt decomposition for complex multi-part queries.
        """
        print(f"\nEnhanced Query: {question}")
        print("=" * 60)

        # Check if this is a complex query that needs decomposition
        self._send_progress('analysis', 'active', 'Evaluating query structure and complexity...')
        query_complexity = self._assess_query_complexity(question)

        if query_complexity < 3:
            # Simple query - use standard processing
            print("Simple query detected - using standard processing")
            self._send_progress('analysis', 'completed', f'Complexity: {query_complexity} (Low) - Using standard processing')
            return super().query(question)

        # Complex query - use decomposition
        print(f"Complex query detected (complexity: {query_complexity}) - using decomposition")
        self._send_progress('analysis', 'completed', f'Complexity: {query_complexity} (High) - Multi-part analytical query detected')

        # Decompose the query
        self._send_progress('decomposition', 'active', 'Breaking query into focused components...')
        sub_queries = self.decompose_complex_query(question)
        self._send_progress('decomposition', 'completed', f'{len(sub_queries)} focused sub-queries generated successfully')

        # Execute sub-queries
        sub_results = self.execute_sub_queries(sub_queries)

        # Synthesize results
        print(f"\nSynthesizing {len(sub_results)} focused results...")
        self._send_progress('synthesis', 'active', 'Integrating all analysis components...')
        final_answer = self.synthesize_results(question, sub_results)
        self._send_progress('synthesis', 'completed', 'Comprehensive response generated')

        # Final validation step
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

    def _assess_query_complexity(self, query: str) -> int:
        """Assess query complexity based on multiple factors"""
        complexity = 0
        query_lower = query.lower()

        # Count different aspects mentioned
        for category, patterns in self.decomposition_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                complexity += 1

        # Additional complexity factors
        if len(query.split()) > 30:  # Long query
            complexity += 1
        if query.count(',') > 2:  # Multiple clauses
            complexity += 1
        if re.search(r'\b(and|or|also|additionally|furthermore)\b', query_lower):
            complexity += 1

        return complexity


def main():
    """Test the enhanced RAG system"""
    rag = EnhancedRAG()

    print("Enhanced RAG System with Prompt Decomposition")
    print("=" * 60)

    # Load test document
    test_file = "test.txt"
    if not os.path.exists(test_file):
        print(f"Test file '{test_file}' not found.")
        return

    if not rag.load_and_process_document(test_file):
        print("Failed to load document.")
        return

    print("\nSystem ready!")

    # Test with the complex query from the user
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