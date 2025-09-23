#!/usr/bin/env python3
"""
Test script for the Enhanced RAG system with prompt decomposition.
Demonstrates how complex multi-part queries are handled vs simple queries.
"""

import sys
import os
sys.path.append('./src')

from enhanced_rag import EnhancedRAG

def test_enhanced_rag():
    print("🚀 Testing Enhanced RAG with Prompt Decomposition")
    print("=" * 70)

    # Initialize system
    rag = EnhancedRAG()

    # Load document
    test_file = "test.txt"
    if not os.path.exists(test_file):
        print(f"❌ Test file '{test_file}' not found.")
        return

    print("📄 Loading document...")
    if not rag.load_and_process_document(test_file):
        print("❌ Failed to load document.")
        return

    print("✅ Document loaded successfully!")
    print()

    # Test cases
    test_cases = [
        {
            "name": "Simple Query (Standard Processing)",
            "query": "How many complaints are from Israel?",
            "expected_approach": "standard"
        },
        {
            "name": "Complex Multi-Part Query (Decomposition)",
            "query": """Analyze the overall complaint numbers by stating total substantiated and unsubstantiated complaints, compare to previous review period using "increased/decreased/remained same", include CAPA details if negative trends exist. Summarize main complaint reasons describing core issues and CAPA status as "in place/ongoing" or "not required". State Israel local market complaint numbers or note "No market-specific trends identified" if none, skip if centralized product.""",
            "expected_approach": "decomposition"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 TEST CASE {i}: {test_case['name']}")
        print("-" * 50)
        print(f"Query: {test_case['query']}")
        print()

        try:
            result = rag.enhanced_query(test_case['query'])

            # Display results
            print(f"📊 RESULTS:")
            print(f"  Approach: {result.get('approach', 'standard')}")

            if 'sub_queries_count' in result:
                print(f"  Sub-queries: {result['sub_queries_count']}")
                print(f"  Complexity: {result['complexity']}")

            if 'chunks_analyzed' in result:
                print(f"  Chunks analyzed: {result['chunks_analyzed']}")

            print()
            print(f"📝 ANSWER:")
            print(result['answer'])
            print()

            # Show decomposition details for complex queries
            if result.get('approach') == 'decomposition' and 'sub_results' in result:
                print(f"🔍 DECOMPOSITION BREAKDOWN:")
                for focus, sub_result in result['sub_results'].items():
                    print(f"  • {focus}: {sub_result['answer'][:100]}...")
                print()

        except Exception as e:
            print(f"❌ Error: {e}")
            print()

        print("=" * 70)
        print()

def main():
    try:
        test_enhanced_rag()
        print("✅ Testing completed!")
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"❌ Testing failed: {e}")

if __name__ == "__main__":
    main()