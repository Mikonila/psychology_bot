import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class UserMemory:
    def __init__(self, memory_file: str = "user_memories.json"):
        """Инициализация системы памяти пользователей"""
        self.memory_file = memory_file
        self.memories = self.load_memories()
    
    def load_memories(self) -> Dict:
        """Загрузка памяти из файла"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            return {}
        except Exception as e:
            print(f"Ошибка при загрузке памяти: {e}")
            return {}
    
    def save_memories(self) -> bool:
        """Сохранение памяти в файл"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as file:
                json.dump(self.memories, file, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении памяти: {e}")
            return False
    
    def get_user_memory(self, user_id: int) -> Dict:
        """Получение памяти конкретного пользователя"""
        if str(user_id) not in self.memories:
            self.memories[str(user_id)] = {
                "user_info": {},
                "conversation_history": [],
                "anxiety_levels": [],
                "preferences": {},
                "progress": {},
                "last_interaction": None
            }
        return self.memories[str(user_id)]
    
    def add_message_to_history(self, user_id: int, role: str, content: str):
        """Добавление сообщения в историю диалога"""
        user_memory = self.get_user_memory(user_id)
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        user_memory["conversation_history"].append(message)
        
        # Ограничиваем историю последними 20 сообщениями
        if len(user_memory["conversation_history"]) > 20:
            user_memory["conversation_history"] = user_memory["conversation_history"][-20:]
        
        user_memory["last_interaction"] = datetime.now().isoformat()
        self.save_memories()
    
    def update_user_info(self, user_id: int, info: Dict):
        """Обновление информации о пользователе"""
        user_memory = self.get_user_memory(user_id)
        user_memory["user_info"].update(info)
        self.save_memories()
    
    def record_anxiety_level(self, user_id: int, level: int, notes: str = ""):
        """Запись уровня тревожности"""
        user_memory = self.get_user_memory(user_id)
        anxiety_record = {
            "level": level,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        user_memory["anxiety_levels"].append(anxiety_record)
        
        # Ограничиваем историю последними 30 записями
        if len(user_memory["anxiety_levels"]) > 30:
            user_memory["anxiety_levels"] = user_memory["anxiety_levels"][-30:]
        
        self.save_memories()
    
    def update_preferences(self, user_id: int, preferences: Dict):
        """Обновление предпочтений пользователя"""
        user_memory = self.get_user_memory(user_id)
        user_memory["preferences"].update(preferences)
        self.save_memories()
    
    def update_progress(self, user_id: int, progress_data: Dict):
        """Обновление прогресса пользователя"""
        user_memory = self.get_user_memory(user_id)
        user_memory["progress"].update(progress_data)
        self.save_memories()
    
    def get_conversation_context(self, user_id: int, max_messages: int = 10) -> str:
        """Получение контекста диалога для GPT"""
        user_memory = self.get_user_memory(user_id)
        history = user_memory["conversation_history"][-max_messages:]
        
        context_parts = []
        
        # Добавляем информацию о пользователе
        if user_memory["user_info"]:
            context_parts.append("Информация о пользователе:")
            for key, value in user_memory["user_info"].items():
                context_parts.append(f"- {key}: {value}")
            context_parts.append("")
        
        # Добавляем последние уровни тревожности
        if user_memory["anxiety_levels"]:
            recent_levels = user_memory["anxiety_levels"][-3:]
            context_parts.append("Последние уровни тревожности:")
            for record in recent_levels:
                context_parts.append(f"- {record['level']}/10 ({record['timestamp'][:10]})")
                if record['notes']:
                    context_parts.append(f"  Заметки: {record['notes']}")
            context_parts.append("")
        
        # Добавляем историю диалога
        if history:
            context_parts.append("История диалога:")
            for message in history:
                role_name = "Пользователь" if message["role"] == "user" else "Бот"
                context_parts.append(f"{role_name}: {message['content']}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_user_summary(self, user_id: int) -> str:
        """Получение краткого резюме о пользователе"""
        user_memory = self.get_user_memory(user_id)
        
        summary_parts = []
        
        # Основная информация
        if user_memory["user_info"]:
            summary_parts.append("Информация о пользователе:")
            for key, value in user_memory["user_info"].items():
                summary_parts.append(f"- {key}: {value}")
        
        # Средний уровень тревожности
        if user_memory["anxiety_levels"]:
            recent_levels = [record["level"] for record in user_memory["anxiety_levels"][-7:]]
            avg_level = sum(recent_levels) / len(recent_levels)
            summary_parts.append(f"- Средний уровень тревожности за последнюю неделю: {avg_level:.1f}/10")
        
        # Ключевые события из истории разговоров (последние 10 сообщений)
        if user_memory["conversation_history"]:
            recent_messages = user_memory["conversation_history"][-10:]
            key_events = []
            for msg in recent_messages:
                if msg["role"] == "user":
                    content = msg["content"].lower()
                    # Ищем ключевые события
                    if any(word in content for word in ["работа", "уволили", "увольнение", "начальник", "коллеги"]):
                        key_events.append(f"Проблемы на работе: {msg['content']}")
                    elif any(word in content for word in ["семья", "родители", "мама", "папа", "родственники"]):
                        key_events.append(f"Семейные отношения: {msg['content']}")
                    elif any(word in content for word in ["экзамен", "учеба", "университет", "институт", "сессия"]):
                        key_events.append(f"Учеба: {msg['content']}")
                    elif any(word in content for word in ["здоровье", "болею", "врач", "больница", "лекарства"]):
                        key_events.append(f"Здоровье: {msg['content']}")
                    elif any(word in content for word in ["друзья", "подруги", "встреча", "вечеринка", "отдых"]):
                        key_events.append(f"Социальная жизнь: {msg['content']}")
            
            if key_events:
                summary_parts.append("Ключевые события из последних разговоров:")
                for event in key_events[-5:]:  # Последние 5 событий
                    summary_parts.append(f"- {event}")
        
        # Предпочтения
        if user_memory["preferences"]:
            summary_parts.append("Предпочтения:")
            for key, value in user_memory["preferences"].items():
                summary_parts.append(f"- {key}: {value}")
        
        # Прогресс
        if user_memory["progress"]:
            summary_parts.append("Прогресс:")
            for key, value in user_memory["progress"].items():
                summary_parts.append(f"- {key}: {value}")
        
        return "\n".join(summary_parts) if summary_parts else "Информация о пользователе отсутствует"
    
    def clear_user_memory(self, user_id: int):
        """Очистка памяти пользователя"""
        if str(user_id) in self.memories:
            del self.memories[str(user_id)]
            self.save_memories()
    
    def get_all_users(self) -> List[int]:
        """Получение списка всех пользователей"""
        return [int(user_id) for user_id in self.memories.keys()]
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Получение статистики пользователя"""
        user_memory = self.get_user_memory(user_id)
        
        stats = {
            "total_messages": len(user_memory["conversation_history"]),
            "anxiety_records": len(user_memory["anxiety_levels"]),
            "last_interaction": user_memory["last_interaction"],
            "user_info_fields": len(user_memory["user_info"]),
            "preferences_count": len(user_memory["preferences"]),
            "progress_fields": len(user_memory["progress"])
        }
        
        # Средний уровень тревожности
        if user_memory["anxiety_levels"]:
            recent_levels = [record["level"] for record in user_memory["anxiety_levels"][-7:]]
            stats["avg_anxiety_week"] = sum(recent_levels) / len(recent_levels)
        
        return stats







