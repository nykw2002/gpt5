import os
import requests
import numpy as np
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import json
import re
import pickle
import hashlib

load_dotenv()

class GeneralPurposeRAG:
    """
    General Purpose RAG system with query-adaptive processing and Chain of Thought reasoning.
    Optimized for GPT-5 with sophisticated chunking strategies and multi-modal query handling.
    """

    def __init__(self, cache_dir: str = "./embeddings_cache"):
        # Configuration
        self.ping_fed_url = os.getenv('PING_FED_URL')
        self.kgw_client_id = os.getenv('KGW_CLIENT_ID')
        self.kgw_client_secret = os.getenv('KGW_CLIENT_SECRET')
        self.kgw_endpoint = os.getenv('KGW_ENDPOINT')
        self.api_version = os.getenv('AOAI_API_VERSION')
        self.embedding_model = os.getenv('EMBEDDING_MODEL_DEPLOYMENT_NAME')

        self.access_token = None
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        # Storage
        self.chunks = []
        self.chunk_embeddings = []
        self.chunk_metadata = []

        print("General Purpose RAG System initialized")

    def get_file_hash(self, file_path: str) -> str:
        """Get MD5 hash of file for caching"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""

    def get_access_token(self) -> bool:
        """Get access token for API authentication"""
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.kgw_client_id,
            'client_secret': self.kgw_client_secret
        }

        try:
            response = requests.post(
                self.ping_fed_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )

            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                return True
            return False
        except Exception as e:
            print(f"Token error: {e}")
            return False

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using configured embedding model"""
        if not self.access_token:
            if not self.get_access_token():
                return []

        url = f"{self.kgw_endpoint}/openai/deployments/{self.embedding_model}/embeddings?api-version={self.api_version}"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {"input": text}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 401:
                if self.get_access_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
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

    def classify_query(self, query: str) -> str:
        """Classify query type for adaptive processing"""
        query_lower = query.lower()

        # Counting queries
        counting_patterns = [
            'how many', 'count', 'number of', 'total', 'sum of',
            'quantity', 'amount of', 'frequency'
        ]

        # Analysis queries
        analysis_patterns = [
            'analyze', 'compare', 'relationship', 'pattern', 'trend',
            'correlation', 'summary', 'overview', 'insights'
        ]

        # Search queries
        search_patterns = [
            'find', 'search', 'locate', 'where', 'which', 'what is',
            'show me', 'list', 'identify'
        ]

        if any(pattern in query_lower for pattern in counting_patterns):
            return 'counting'
        elif any(pattern in query_lower for pattern in analysis_patterns):
            return 'analysis'
        elif any(pattern in query_lower for pattern in search_patterns):
            return 'search'
        else:
            return 'general'

    def detect_content_type(self, line: str) -> str:
        """Detect content type for adaptive chunking"""
        line = line.strip()
        if not line:
            return 'empty'

        # Structured data patterns
        if re.match(r'^\d{10,}', line) or re.match(r'^[A-Z]{2,3}-\d+', line):
            return 'structured_data'

        # Table-like data
        if len(line.split('\t')) > 3 or len(line.split(',')) > 3:
            return 'tabular'

        # Headers and titles
        if line.isupper() or line.endswith(':'):
            return 'header'

        # Regular text
        return 'text'

    def create_adaptive_chunks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Create chunks with adaptive sizing based on content type"""
        print("Creating adaptive chunks...")

        chunks = []
        current_chunk_lines = []
        current_content_type = "unknown"

        # Adaptive chunk sizes
        chunk_sizes = {
            'structured_data': 25,  # Smaller chunks for structured data
            'tabular': 15,          # Very small for tables
            'header': 50,           # Larger for headers and context
            'text': 30,             # Standard for regular text
            'empty': 0              # Skip empty lines
        }

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            if not line_stripped:
                continue

            content_type = self.detect_content_type(line_stripped)

            # Check if we need a new chunk
            start_new_chunk = (
                current_content_type != content_type or
                len(current_chunk_lines) >= chunk_sizes.get(content_type, 30)
            )

            if start_new_chunk and current_chunk_lines:
                chunk_content = '\n'.join(current_chunk_lines)
                chunks.append({
                    'content': chunk_content,
                    'type': current_content_type,
                    'line_count': len(current_chunk_lines),
                    'start_line': i - len(current_chunk_lines) + 1,
                    'end_line': i
                })
                current_chunk_lines = []

            current_chunk_lines.append(line_stripped)
            current_content_type = content_type

        # Add final chunk
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            chunks.append({
                'content': chunk_content,
                'type': current_content_type,
                'line_count': len(current_chunk_lines),
                'start_line': len(lines) - len(current_chunk_lines) + 1,
                'end_line': len(lines)
            })

        # Print chunk analysis
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk['type']
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        print(f"Created {len(chunks)} adaptive chunks:")
        for chunk_type, count in chunk_types.items():
            print(f"  {chunk_type}: {count} chunks")

        return chunks

    def load_and_process_document(self, file_path: str) -> bool:
        """Load and process document with adaptive chunking and caching"""
        file_hash = self.get_file_hash(file_path)
        cache_file = os.path.join(self.cache_dir, f"general_rag_{file_hash}.pkl")

        # Try cache first
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)

                if (cached_data['file_hash'] == file_hash and
                    os.path.exists(file_path) and
                    cached_data['timestamp'] == os.path.getmtime(file_path)):

                    print("Loading from cache...")
                    self.chunks = cached_data['chunks']
                    self.chunk_embeddings = cached_data['chunk_embeddings']
                    self.chunk_metadata = cached_data['chunk_metadata']

                    print(f"Loaded {len(self.chunks)} cached chunks")
                    return True

            except Exception as e:
                print(f"Cache loading failed: {e}")

        # Process from scratch
        print("Processing document...")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Failed to read file: {e}")
            return False

        print(f"Document loaded: {len(lines)} lines")

        # Create adaptive chunks
        chunks_data = self.create_adaptive_chunks(lines)

        # Create embeddings
        print("Creating embeddings...")
        self.chunks = []
        self.chunk_embeddings = []
        self.chunk_metadata = []

        for i, chunk_data in enumerate(chunks_data):
            if i % 20 == 0:
                print(f"  Processing chunk {i+1}/{len(chunks_data)}")

            content = chunk_data['content']
            embedding = self.get_embedding(content)

            if not embedding:
                print(f"Failed to get embedding for chunk {i+1}")
                return False

            self.chunks.append(content)
            self.chunk_embeddings.append(embedding)
            self.chunk_metadata.append(chunk_data)

        # Save to cache
        try:
            cache_data = {
                'file_hash': file_hash,
                'timestamp': os.path.getmtime(file_path),
                'chunks': self.chunks,
                'chunk_embeddings': self.chunk_embeddings,
                'chunk_metadata': self.chunk_metadata
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"Cached to: {cache_file}")

        except Exception as e:
            print(f"Failed to cache: {e}")

        return True

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0

        return dot_product / (norm1 * norm2)

    def adaptive_search(self, query: str, query_type: str) -> List[int]:
        """Adaptive search based on query classification"""
        print(f"Running adaptive search for {query_type} query...")

        query_embedding = self.get_embedding(query)
        if not query_embedding:
            return []

        # Calculate similarities
        similarities = []
        for i, chunk_embedding in enumerate(self.chunk_embeddings):
            similarity = self.cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((i, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Adaptive selection based on query type
        if query_type == 'counting':
            # For counting: prioritize structured data, lower threshold
            selected = []
            for chunk_idx, similarity in similarities:
                metadata = self.chunk_metadata[chunk_idx]
                if metadata['type'] == 'structured_data' and similarity >= 0.3:
                    selected.append(chunk_idx)
                elif similarity >= 0.6:
                    selected.append(chunk_idx)
                if len(selected) >= 15:  # More chunks for counting
                    break

        elif query_type == 'analysis':
            # For analysis: diverse content types, medium threshold
            selected = []
            seen_types = set()
            for chunk_idx, similarity in similarities:
                metadata = self.chunk_metadata[chunk_idx]
                if similarity >= 0.5:
                    selected.append(chunk_idx)
                    seen_types.add(metadata['type'])
                if len(selected) >= 10:
                    break

        else:
            # Default: high relevance chunks
            selected = [chunk_idx for chunk_idx, similarity in similarities[:8] if similarity >= 0.7]

        print(f"  Selected {len(selected)} chunks")
        return selected

    def query_gpt5_with_cot(self, query: str, context_chunks: List[str], query_type: str) -> str:
        """Query GPT-5 with Chain of Thought reasoning"""
        if not self.access_token:
            if not self.get_access_token():
                return "Authentication failed"

        context = "\n\n".join([f"Data Block {i+1}:\n{chunk}" for i, chunk in enumerate(context_chunks)])

        # Adaptive prompting based on query type
        if query_type == 'counting':
            system_prompt = """You are an expert data analyst. When counting items, use Chain of Thought reasoning:
1. First, identify all relevant items in each data block
2. Count them systematically
3. Double-check your count
4. Provide the final total with confidence

Be thorough and accurate. Show your reasoning process."""

        elif query_type == 'analysis':
            system_prompt = """You are an expert data analyst. When analyzing data:
1. First, examine the data structure and patterns
2. Identify key insights and relationships
3. Synthesize findings into clear conclusions
4. Support your analysis with specific evidence

Provide comprehensive analysis with clear reasoning."""

        else:
            system_prompt = """You are an expert assistant. Analyze the provided data carefully and answer the question thoroughly with supporting evidence."""

        prompt = f"""{system_prompt}

DATA:
{context}

QUESTION: {query}

ANSWER:"""

        url = f"{self.kgw_endpoint}/openai/deployments/gpt-5/chat/completions?api-version={self.api_version}"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Adaptive reasoning effort based on query complexity
        reasoning_effort = "medium" if query_type in ['counting', 'analysis'] else "minimal"

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": 3000,
            "reasoning_effort": reasoning_effort
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)

            if response.status_code == 401:
                if self.get_access_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.post(url, headers=headers, json=payload, timeout=90)

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']

                usage = result.get('usage', {})
                completion_details = usage.get('completion_tokens_details', {})
                reasoning_tokens = completion_details.get('reasoning_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0) - reasoning_tokens

                print(f"GPT-5 tokens: {reasoning_tokens} reasoning + {output_tokens} output = {usage.get('total_tokens', 0)} total")

                return content if content else "No response generated"
            else:
                return f"GPT-5 request failed: {response.status_code}"

        except Exception as e:
            return f"GPT-5 error: {e}"

    def query(self, question: str) -> Dict[str, Any]:
        """Execute adaptive query with Chain of Thought reasoning"""
        print(f"\nQuery: {question}")
        print("=" * 50)

        # Classify query for adaptive processing
        query_type = self.classify_query(question)
        print(f"Query type: {query_type}")

        # Find relevant chunks using adaptive search
        relevant_chunk_indices = self.adaptive_search(question, query_type)

        if not relevant_chunk_indices:
            return {
                "question": question,
                "answer": "No relevant chunks found",
                "query_type": query_type,
                "chunks_analyzed": 0
            }

        # Get chunks and analyze composition
        relevant_chunks = [self.chunks[i] for i in relevant_chunk_indices]

        chunk_types = {}
        for idx in relevant_chunk_indices:
            chunk_type = self.chunk_metadata[idx]['type']
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        print(f"Sending {len(relevant_chunks)} chunks to GPT-5:")
        for chunk_type, count in chunk_types.items():
            print(f"  {chunk_type}: {count} chunks")

        # Generate answer with Chain of Thought
        answer = self.query_gpt5_with_cot(question, relevant_chunks, query_type)

        return {
            "question": question,
            "answer": answer,
            "query_type": query_type,
            "chunks_analyzed": len(relevant_chunks),
            "chunk_types": chunk_types
        }


def main():
    """Main function for testing the RAG system"""
    rag = GeneralPurposeRAG()

    print("General Purpose RAG System - GPT-5 Optimized")
    print("=" * 50)

    # Load test document
    test_file = "test.txt"
    if not os.path.exists(test_file):
        print(f"Test file '{test_file}' not found. Please ensure it exists.")
        return

    if not rag.load_and_process_document(test_file):
        print("Failed to load document.")
        return

    print("\nSystem ready!")

    # Test queries
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

    # Interactive mode
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