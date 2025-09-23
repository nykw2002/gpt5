from typing import List, Dict, Any

class SubQueryExecutor:
    def __init__(self, base_rag, progress_callback=None):
        self.base_rag = base_rag
        self.progress_callback = progress_callback

    def _send_progress(self, step: str, status: str, detail: str = ""):
        if self.progress_callback:
            self.progress_callback({
                'step': step,
                'status': status,
                'detail': detail
            })

    def execute_sub_queries(self, sub_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = {}

        for sub_query in sub_queries:
            focus = sub_query['focus']
            print(f"\nExecuting: {focus}")
            print(f"Query: {sub_query['query']}")

            self._send_progress(focus, 'active', f"Processing {focus.replace('_', ' ')}...")

            result = self.base_rag.query(sub_query['query'])

            results[focus] = {
                'query': sub_query['query'],
                'answer': result['answer'],
                'type': sub_query['type'],
                'chunks_analyzed': result['chunks_analyzed']
            }

            print(f"Result preview: {result['answer'][:200]}...")

            preview = result['answer'][:80] if result['answer'] else "Processing completed"
            self._send_progress(focus, 'completed', preview)

        return results