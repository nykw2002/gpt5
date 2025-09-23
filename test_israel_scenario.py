#!/usr/bin/env python3
"""
Test the specific Israel complaints scenario that was problematic.
Compare standard vs enhanced RAG performance.
"""

import sys
import os
sys.path.append('./src')

from enhanced_rag import EnhancedRAG
from general_purpose_rag import GeneralPurposeRAG

def test_israel_scenario():
    print("🇮🇱 Testing Israel Complaints Scenario")
    print("=" * 50)

    # Test queries
    simple_query = "How many complaints are from Israel?"

    complex_query = """Analyze the overall complaint numbers by stating total substantiated and unsubstantiated complaints, compare to previous review period using "increased/decreased/remained same", include CAPA details if negative trends exist. Summarize main complaint reasons describing core issues and CAPA status as "in place/ongoing" or "not required". State Israel local market complaint numbers or note "No market-specific trends identified" if none, skip if centralized product."""

    # Load document first
    test_file = "test.txt"
    if not os.path.exists(test_file):
        print(f"❌ Test file '{test_file}' not found.")
        return

    print("📄 Loading document...")

    # Test 1: Standard RAG with simple query
    print("\n🧪 TEST 1: Standard RAG - Simple Israel Query")
    print("-" * 40)
    standard_rag = GeneralPurposeRAG()
    if standard_rag.load_and_process_document(test_file):
        result1 = standard_rag.query(simple_query)
        print(f"Query: {simple_query}")
        print(f"Answer: {result1['answer']}")
        print(f"Chunks analyzed: {result1['chunks_analyzed']}")
    else:
        print("❌ Failed to load document for standard RAG")
        return

    # Test 2: Standard RAG with complex query
    print(f"\n🧪 TEST 2: Standard RAG - Complex Query")
    print("-" * 40)
    print(f"Query: {complex_query[:100]}...")
    result2 = standard_rag.query(complex_query)
    print(f"Answer preview: {result2['answer'][:300]}...")
    print(f"Chunks analyzed: {result2['chunks_analyzed']}")

    # Test 3: Enhanced RAG with complex query
    print(f"\n🧪 TEST 3: Enhanced RAG - Complex Query (Decomposition)")
    print("-" * 40)
    enhanced_rag = EnhancedRAG()
    if enhanced_rag.load_and_process_document(test_file):
        print(f"Query: {complex_query[:100]}...")
        result3 = enhanced_rag.enhanced_query(complex_query)
        print(f"Approach: {result3.get('approach', 'N/A')}")
        if 'sub_queries_count' in result3:
            print(f"Sub-queries: {result3['sub_queries_count']}")
        print(f"Answer preview: {result3['answer'][:300]}...")

        # Show specific Israel results if available
        if 'sub_results' in result3:
            for focus, sub_result in result3['sub_results'].items():
                if 'israel' in focus.lower():
                    print(f"\n🎯 Israel-specific result:")
                    print(f"  Focus: {focus}")
                    print(f"  Answer: {sub_result['answer']}")
    else:
        print("❌ Failed to load document for enhanced RAG")

    print(f"\n✅ Testing completed!")
    print("\n📊 SUMMARY:")
    print("- Test 1: Standard RAG handles simple Israel query well")
    print("- Test 2: Standard RAG may miss Israel details in complex query")
    print("- Test 3: Enhanced RAG decomposes complex query for better results")

if __name__ == "__main__":
    test_israel_scenario()