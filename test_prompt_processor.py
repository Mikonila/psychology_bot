#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы PromptProcessor
"""

from prompt_processor import PromptProcessor
from config import OPENAI_API_KEY

def test_prompt_processor():
    """Тестирование процессора промптов"""
    
    print("🚀 Тестирование системы чанков и эмбеддингов")
    print("=" * 50)
    
    # Инициализация процессора
    processor = PromptProcessor(OPENAI_API_KEY)
    
    # Попытка загрузить существующие данные
    print("\n📂 Попытка загрузки существующих данных...")
    if processor.load_processed_data():
        print("✅ Данные успешно загружены")
    else:
        print("❌ Данные не найдены, обрабатываю промпт заново...")
        
        # Обработка промпта
        if processor.process_prompt():
            print("✅ Промпт успешно обработан")
            processor.save_processed_data()
        else:
            print("❌ Ошибка при обработке промпта")
            return
    
    # Информация о чанках
    print("\n📊 Информация о чанках:")
    info = processor.get_chunk_info()
    print(f"Всего чанков: {info['total_chunks']}")
    print(f"Всего токенов: {info['total_tokens']}")
    print(f"Эмбеддинги загружены: {info['embeddings_loaded']}")
    
    print("\n📝 Заголовки чанков:")
    for i, title in enumerate(info['chunk_titles'][:5]):  # Показываем первые 5
        print(f"  {i+1}. {title}")
    if len(info['chunk_titles']) > 5:
        print(f"  ... и еще {len(info['chunk_titles']) - 5} чанков")
    
    # Тестирование поиска релевантных чанков
    test_queries = [
        "Как помочь при тревоге?",
        "Техники дыхания",
        "Когнитивно-поведенческая терапия",
        "Что делать при панике?",
        "Как улучшить сон?"
    ]
    
    print("\n🔍 Тестирование поиска релевантных чанков:")
    for query in test_queries:
        print(f"\nЗапрос: '{query}'")
        relevant_chunks = processor.find_relevant_chunks(query, top_k=2)
        
        if relevant_chunks:
            for i, chunk in enumerate(relevant_chunks):
                similarity = chunk.get('similarity', 0)
                print(f"  {i+1}. {chunk['title']} (сходство: {similarity:.3f})")
        else:
            print("  ❌ Релевантные чанки не найдены")
    
    # Тестирование получения контекста
    print("\n📖 Тестирование получения контекста:")
    test_query = "Мне очень тревожно, что делать?"
    context = processor.get_context_for_query(test_query)
    
    print(f"Запрос: '{test_query}'")
    print(f"Длина контекста: {len(context)} символов")
    print("Первые 200 символов контекста:")
    print(context[:200] + "..." if len(context) > 200 else context)
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    test_prompt_processor()



















