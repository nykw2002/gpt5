#!/usr/bin/env python3
"""Quick test of the Enhanced RAG system"""

import sys
import os
sys.path.append('./src')

from enhanced_rag import EnhancedRAG

def quick_test():
    print("🚀 Quick Enhanced RAG Test")
    print("=" * 40)

    # Initialize
    rag = EnhancedRAG()

    # Test complexity assessment first
    simple_query = "How many complaints are from Israel?"
    complex_query = """Analyze the overall complaint numbers by stating total substantiated and unsubstantiated complaints, compare to previous review period using "increased/decreased/remained same", include CAPA details if negative trends exist."""

    print("📊 Testing Query Complexity Assessment:")
    print(f"Simple: '{simple_query}' → Complexity: {rag._assess_query_complexity(simple_query)}")
    print(f"Complex: '{complex_query[:60]}...' → Complexity: {rag._assess_query_complexity(complex_query)}")
    print()

    # Test decomposition without running full queries
    print("🔧 Testing Query Decomposition:")
    sub_queries = rag.decompose_complex_query(complex_query)
    print(f"Decomposed into {len(sub_queries)} sub-queries:")
    for i, sq in enumerate(sub_queries, 1):
        print(f"  {i}. [{sq['type']}] {sq['query'][:60]}...")
    print()

    print("✅ Quick test completed!")

if __name__ == "__main__":
    quick_test()