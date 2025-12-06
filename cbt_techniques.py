# -*- coding: utf-8 -*-
"""
Модуль для работы с КПТ техниками и упражнениями
"""
from typing import Dict, List, Optional
from datetime import datetime

class CBTTechniques:
    """Класс для работы с когнитивно-поведенческими техниками"""
    
    def __init__(self):
        self.techniques = {
            "breathing_478": {
                "name": "Дыхание 4-7-8",
                "description": "Техника для быстрого снятия тревоги",
                "steps": [
                    "Вдохни на 4 счёта",
                    "Задержи дыхание на 7 счётов",
                    "Выдохни на 8 счётов",
                    "Повтори 3-4 раза"
                ],
                "duration": 3,
                "category": "breathing"
            },
            "breathing_square": {
                "name": "Дыхание по квадрату",
                "description": "Стабилизация дыхания через визуализацию",
                "steps": [
                    "Вдохни на 4 счёта",
                    "Задержи дыхание на 4 счёта",
                    "Выдохни на 4 счёта",
                    "Пауза на 4 счёта",
                    "Повтори 5-10 минут"
                ],
                "duration": 5,
                "category": "breathing"
            },
            "grounding_54321": {
                "name": "Заземление 5-4-3-2-1",
                "description": "Возвращение в настоящий момент",
                "steps": [
                    "Назови 5 предметов, которые видишь",
                    "Назови 4 звука, которые слышишь",
                    "Назови 3 ощущения, которых касаешься",
                    "Назови 2 запаха, которые чувствуешь",
                    "Назови 1 вкус во рту"
                ],
                "duration": 2,
                "category": "grounding"
            },
            "progressive_relaxation": {
                "name": "Прогрессивная мышечная релаксация",
                "description": "Снятие мышечного напряжения",
                "steps": [
                    "Напряги мышцы стоп на 5 секунд, затем расслабь на 30 секунд",
                    "Напряги мышцы голеней на 5 секунд, затем расслабь на 30 секунд",
                    "Напряги мышцы бедер на 5 секунд, затем расслабь на 30 секунд",
                    "Напряги мышцы живота на 5 секунд, затем расслабь на 30 секунд",
                    "Напряги мышцы рук на 5 секунд, затем расслабь на 30 секунд",
                    "Напряги мышцы плеч на 5 секунд, затем расслабь на 30 секунд",
                    "Напряги мышцы лица на 5 секунд, затем расслабь на 30 секунд"
                ],
                "duration": 15,
                "category": "relaxation"
            },
            "mindful_breathing": {
                "name": "Осознанное дыхание",
                "description": "Медитация на дыхании",
                "steps": [
                    "Сядь удобно и закрой глаза",
                    "Сосредоточься на дыхании",
                    "Не пытайся изменить дыхание",
                    "Просто наблюдай за вдохами и выдохами",
                    "Если мысли отвлекают, мягко верни внимание к дыханию"
                ],
                "duration": 10,
                "category": "mindfulness"
            },
            "thought_stopping": {
                "name": "Остановка мысли",
                "description": "Прерывание негативных мыслей",
                "steps": [
                    "Заметь негативную мысль",
                    "Мысленно скажи 'Стоп!'",
                    "Можно щелкнуть резинкой на запястье",
                    "Переключись на другую деятельность",
                    "Повтори при необходимости"
                ],
                "duration": 1,
                "category": "cognitive"
            }
        }
        
        self.cognitive_distortions = {
            "all_or_nothing": {
                "name": "Мышление 'всё или ничего'",
                "description": "Восприятие вещей в крайностях, без полутонов",
                "example": "Если я не идеален, значит я полный неудачник"
            },
            "overgeneralization": {
                "name": "Сверхобобщение",
                "description": "Делание общих выводов на основе одного случая",
                "example": "Я всегда всё порчу"
            },
            "mental_filter": {
                "name": "Ментальный фильтр",
                "description": "Фокусирование только на негативных аспектах",
                "example": "Всё было плохо, несмотря на хорошие моменты"
            },
            "mind_reading": {
                "name": "Чтение мыслей",
                "description": "Предположение о том, что думают другие",
                "example": "Они все думают, что я глупый"
            },
            "catastrophizing": {
                "name": "Катастрофизация",
                "description": "Преувеличение негативных последствий",
                "example": "Если я опоздаю, меня уволят и я останусь без денег"
            },
            "emotional_reasoning": {
                "name": "Эмоциональное обоснование",
                "description": "Принятие эмоций за факты",
                "example": "Я чувствую себя неудачником, значит я неудачник"
            },
            "labeling": {
                "name": "Навешивание ярлыков",
                "description": "Присвоение негативных ярлыков себе или другим",
                "example": "Я идиот"
            },
            "should_statements": {
                "name": "Долженствования",
                "description": "Жесткие правила о том, как должны быть вещи",
                "example": "Я должен всегда быть идеальным"
            },
            "personalization": {
                "name": "Персонализация",
                "description": "Принятие на себя ответственности за события, не связанные с вами",
                "example": "Это моя вина, что команда проиграла"
            },
            "fortune_telling": {
                "name": "Предсказание будущего",
                "description": "Негативные предсказания о будущем",
                "example": "Я никогда не найду работу"
            }
        }

    def get_technique(self, technique_id: str) -> Optional[Dict]:
        """Получение информации о технике"""
        return self.techniques.get(technique_id)

    def get_techniques_by_category(self, category: str) -> List[Dict]:
        """Получение техник по категории"""
        return [
            {**tech, "id": tech_id} 
            for tech_id, tech in self.techniques.items() 
            if tech["category"] == category
        ]

    def get_breathing_techniques(self) -> List[Dict]:
        """Получение дыхательных техник"""
        return self.get_techniques_by_category("breathing")

    def get_grounding_techniques(self) -> List[Dict]:
        """Получение техник заземления"""
        return self.get_techniques_by_category("grounding")

    def get_relaxation_techniques(self) -> List[Dict]:
        """Получение техник релаксации"""
        return self.get_techniques_by_category("relaxation")

    def get_mindfulness_techniques(self) -> List[Dict]:
        """Получение техник осознанности"""
        return self.get_techniques_by_category("mindfulness")

    def get_cognitive_techniques(self) -> List[Dict]:
        """Получение когнитивных техник"""
        return self.get_techniques_by_category("cognitive")

    def get_cognitive_distortion(self, distortion_id: str) -> Optional[Dict]:
        """Получение информации о когнитивном искажении"""
        return self.cognitive_distortions.get(distortion_id)

    def identify_cognitive_distortion(self, thought: str) -> Optional[str]:
        """Попытка идентифицировать когнитивное искажение в мысли"""
        thought_lower = thought.lower()
        
        # Простые ключевые слова для идентификации
        patterns = {
            "all_or_nothing": ["всегда", "никогда", "все", "ничего", "идеально", "полный"],
            "overgeneralization": ["всегда", "никогда", "все", "каждый раз"],
            "mental_filter": ["только", "лишь", "всё плохо", "ничего хорошего"],
            "mind_reading": ["думают", "считают", "знают", "понимают"],
            "catastrophizing": ["ужасно", "катастрофа", "конец", "всё пропало"],
            "emotional_reasoning": ["чувствую", "кажется", "ощущаю"],
            "labeling": ["идиот", "дурак", "неудачник", "плохой"],
            "should_statements": ["должен", "обязан", "надо", "нельзя"],
            "personalization": ["моя вина", "из-за меня", "я виноват"],
            "fortune_telling": ["никогда", "всегда будет", "не получится", "не смогу"]
        }
        
        for distortion_id, keywords in patterns.items():
            if any(keyword in thought_lower for keyword in keywords):
                return distortion_id
        
        return None

    def get_challenge_questions(self, distortion_id: str) -> List[str]:
        """Получение вопросов для вызова когнитивного искажения"""
        challenge_questions = {
            "all_or_nothing": [
                "Есть ли серые зоны в этой ситуации?",
                "Можно ли найти исключения из этого правила?",
                "Что бы ты сказал другу в такой ситуации?"
            ],
            "overgeneralization": [
                "Сколько раз это действительно происходило?",
                "Есть ли случаи, когда это было не так?",
                "Насколько репрезентативен этот случай?"
            ],
            "mental_filter": [
                "Что хорошего произошло сегодня?",
                "Какие позитивные аспекты я упускаю?",
                "Что бы заметил оптимист в этой ситуации?"
            ],
            "mind_reading": [
                "Какие у меня есть доказательства этого?",
                "Могу ли я знать наверняка, что думают другие?",
                "Есть ли альтернативные объяснения их поведения?"
            ],
            "catastrophizing": [
                "Какова реальная вероятность худшего исхода?",
                "Что самое плохое может случиться?",
                "Как я справлялся с подобными ситуациями раньше?"
            ],
            "emotional_reasoning": [
                "Подтверждают ли факты мои чувства?",
                "Могут ли мои эмоции быть неточными?",
                "Что бы сказал объективный наблюдатель?"
            ],
            "labeling": [
                "Описывает ли это меня полностью?",
                "Какие мои качества не учитывает этот ярлык?",
                "Как бы я описал друга в такой ситуации?"
            ],
            "should_statements": [
                "Откуда взялось это правило?",
                "Кто сказал, что так должно быть?",
                "Что произойдет, если я не буду следовать этому правилу?"
            ],
            "personalization": [
                "Какие факторы вне моего контроля повлияли на это?",
                "Какую роль сыграли другие люди?",
                "Что бы сказал нейтральный наблюдатель?"
            ],
            "fortune_telling": [
                "Какие у меня есть доказательства этого предсказания?",
                "Как часто мои негативные предсказания сбывались?",
                "Есть ли альтернативные сценарии развития событий?"
            ]
        }
        
        return challenge_questions.get(distortion_id, [
            "Какие у меня есть доказательства этой мысли?",
            "Есть ли альтернативные объяснения?",
            "Что бы я сказал другу в такой ситуации?",
            "Насколько реалистична эта мысль?"
        ])

    def suggest_technique_for_anxiety_level(self, anxiety_level: int) -> str:
        """Предложение техники на основе уровня тревоги"""
        if anxiety_level >= 8:
            return "breathing_478"  # Самая быстрая техника
        elif anxiety_level >= 6:
            return "grounding_54321"  # Заземление
        elif anxiety_level >= 4:
            return "breathing_square"  # Стабилизация
        else:
            return "mindful_breathing"  # Профилактика

    def get_technique_instructions(self, technique_id: str) -> str:
        """Получение инструкций для выполнения техники"""
        technique = self.get_technique(technique_id)
        if not technique:
            return "Техника не найдена"
        
        instructions = f"<b>{technique['name']}</b>\n\n"
        instructions += f"{technique['description']}\n\n"
        instructions += "<b>Пошаговые инструкции:</b>\n"
        
        for i, step in enumerate(technique['steps'], 1):
            instructions += f"{i}. {step}\n"
        
        instructions += f"\n<b>Рекомендуемая продолжительность:</b> {technique['duration']} минут"
        
        return instructions











