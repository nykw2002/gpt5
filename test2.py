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
    General Purpose RAG system with query-adaptive retrieval and processing
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
        """Get MD5 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def get_access_token(self) -> bool:
        """Get access token"""
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
        """Get embedding using Ada-002"""
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
    
    def classify_query_type(self, query: str) -> Dict[str, Any]:
        """Classify query to determine optimal processing approach"""
        query_lower = query.lower()
        
        # Pattern analysis
        counting_patterns = [
            r'\bhow many\b',
            r'\bcount\b',
            r'\bnumber of\b',
            r'\btotal\b.*\b(complaints?|entries?|records?|items?)\b',
            r'\blist\b.*\ball\b',
            r'\bfind\b.*\ball\b'
        ]
        
        analysis_patterns = [
            r'\banalyz[es]?\b',
            r'\bcompare\b',
            r'\btrend\b',
            r'\bsummar[yz]e?\b',
            r'\bevaluat[es]?\b',
            r'\bassess\b',
            r'\breview\b',
            r'\breport\b'
        ]
        
        search_patterns = [
            r'\bfind\b',
            r'\bsearch\b',
            r'\blook.?up\b',
            r'\bshow\b.*\bwhere\b',
            r'\bwhat\b.*\bis\b',
            r'\btell me about\b'
        ]
        
        # Check for specific entities/filters
        entity_keywords = []
        if re.search(r'\bisrael\b', query_lower):
            entity_keywords.append('israel')
        if re.search(r'\bsubstantiated\b', query_lower):
            entity_keywords.append('substantiated')
        if re.search(r'\bunsubstantiated\b', query_lower):
            entity_keywords.append('unsubstantiated')
        if re.search(r'\bcapa\b', query_lower):
            entity_keywords.append('capa')
        if re.search(r'\bqe-\b', query_lower):
            entity_keywords.append('qe_format')
        
        # Score patterns
        counting_score = sum(1 for pattern in counting_patterns if re.search(pattern, query_lower))
        analysis_score = sum(1 for pattern in analysis_patterns if re.search(pattern, query_lower))
        search_score = sum(1 for pattern in search_patterns if re.search(pattern, query_lower))
        
        # Determine primary query type
        scores = {
            'counting': counting_score,
            'analysis': analysis_score,
            'search': search_score
        }
        
        primary_type = max(scores, key=scores.get)
        confidence = scores[primary_type] / max(sum(scores.values()), 1)
        
        # Check for complex multi-part queries
        is_complex = len(query) > 200 or query.count('.') > 2 or query.count('?') > 1
        
        return {
            'primary_type': primary_type,
            'confidence': confidence,
            'entity_keywords': entity_keywords,
            'is_complex': is_complex,
            'scores': scores,
            'length': len(query)
        }
    
    def is_complaint_data_line(self, line: str) -> bool:
        """Check if line contains complaint data"""
        line = line.strip()
        if not line:
            return False
        
        patterns = [
            bool(re.match(r'^\d{10,}', line)),
            bool(re.match(r'^QE-\d+', line)),
            bool(re.search(r'\b(Israel|USA|UK|Germany|France|Canada|Australia|Singapore|India|China)\b', line, re.IGNORECASE)) and len(line.split()) >= 4,
            bool(re.search(r'\b(spray|pump|device|substance|dose|nasal|complaint)\b', line, re.IGNORECASE)) and len(line.split()) >= 3
        ]
        
        return any(patterns)
    
    def create_enhanced_chunks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Create chunks with enhanced metadata for general purpose queries"""
        print("Creating enhanced chunks for general purpose processing...")
        
        chunks = []
        current_chunk_lines = []
        current_chunk_type = "unknown"
        
        complaint_chunk_size = 30
        regular_chunk_size = 20
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            is_complaint = self.is_complaint_data_line(line_stripped)
            new_chunk_type = "complaint_data" if is_complaint else "regular"
            
            start_new_chunk = False
            
            if current_chunk_type != new_chunk_type:
                start_new_chunk = True
            elif new_chunk_type == "complaint_data" and len(current_chunk_lines) >= complaint_chunk_size:
                start_new_chunk = True
            elif new_chunk_type == "regular" and len(current_chunk_lines) >= regular_chunk_size:
                start_new_chunk = True
            
            if start_new_chunk and current_chunk_lines:
                chunk_content = '\n'.join(current_chunk_lines)
                metadata = self.calculate_chunk_metadata(chunk_content, current_chunk_lines, i - len(current_chunk_lines), i - 1)
                chunks.append(metadata)
                current_chunk_lines = []
            
            current_chunk_lines.append(line_stripped)
            current_chunk_type = new_chunk_type
        
        # Add final chunk
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            metadata = self.calculate_chunk_metadata(chunk_content, current_chunk_lines, len(lines) - len(current_chunk_lines) + 1, len(lines))
            chunks.append(metadata)
        
        print(f"Created {len(chunks)} enhanced chunks")
        
        return chunks
    
    def calculate_chunk_metadata(self, chunk_content: str, chunk_lines: List[str], start_line: int, end_line: int) -> Dict[str, Any]:
        """Calculate comprehensive metadata for a chunk"""
        content_lower = chunk_content.lower()
        
        # Entity detection
        entities = {}
        entity_patterns = {
            'israel': r'\bisrael\b',
            'usa': r'\busa\b|\bunited states\b',
            'uk': r'\buk\b|\bunited kingdom\b',
            'germany': r'\bgermany\b',
            'france': r'\bfrance\b',
            'singapore': r'\bsingapore\b',
            'south_africa': r'\bsouth africa\b'
        }
        
        for entity, pattern in entity_patterns.items():
            count = len(re.findall(pattern, content_lower))
            if count > 0:
                entities[entity] = count
        
        # Complaint type analysis
        qe_complaints = len([l for l in chunk_lines if l.strip().startswith('QE-')])
        numeric_complaints = len([l for l in chunk_lines if re.match(r'^\d{10,}', l.strip())])
        
        # Content type classification
        chunk_type = "complaint_data" if self.is_complaint_data_line(chunk_lines[0] if chunk_lines else "") else "regular"
        
        # Keyword density analysis
        keywords = {
            'substantiated': len(re.findall(r'\bsubstantiated\b', content_lower)),
            'unsubstantiated': len(re.findall(r'\bunsubstantiated\b', content_lower)),
            'capa': len(re.findall(r'\bcapa\b', content_lower)),
            'pump': len(re.findall(r'\bpump\b', content_lower)),
            'spray': len(re.findall(r'\bspray\b', content_lower)),
            'device': len(re.findall(r'\bdevice\b', content_lower)),
            'substance': len(re.findall(r'\bsubstance\b', content_lower))
        }
        
        return {
            'content': chunk_content,
            'type': chunk_type,
            'line_count': len(chunk_lines),
            'start_line': start_line,
            'end_line': end_line,
            'entities': entities,
            'qe_complaints': qe_complaints,
            'numeric_complaints': numeric_complaints,
            'total_complaints': qe_complaints + numeric_complaints if chunk_type == "complaint_data" else 0,
            'keywords': keywords,
            'char_length': len(chunk_content)
        }
    
    def load_and_process_document(self, file_path: str) -> bool:
        """Load and process document with enhanced metadata"""
        file_hash = self.get_file_hash(file_path)
        cache_file = os.path.join(self.cache_dir, f"general_purpose_{file_hash}.pkl")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                if (cached_data['file_hash'] == file_hash and 
                    os.path.exists(file_path) and
                    cached_data['timestamp'] == os.path.getmtime(file_path)):
                    
                    print("Loading from general purpose cache...")
                    self.chunks = cached_data['chunks']
                    self.chunk_embeddings = cached_data['chunk_embeddings']
                    self.chunk_metadata = cached_data['chunk_metadata']
                    
                    print(f"Loaded {len(self.chunks)} cached chunks")
                    return True
                    
            except Exception as e:
                print(f"Cache loading failed: {e}")
        
        print("Processing document with general purpose enhancement...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Failed to read file: {e}")
            return False
        
        print(f"Document loaded: {len(lines)} lines")
        
        chunks_data = self.create_enhanced_chunks(lines)
        
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
        """Calculate cosine similarity"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def adaptive_chunk_selection(self, query: str, query_classification: Dict[str, Any], max_chunks: int = 25) -> List[int]:
        """Select chunks based on query type and content"""
        print(f"Running adaptive chunk selection for {query_classification['primary_type']} query...")
        
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            return []
        
        # Calculate semantic similarities
        similarities = []
        for i, chunk_embedding in enumerate(self.chunk_embeddings):
            similarity = self.cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((i, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        selected_chunks = set()
        
        # Strategy based on query type
        if query_classification['primary_type'] == 'counting':
            # For counting queries, prioritize entity-specific chunks
            entity_keywords = query_classification['entity_keywords']
            
            # Add all chunks containing target entities
            for i, metadata in enumerate(self.chunk_metadata):
                for entity in entity_keywords:
                    if entity in metadata.get('entities', {}) and metadata['entities'][entity] > 0:
                        selected_chunks.add(i)
            
            print(f"  Entity-based selection: {len(selected_chunks)} chunks")
            
            # Fill remaining slots with high semantic similarity
            remaining_slots = max_chunks - len(selected_chunks)
            for chunk_idx, similarity in similarities:
                if len(selected_chunks) >= max_chunks:
                    break
                if chunk_idx not in selected_chunks and similarity >= 0.4:
                    selected_chunks.add(chunk_idx)
        
        elif query_classification['primary_type'] == 'analysis':
            # For analysis queries, prioritize diverse high-quality chunks
            threshold = 0.3
            
            # Get top semantic matches
            for chunk_idx, similarity in similarities:
                if len(selected_chunks) >= max_chunks:
                    break
                if similarity >= threshold:
                    selected_chunks.add(chunk_idx)
            
            # Ensure we have complaint data chunks for analysis
            complaint_chunks = [i for i, meta in enumerate(self.chunk_metadata) if meta['type'] == 'complaint_data']
            for chunk_idx in complaint_chunks[:10]:  # Add top 10 complaint chunks
                if len(selected_chunks) >= max_chunks:
                    break
                selected_chunks.add(chunk_idx)
        
        else:  # search queries
            # For search queries, focus on semantic similarity
            threshold = 0.3
            for chunk_idx, similarity in similarities:
                if len(selected_chunks) >= max_chunks:
                    break
                if similarity >= threshold:
                    selected_chunks.add(chunk_idx)
        
        result = sorted(list(selected_chunks))
        print(f"  Final selection: {len(result)} chunks")
        
        return result
    
    def generate_adaptive_prompt(self, query: str, query_classification: Dict[str, Any], context_chunks: List[str]) -> str:
        """Generate prompt based on query type"""
        
        if query_classification['primary_type'] == 'counting':
            return self.generate_counting_prompt(query, context_chunks)
        elif query_classification['primary_type'] == 'analysis':
            return self.generate_analysis_prompt(query, context_chunks)
        else:
            return self.generate_search_prompt(query, context_chunks)
    
    def generate_counting_prompt(self, query: str, context_chunks: List[str]) -> str:
        """Generate systematic counting prompt"""
        context = "\n\n".join([f"Data Block {i+1}:\n{chunk}" for i, chunk in enumerate(context_chunks)])
        
        return f"""You are a systematic data analyst. Use step-by-step analysis to ensure 100% accuracy.

TASK: {query}

MANDATORY PROCESS - Follow this exactly:

STEP 1: Process each data block individually and maintain a running count.

Block 1 Analysis:
- Scan every line for relevant items
- List any items found: [list items or state "NONE"]
- Running total after Block 1: [number]

Block 2 Analysis:
- Scan every line for relevant items  
- List any items found: [list items or state "NONE"]
- Running total after Block 2: [number]

[Continue this pattern for ALL {len(context_chunks)} blocks - do not skip any]

STEP 2: Create complete inventory
After processing all blocks, list every item found with block reference:
1. [Item details] (from Block X)
2. [Item details] (from Block Y)
...

STEP 3: Verification
- Count items in your complete list: [number]
- Verify this matches your final running total: [Yes/No]
- If mismatch, recount and correct

DATA TO ANALYZE:
{context}

IMPORTANT: You must process every single block individually and show your running count after each block. Do not summarize or skip blocks."""
    
    def generate_analysis_prompt(self, query: str, context_chunks: List[str]) -> str:
        """Generate analytical prompt"""
        context = "\n\n".join([f"Data Section {i+1}:\n{chunk}" for i, chunk in enumerate(context_chunks)])
        
        return f"""You are an expert data analyst. Provide a comprehensive analysis based on the provided data.

ANALYSIS REQUEST: {query}

APPROACH:
1. Review all data sections systematically
2. Identify relevant patterns, trends, and insights
3. Provide specific examples and evidence
4. Structure your response clearly with headings and bullet points
5. If specific numbers are requested, count carefully and show your work

DATA FOR ANALYSIS:
{context}

RESPONSE FORMAT:
- Use clear headings for different sections of your analysis
- Provide specific evidence from the data
- Include quantitative details where relevant
- Conclude with key insights and recommendations if applicable

Begin your analysis:"""
    
    def generate_search_prompt(self, query: str, context_chunks: List[str]) -> str:
        """Generate search/information retrieval prompt"""
        context = "\n\n".join([f"Information Block {i+1}:\n{chunk}" for i, chunk in enumerate(context_chunks)])
        
        return f"""You are an information specialist. Find and present relevant information based on the query.

SEARCH QUERY: {query}

INSTRUCTIONS:
1. Search through all information blocks for relevant content
2. Extract and present the most pertinent information
3. Organize findings clearly
4. Cite which information blocks contain the relevant details

INFORMATION TO SEARCH:
{context}

Please provide a clear, organized response with the relevant information found."""
    
    def query_gpt5_adaptive(self, query: str, query_classification: Dict[str, Any], context_chunks: List[str]) -> str:
        """Query GPT-5 with adaptive approach"""
        if not self.access_token:
            if not self.get_access_token():
                return "Authentication failed"
        
        prompt = self.generate_adaptive_prompt(query, query_classification, context_chunks)
        
        # Adaptive token limits based on query complexity
        if query_classification['is_complex']:
            max_tokens = 4000
            timeout = 120
        else:
            max_tokens = 3000
            timeout = 90
        
        url = f"{self.kgw_endpoint}/openai/deployments/gpt-5/chat/completions?api-version={self.api_version}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": max_tokens,
            "reasoning_effort": "minimal"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            
            if response.status_code == 401:
                if self.get_access_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                usage = result.get('usage', {})
                print(f"GPT-5 tokens: {usage.get('total_tokens', 0)} total")
                
                return content if content else "No response generated"
            else:
                error_msg = f"GPT-5 request failed: {response.status_code}"
                return error_msg
                
        except Exception as e:
            error_msg = f"GPT-5 error: {e}"
            return error_msg
    
    def query(self, question: str) -> Dict[str, Any]:
        """Execute adaptive query processing"""
        print(f"\nGeneral Purpose Query: {question}")
        print("=" * 60)
        
        # Classify query type
        query_classification = self.classify_query_type(question)
        print(f"Query classification: {query_classification['primary_type']} (confidence: {query_classification['confidence']:.2f})")
        if query_classification['entity_keywords']:
            print(f"Detected entities: {query_classification['entity_keywords']}")
        
        # Select appropriate chunks
        relevant_chunk_indices = self.adaptive_chunk_selection(question, query_classification, max_chunks=25)
        
        if not relevant_chunk_indices:
            return {
                "question": question,
                "answer": "No relevant chunks found",
                "query_classification": query_classification
            }
        
        relevant_chunks = [self.chunks[i] for i in relevant_chunk_indices]
        
        # Analyze chunk composition
        chunk_analysis = {}
        for idx in relevant_chunk_indices:
            chunk_type = self.chunk_metadata[idx]['type']
            chunk_analysis[chunk_type] = chunk_analysis.get(chunk_type, 0) + 1
        
        print(f"Selected {len(relevant_chunks)} chunks for {query_classification['primary_type']} processing:")
        for chunk_type, count in chunk_analysis.items():
            print(f"  {chunk_type}: {count} chunks")
        
        # Generate response
        answer = self.query_gpt5_adaptive(question, query_classification, relevant_chunks)
        
        return {
            "question": question,
            "answer": answer,
            "query_classification": query_classification,
            "chunks_analyzed": len(relevant_chunks),
            "chunk_analysis": chunk_analysis
        }

def main():
    """Main function"""
    rag = GeneralPurposeRAG()
    
    print("General Purpose RAG System")
    print("=" * 40)
    
    if not rag.load_and_process_document("test.txt"):
        print("Failed to load document.")
        return
    
    print("\nGeneral purpose system ready!")
    
    # Interactive mode
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
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()