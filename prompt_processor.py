import json
import re
from typing import List, Dict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import tiktoken
from openai import OpenAI
import logging


class PromptProcessor:
    def __init__(self, openai_api_key: str):
        """Инициализация процессора промптов"""
        self.client = OpenAI(api_key=openai_api_key)
        self.encoding = tiktoken.get_encoding("cl100k_base")  # Для GPT-4 / GPT-3.5
        self.chunks: List[Dict] = []
        self.embeddings: List[List[float]] = []

    def load_prompt_from_file(self, file_path: str = "prompt.txt") -> str:
        """Загрузка промпта из файла"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            print(f"Файл {file_path} не найден")
            return ""

    def _split_section_by_tokens(
        self, text: str, start_chunk_id: int, max_tokens: int, overlap: int
    ) -> List[Dict]:
        """Режем одну секцию по токенам с перекрытием, если она длиннее лимита."""
        chunks: List[Dict] = []
        tokens = self.encoding.encode(text)
        i = 0
        chunk_id = start_chunk_id
        while i < len(tokens):
            window = tokens[i : i + max_tokens]
            chunk_text = self.encoding.decode(window)
            lines = chunk_text.split("\n")
            title = lines[0].strip() if lines else f"Чанк {chunk_id}"
            chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text,
                    "title": title if title.startswith("#") else f"Чанк {chunk_id}",
                    "start_token": i,
                    "end_token": i + len(window),
                    "tokens_count": len(window),
                }
            )
            chunk_id += 1
            if len(tokens) <= max_tokens:
                break
            i += max_tokens - overlap
        return chunks

    def split_into_chunks(
        self, text: str, max_tokens: int = 1000, overlap: int = 100
    ) -> List[Dict]:
        """Разбиение текста по Markdown-заголовкам; длинные секции режем по токенам с перекрытием."""
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        headers = list(header_pattern.finditer(text))

        chunks: List[Dict] = []
        chunk_id = 0

        if headers:
            sections: List[Dict] = []
            for idx, match in enumerate(headers):
                start_idx = match.start()
                end_idx = (
                    headers[idx + 1].start() if idx + 1 < len(headers) else len(text)
                )
                section_text = text[start_idx:end_idx]
                title_text = match.group(2).strip()
                sections.append({"title": title_text, "text": section_text})

            for section in sections:
                section_tokens = self.encoding.encode(section["text"])
                if len(section_tokens) <= max_tokens:
                    chunks.append(
                        {
                            "id": chunk_id,
                            "text": section["text"],
                            "title": section["title"],
                            "start_token": 0,
                            "end_token": len(section_tokens),
                            "tokens_count": len(section_tokens),
                        }
                    )
                    chunk_id += 1
                else:
                    sub_chunks = self._split_section_by_tokens(
                        section["text"], chunk_id, max_tokens, overlap
                    )
                    for sc in sub_chunks:
                        sc["title"] = section["title"]
                        chunks.append(sc)
                        chunk_id = sc["id"] + 1
        else:
            fallback_chunks = self._split_section_by_tokens(text, chunk_id, max_tokens, overlap)
            for fc in fallback_chunks:
                fc["title"] = (
                    fc["title"] if fc["title"].startswith("#") else f"Чанк {fc['id']}"
                )
                chunks.append(fc)

        return chunks

    def create_embeddings_for_chunks(self, chunks: List[Dict]) -> List[List[float]]:
        """Создание эмбеддингов для чанков"""
        embeddings = []
        for chunk in chunks:
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-ada-002", input=chunk["text"]
                )
                embedding = response.data[0].embedding
                embeddings.append(embedding)
                print(f"Создан эмбеддинг для чанка {chunk['id']}: {chunk['title']}")
            except Exception as e:
                print(f"Ошибка при создании эмбеддинга для чанка {chunk['id']}: {e}")
                embeddings.append([0.0] * 1536)  # fallback
        return embeddings

    def find_relevant_chunks(self, query: str, top_k: int = 3) -> List[Dict]:
        """Поиск релевантных чанков для запроса"""
        if not self.embeddings:
            print("Эмбеддинги не загружены. Сначала вызовите process_prompt()")
            return []

        if not query.strip():
            print("Пустой запрос для поиска эмбеддингов")
            return []

        try:
            query_response = self.client.embeddings.create(
                model="text-embedding-ada-002", input=query
            )
            query_embedding = query_response.data[0].embedding
        except Exception as e:
            print(f"Ошибка при создании эмбеддинга для запроса: {e}")
            return []

        similarities = []
        for i, chunk_embedding in enumerate(self.embeddings):
            similarity = cosine_similarity([query_embedding], [chunk_embedding])[0][0]
            similarities.append((similarity, i))

        similarities.sort(reverse=True)
        relevant_chunks = []
        for similarity, chunk_idx in similarities[:top_k]:
            chunk_data = self.chunks[chunk_idx].copy()
            chunk_data["similarity"] = similarity
            relevant_chunks.append(chunk_data)
        return relevant_chunks

    def process_prompt(self, file_path: str = "prompt.txt") -> bool:
        """Полная обработка промпта"""
        print("Начинаю обработку промпта...")
        prompt_text = self.load_prompt_from_file(file_path)
        if not prompt_text:
            return False
        print(f"Загружен промпт размером {len(prompt_text)} символов")

        self.chunks = self.split_into_chunks(prompt_text)
        print(f"Создано {len(self.chunks)} чанков")

        self.embeddings = self.create_embeddings_for_chunks(self.chunks)
        print(f"Создано {len(self.embeddings)} эмбеддингов")

        return True

    def get_context_for_query(self, query: str, max_context_length: int = 3000) -> str:
        """Контекст по релевантным чанкам"""
        relevant_chunks = self.find_relevant_chunks(query)
        if not relevant_chunks:
            return "Контекст не найден"

        context_parts = []
        current_length = 0
        for chunk in relevant_chunks:
            chunk_text = chunk["text"]
            if current_length + len(chunk_text) <= max_context_length:
                context_parts.append(f"=== {chunk['title']} ===\n{chunk_text}")
                current_length += len(chunk_text)
            else:
                break
        return "\n\n".join(context_parts)

    def save_processed_data(self, file_path: str = "processed_prompt.json"):
        """Сохраняем чанки и эмбеддинги"""
        data = {"chunks": self.chunks, "embeddings": self.embeddings}
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            print(f"Данные сохранены в {file_path}")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении данных: {e}")
            return False

    def load_processed_data(self, file_path: str = "processed_prompt.json") -> bool:
        """Загружаем чанки и эмбеддинги"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.chunks = data["chunks"]
            self.embeddings = data["embeddings"]
            logging.info("📂 Начинаю загрузку эмбеддингов...")

            print(
                f"Загружено {len(self.chunks)} чанков и {len(self.embeddings)} эмбеддингов"
            )
            return True
        except FileNotFoundError:
            print(f"Файл {file_path} не найден")
            return False
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return False

    def get_chunk_info(self) -> Dict:
        """Инфа о чанках"""
        if not self.chunks:
            return {"error": "Чанки не загружены"}
        total_tokens = sum(chunk["tokens_count"] for chunk in self.chunks)
        titles = [chunk["title"] for chunk in self.chunks]
        return {
            "total_chunks": len(self.chunks),
            "total_tokens": total_tokens,
            "chunk_titles": titles,
            "embeddings_loaded": len(self.embeddings) > 0,
        }


if __name__ == "__main__":
    processor = PromptProcessor(openai_api_key="ТВОЙ_API_KEY")

    if processor.process_prompt("prompt.txt"):
        processor.save_processed_data("processed_prompt.json")

    processor.load_processed_data("processed_prompt.json")

    query = "тревога"
    context = processor.get_context_for_query(query)
    print("Контекст для запроса:")
    print(context)
