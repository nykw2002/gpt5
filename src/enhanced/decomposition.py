import re
from typing import List, Dict, Any

class QueryDecomposer:
    def __init__(self):
        self.decomposition_patterns = self._init_decomposition_patterns()

    def _init_decomposition_patterns(self) -> Dict[str, List[str]]:
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
        query_lower = query.lower()
        sub_queries = []

        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['overall_numbers']):
            sub_queries.append({
                'type': 'counting',
                'query': 'What are the total substantiated and unsubstantiated complaint numbers?',
                'priority': 1,
                'focus': 'overall_numbers'
            })

        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['market_specific']):
            sub_queries.append({
                'type': 'counting',
                'query': 'How many complaints are from Israel local market specifically?',
                'priority': 2,
                'focus': 'israel_market'
            })

        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['comparison']):
            sub_queries.append({
                'type': 'analysis',
                'query': 'Compare current complaint numbers to previous review period - increased, decreased, or remained same?',
                'priority': 1,
                'focus': 'comparison'
            })

        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['complaint_reasons']):
            sub_queries.append({
                'type': 'analysis',
                'query': 'What are the main complaint reasons and core issues identified?',
                'priority': 2,
                'focus': 'reasons'
            })

        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['capa_details']):
            sub_queries.append({
                'type': 'search',
                'query': 'What is the CAPA status for negative trends - in place, ongoing, or not required?',
                'priority': 3,
                'focus': 'capa'
            })

        if any(re.search(pattern, query_lower) for pattern in self.decomposition_patterns['trends_patterns']):
            sub_queries.append({
                'type': 'analysis',
                'query': 'Are there any significant market-specific trends or patterns identified?',
                'priority': 2,
                'focus': 'trends'
            })

        if not sub_queries:
            sub_queries.append({
                'type': 'analysis',
                'query': query,
                'priority': 1,
                'focus': 'general'
            })

        sub_queries.sort(key=lambda x: x['priority'])

        print(f"Decomposed into {len(sub_queries)} sub-queries:")
        for i, sq in enumerate(sub_queries):
            print(f"  {i+1}. [{sq['type']}] {sq['query']}")

        return sub_queries

    def assess_query_complexity(self, query: str) -> int:
        complexity = 0
        query_lower = query.lower()

        for category, patterns in self.decomposition_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                complexity += 1

        if len(query.split()) > 30:
            complexity += 1
        if query.count(',') > 2:
            complexity += 1
        if re.search(r'\b(and|or|also|additionally|furthermore)\b', query_lower):
            complexity += 1

        return complexity