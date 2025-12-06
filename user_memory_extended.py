# -*- coding: utf-8 -*-
"""
Расширенные методы для работы с пользовательской памятью
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List

class UserMemoryExtended:
    """Расширенный класс для работы с пользовательской памятью"""
    
    def __init__(self, user_memory_instance):
        self.user_memory = user_memory_instance
    
    def _ensure_key_exists(self, user_memory: Dict, key_path: str, default_value=None):
        """Обеспечивает существование ключа в словаре"""
        keys = key_path.split('.')
        current = user_memory
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        if keys[-1] not in current:
            current[keys[-1]] = default_value if default_value is not None else []
    
    # Методы для работы с КПТ техниками
    def record_cbt_exercise(self, user_id: int, exercise_data: Dict):
        """Запись выполненного КПТ упражнения"""
        user_memory = self.user_memory.get_user_memory(user_id)
        self._ensure_key_exists(user_memory, "cbt_techniques.completed_exercises")
        
        exercise_record = {
            "technique": exercise_data.get("technique", ""),
            "duration": exercise_data.get("duration", 0),
            "effectiveness": exercise_data.get("effectiveness", 0),
            "notes": exercise_data.get("notes", ""),
            "timestamp": datetime.now().isoformat()
        }
        user_memory["cbt_techniques"]["completed_exercises"].append(exercise_record)
        self.user_memory.save_memories()

    def update_technique_effectiveness(self, user_id: int, technique: str, effectiveness: int):
        """Обновление эффективности техники"""
        user_memory = self.user_memory.get_user_memory(user_id)
        self._ensure_key_exists(user_memory, "cbt_techniques.technique_effectiveness", {})
        
        if technique not in user_memory["cbt_techniques"]["technique_effectiveness"]:
            user_memory["cbt_techniques"]["technique_effectiveness"][technique] = []
        user_memory["cbt_techniques"]["technique_effectiveness"][technique].append({
            "effectiveness": effectiveness,
            "timestamp": datetime.now().isoformat()
        })
        self.user_memory.save_memories()

    # Методы для работы с ежедневными оценками
    def add_daily_assessment(self, user_id: int, assessment_data: Dict):
        """Добавление ежедневной оценки"""
        user_memory = self.user_memory.get_user_memory(user_id)
        
        if "mood_score" in assessment_data:
            self._ensure_key_exists(user_memory, "daily_assessments.mood_scores")
            user_memory["daily_assessments"]["mood_scores"].append({
                "score": assessment_data["mood_score"],
                "timestamp": datetime.now().isoformat()
            })
        
        if "resource_score" in assessment_data:
            self._ensure_key_exists(user_memory, "daily_assessments.resource_scores")
            user_memory["daily_assessments"]["resource_scores"].append({
                "score": assessment_data["resource_score"],
                "timestamp": datetime.now().isoformat()
            })
        
        if "sleep_quality" in assessment_data:
            self._ensure_key_exists(user_memory, "daily_assessments.sleep_quality")
            user_memory["daily_assessments"]["sleep_quality"].append({
                "quality": assessment_data["sleep_quality"],
                "timestamp": datetime.now().isoformat()
            })
        
        if "stress_factors" in assessment_data:
            self._ensure_key_exists(user_memory, "daily_assessments.stress_factors")
            user_memory["daily_assessments"]["stress_factors"].append({
                "factors": assessment_data["stress_factors"],
                "timestamp": datetime.now().isoformat()
            })
        
        if "helpful_actions" in assessment_data:
            self._ensure_key_exists(user_memory, "daily_assessments.helpful_actions")
            user_memory["daily_assessments"]["helpful_actions"].append({
                "actions": assessment_data["helpful_actions"],
                "timestamp": datetime.now().isoformat()
            })
        
        self.user_memory.save_memories()

    # Методы для работы с когнитивными искажениями
    def add_cognitive_pattern(self, user_id: int, pattern_data: Dict):
        """Добавление выявленного когнитивного паттерна"""
        user_memory = self.user_memory.get_user_memory(user_id)
        self._ensure_key_exists(user_memory, "cognitive_distortions.identified_patterns")
        
        pattern_entry = {
            "distortion_type": pattern_data.get("distortion_type", ""),
            "example_thought": pattern_data.get("example_thought", ""),
            "challenge_strategy": pattern_data.get("challenge_strategy", ""),
            "timestamp": datetime.now().isoformat()
        }
        user_memory["cognitive_distortions"]["identified_patterns"].append(pattern_entry)
        self.user_memory.save_memories()

    def add_cognitive_challenge(self, user_id: int, challenge_data: Dict):
        """Добавление вызова негативной мысли"""
        user_memory = self.user_memory.get_user_memory(user_id)
        self._ensure_key_exists(user_memory, "cognitive_distortions.challenges")
        
        challenge_entry = {
            "original_thought": challenge_data.get("original_thought", ""),
            "challenge_questions": challenge_data.get("challenge_questions", []),
            "rational_response": challenge_data.get("rational_response", ""),
            "belief_change": challenge_data.get("belief_change", 0),
            "timestamp": datetime.now().isoformat()
        }
        user_memory["cognitive_distortions"]["challenges"].append(challenge_entry)
        self.user_memory.save_memories()

    # Методы для работы с целями
    def add_goal(self, user_id: int, goal_data: Dict):
        """Добавление новой цели"""
        user_memory = self.user_memory.get_user_memory(user_id)
        self._ensure_key_exists(user_memory, "goals.current_goals")
        
        goal_entry = {
            "goal": goal_data.get("goal", ""),
            "category": goal_data.get("category", ""),
            "target_date": goal_data.get("target_date", ""),
            "priority": goal_data.get("priority", 1),
            "progress": 0,
            "created_at": datetime.now().isoformat()
        }
        user_memory["goals"]["current_goals"].append(goal_entry)
        self.user_memory.save_memories()

    def update_goal_progress(self, user_id: int, goal_index: int, progress: int, notes: str = ""):
        """Обновление прогресса по цели"""
        user_memory = self.user_memory.get_user_memory(user_id)
        self._ensure_key_exists(user_memory, "goals.current_goals")
        
        if 0 <= goal_index < len(user_memory["goals"]["current_goals"]):
            user_memory["goals"]["current_goals"][goal_index]["progress"] = progress
            if notes:
                if "progress_notes" not in user_memory["goals"]["current_goals"][goal_index]:
                    user_memory["goals"]["current_goals"][goal_index]["progress_notes"] = []
                user_memory["goals"]["current_goals"][goal_index]["progress_notes"].append({
                    "note": notes,
                    "timestamp": datetime.now().isoformat()
                })
            self.user_memory.save_memories()

    def complete_goal(self, user_id: int, goal_index: int):
        """Завершение цели"""
        user_memory = self.user_memory.get_user_memory(user_id)
        self._ensure_key_exists(user_memory, "goals.current_goals")
        self._ensure_key_exists(user_memory, "goals.achieved_goals")
        
        if 0 <= goal_index < len(user_memory["goals"]["current_goals"]):
            completed_goal = user_memory["goals"]["current_goals"].pop(goal_index)
            completed_goal["completed_at"] = datetime.now().isoformat()
            user_memory["goals"]["achieved_goals"].append(completed_goal)
            self.user_memory.save_memories()

    # Методы для получения аналитики
    def get_emotion_analytics(self, user_id: int, days: int = 30) -> Dict:
        """Получение аналитики по эмоциям"""
        user_memory = self.user_memory.get_user_memory(user_id)
        
        # Проверяем существование ключей
        if "emotion_tracker" not in user_memory or "emotions" not in user_memory["emotion_tracker"]:
            return {
                "total_entries": 0,
                "emotion_distribution": {},
                "average_intensity": 0,
                "recent_emotions": [],
                "intensity_trend": "stable"
            }
        
        emotions = user_memory["emotion_tracker"]["emotions"]
        
        # Фильтруем записи за последние N дней
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_emotions = [
            e for e in emotions 
            if datetime.fromisoformat(e["timestamp"]) >= cutoff_date
        ]
        
        if not recent_emotions:
            return {"error": "Недостаточно данных"}
        
        # Анализируем эффективность техник
        technique_effectiveness = {}
        for emotion in recent_emotions:
            technique = emotion["technique_used"]
            if technique:
                if technique not in technique_effectiveness:
                    technique_effectiveness[technique] = []
                improvement = emotion["intensity_before"] - emotion["intensity_after"]
                technique_effectiveness[technique].append(improvement)
        
        # Вычисляем среднюю эффективность
        avg_effectiveness = {}
        for technique, improvements in technique_effectiveness.items():
            avg_effectiveness[technique] = sum(improvements) / len(improvements)
        
        return {
            "total_entries": len(recent_emotions),
            "technique_effectiveness": avg_effectiveness,
            "most_common_emotions": self._get_most_common_emotions(recent_emotions),
            "average_improvement": sum(e["intensity_before"] - e["intensity_after"] for e in recent_emotions) / len(recent_emotions)
        }

    def get_mood_trends(self, user_id: int, days: int = 30) -> Dict:
        """Получение трендов настроения"""
        user_memory = self.user_memory.get_user_memory(user_id)
        
        # Проверяем существование ключей
        if "daily_assessments" not in user_memory:
            return {
                "mood_trend": "stable",
                "resource_trend": "stable",
                "average_mood": 5,
                "average_resources": 5,
                "mood_data": [],
                "resource_data": []
            }
        
        mood_scores = user_memory["daily_assessments"].get("mood_scores", [])
        resource_scores = user_memory["daily_assessments"].get("resource_scores", [])
        
        # Фильтруем записи за последние N дней
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_moods = [
            m for m in mood_scores 
            if datetime.fromisoformat(m["timestamp"]) >= cutoff_date
        ]
        recent_resources = [
            r for r in resource_scores 
            if datetime.fromisoformat(r["timestamp"]) >= cutoff_date
        ]
        
        if not recent_moods:
            return {"error": "Недостаточно данных о настроении"}
        
        mood_values = [m["score"] for m in recent_moods]
        resource_values = [r["score"] for r in recent_resources] if recent_resources else []
        
        return {
            "mood_trend": self._calculate_trend(mood_values),
            "resource_trend": self._calculate_trend(resource_values) if resource_values else "Недостаточно данных",
            "average_mood": sum(mood_values) / len(mood_values),
            "average_resource": sum(resource_values) / len(resource_values) if resource_values else None,
            "mood_volatility": self._calculate_volatility(mood_values),
            "data_points": len(mood_values)
        }

    def _get_most_common_emotions(self, emotions: List[Dict]) -> List[Dict]:
        """Получение наиболее частых эмоций"""
        emotion_counts = {}
        for emotion in emotions:
            emo = emotion["emotion"]
            emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
        
        return sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    def _calculate_trend(self, values: List[float]) -> str:
        """Вычисление тренда значений"""
        if len(values) < 2:
            return "Недостаточно данных"
        
        # Простая линейная регрессия
        n = len(values)
        x = list(range(n))
        y = values
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "Стабильно"
        
        slope = numerator / denominator
        
        if slope > 0.1:
            return "Растет"
        elif slope < -0.1:
            return "Снижается"
        else:
            return "Стабильно"

    def _calculate_volatility(self, values: List[float]) -> float:
        """Вычисление волатильности значений"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
