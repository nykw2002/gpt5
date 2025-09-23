import os
import re
import pickle
import hashlib
from typing import List, Dict, Any
from .config import CHUNK_SIZES

class ChunkingService:
    def __init__(self, embedding_service, cache_dir: str = "./embeddings_cache"):
        self.embedding_service = embedding_service
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""

    @staticmethod
    def detect_content_type(line: str) -> str:
        line = line.strip()
        if not line:
            return 'empty'

        if re.match(r'^\d{10,}', line) or re.match(r'^[A-Z]{2,3}-\d+', line):
            return 'structured_data'

        if len(line.split('\t')) > 3 or len(line.split(',')) > 3:
            return 'tabular'

        if line.isupper() or line.endswith(':'):
            return 'header'

        return 'text'

    def create_adaptive_chunks(self, lines: List[str]) -> List[Dict[str, Any]]:
        print("Creating adaptive chunks...")

        chunks = []
        current_chunk_lines = []
        current_content_type = "unknown"

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            if not line_stripped:
                continue

            content_type = self.detect_content_type(line_stripped)

            start_new_chunk = (
                current_content_type != content_type or
                len(current_chunk_lines) >= CHUNK_SIZES.get(content_type, 30)
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

        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            chunks.append({
                'content': chunk_content,
                'type': current_content_type,
                'line_count': len(current_chunk_lines),
                'start_line': len(lines) - len(current_chunk_lines) + 1,
                'end_line': len(lines)
            })

        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk['type']
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        print(f"Created {len(chunks)} adaptive chunks:")
        for chunk_type, count in chunk_types.items():
            print(f"  {chunk_type}: {count} chunks")

        return chunks

    def load_and_process_document(self, file_path: str) -> tuple:
        file_hash = self.get_file_hash(file_path)
        cache_file = os.path.join(self.cache_dir, f"general_rag_{file_hash}.pkl")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)

                if (cached_data['file_hash'] == file_hash and
                    os.path.exists(file_path) and
                    cached_data['timestamp'] == os.path.getmtime(file_path)):

                    print("Loading from cache...")
                    chunks = cached_data['chunks']
                    chunk_embeddings = cached_data['chunk_embeddings']
                    chunk_metadata = cached_data['chunk_metadata']

                    print(f"Loaded {len(chunks)} cached chunks")
                    return chunks, chunk_embeddings, chunk_metadata

            except Exception as e:
                print(f"Cache loading failed: {e}")

        print("Processing document...")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Failed to read file: {e}")
            return None, None, None

        print(f"Document loaded: {len(lines)} lines")

        chunks_data = self.create_adaptive_chunks(lines)

        print("Creating embeddings...")
        chunks = []
        chunk_embeddings = []
        chunk_metadata = []

        for i, chunk_data in enumerate(chunks_data):
            if i % 20 == 0:
                print(f"  Processing chunk {i+1}/{len(chunks_data)}")

            content = chunk_data['content']
            embedding = self.embedding_service.get_embedding(content)

            if not embedding:
                print(f"Failed to get embedding for chunk {i+1}")
                return None, None, None

            chunks.append(content)
            chunk_embeddings.append(embedding)
            chunk_metadata.append(chunk_data)

        try:
            cache_data = {
                'file_hash': file_hash,
                'timestamp': os.path.getmtime(file_path),
                'chunks': chunks,
                'chunk_embeddings': chunk_embeddings,
                'chunk_metadata': chunk_metadata
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"Cached to: {cache_file}")

        except Exception as e:
            print(f"Failed to cache: {e}")

        return chunks, chunk_embeddings, chunk_metadata