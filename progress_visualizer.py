# -*- coding: utf-8 -*-
"""
Модуль для визуализации прогресса пользователя
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional
import os
import io
import base64

# Настройка matplotlib для русского языка и красивого шрифта
import matplotlib.font_manager as fm

# Пытаемся использовать Montserrat, если доступен
try:
    # Обновляем кэш шрифтов
    fm.fontManager.addfont('/usr/share/fonts/truetype/montserrat/Montserrat-Regular.ttf')
    fm.fontManager.addfont('/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf')
    
    # Проверяем доступность Montserrat
    montserrat_fonts = [f.name for f in fm.fontManager.ttflist if 'Montserrat' in f.name]
    if montserrat_fonts:
        plt.rcParams['font.family'] = 'Montserrat'
    else:
        # Fallback на системные шрифты
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
        print("Montserrat не найден, используется DejaVu Sans")
except Exception as e:
    plt.rcParams['font.family'] = 'DejaVu Sans'
    print(f"Ошибка при загрузке Montserrat: {e}")

plt.rcParams['axes.unicode_minus'] = False

class ProgressVisualizer:
    """Класс для создания графиков прогресса"""
    
    def __init__(self):
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#F18F01',
            'warning': '#C73E1D',
            'neutral': '#6C757D'
        }
    
    def create_mood_trend_chart(self, mood_data: List[Dict], days: int = 30) -> str:
        """Создание графика тренда настроения"""
        if not mood_data:
            return self._create_empty_chart("Недостаточно данных о настроении")
        
        # Фильтруем данные за последние N дней
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_data = [
            d for d in mood_data 
            if datetime.fromisoformat(d['timestamp']) >= cutoff_date
        ]
        
        if not recent_data:
            return self._create_empty_chart("Недостаточно данных за выбранный период")
        
        # Подготавливаем данные
        dates = [datetime.fromisoformat(d['timestamp']).date() for d in recent_data]
        scores = [d['score'] for d in recent_data]
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Основная линия настроения
        ax.plot(dates, scores, color=self.colors['primary'], linewidth=2, marker='o', markersize=4)
        
        # Линия тренда
        if len(scores) > 1:
            x_numeric = np.arange(len(scores))
            z = np.polyfit(x_numeric, scores, 1)
            p = np.poly1d(z)
            ax.plot(dates, p(x_numeric), color=self.colors['success'], linestyle='--', alpha=0.7, linewidth=2)
        
        # Настройка графика
        ax.set_title('Тренд настроения', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Дата', fontsize=12)
        ax.set_ylabel('Оценка настроения (1-10)', fontsize=12)
        ax.set_ylim(0, 10)
        ax.grid(True, alpha=0.3)
        
        # Простое форматирование дат без переполнения
        # Создаем список дат для отображения
        if len(dates) <= 7:
            # Показываем все даты
            display_dates = dates
        elif len(dates) <= 14:
            # Показываем каждую вторую дату
            display_dates = dates[::2]
        elif len(dates) <= 30:
            # Показываем каждую третью дату
            display_dates = dates[::3]
        else:
            # Показываем каждую пятую дату
            display_dates = dates[::5]
        
        # Устанавливаем тики и подписи
        ax.set_xticks(display_dates)
        ax.set_xticklabels([d.strftime('%d.%m') for d in display_dates], rotation=45, ha='right')
        
        # Настройка размера шрифта
        ax.tick_params(axis='x', which='major', labelsize=8)
        plt.tight_layout()
        
        # Добавляем среднее значение
        avg_score = np.mean(scores)
        ax.axhline(y=avg_score, color=self.colors['warning'], linestyle=':', alpha=0.7, 
                  label=f'Среднее: {avg_score:.1f}')
        ax.legend()
        
        # Сохраняем в base64
        return self._save_chart_to_base64(fig)
    
    def create_anxiety_progress_chart(self, anxiety_data: List[Dict], days: int = 30) -> str:
        """Создание графика прогресса тревожности"""
        if not anxiety_data:
            return self._create_empty_chart("Недостаточно данных о тревожности")
        
        # Фильтруем данные за последние N дней
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_data = [
            d for d in anxiety_data 
            if datetime.fromisoformat(d['timestamp']) >= cutoff_date
        ]
        
        if not recent_data:
            return self._create_empty_chart("Недостаточно данных за выбранный период")
        
        # Группируем по датам
        daily_data = {}
        for record in recent_data:
            date = datetime.fromisoformat(record['timestamp']).date()
            if date not in daily_data:
                daily_data[date] = []
            daily_data[date].append(record['level'])
        
        # Вычисляем средние значения по дням
        dates = sorted(daily_data.keys())
        avg_scores = [np.mean(daily_data[date]) for date in dates]
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Основная линия тревожности
        ax.plot(dates, avg_scores, color=self.colors['secondary'], linewidth=2, marker='o', markersize=4)
        
        # Зона комфорта (0-3)
        ax.axhspan(0, 3, alpha=0.2, color=self.colors['success'], label='Зона комфорта')
        
        # Зона умеренной тревоги (4-6)
        ax.axhspan(3, 6, alpha=0.2, color=self.colors['warning'], label='Умеренная тревога')
        
        # Зона высокой тревоги (7-10)
        ax.axhspan(6, 10, alpha=0.2, color=self.colors['warning'], label='Высокая тревога')
        
        # Настройка графика
        ax.set_title('Прогресс тревожности', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Дата', fontsize=12)
        ax.set_ylabel('Уровень тревожности (0-10)', fontsize=12)
        ax.set_ylim(0, 10)
        ax.grid(True, alpha=0.3)
        
        # Простое форматирование дат без переполнения
        # Создаем список дат для отображения
        if len(dates) <= 7:
            # Показываем все даты
            display_dates = dates
        elif len(dates) <= 14:
            # Показываем каждую вторую дату
            display_dates = dates[::2]
        elif len(dates) <= 30:
            # Показываем каждую третью дату
            display_dates = dates[::3]
        else:
            # Показываем каждую пятую дату
            display_dates = dates[::5]
        
        # Устанавливаем тики и подписи
        ax.set_xticks(display_dates)
        ax.set_xticklabels([d.strftime('%d.%m') for d in display_dates], rotation=45, ha='right')
        
        # Настройка размера шрифта
        ax.tick_params(axis='x', which='major', labelsize=8)
        plt.tight_layout()
        
        # Добавляем среднее значение
        avg_anxiety = np.mean(avg_scores)
        ax.axhline(y=avg_anxiety, color=self.colors['neutral'], linestyle='--', alpha=0.7, 
                  label=f'Среднее: {avg_anxiety:.1f}')
        ax.legend()
        
        # Сохраняем в base64
        return self._save_chart_to_base64(fig)
    
    def create_technique_effectiveness_chart(self, technique_data: Dict) -> str:
        """Создание графика эффективности техник"""
        if not technique_data:
            return self._create_empty_chart("Недостаточно данных об эффективности техник")
        
        # Подготавливаем данные
        techniques = list(technique_data.keys())
        effectiveness = list(technique_data.values())
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Создаем столбчатую диаграмму
        bars = ax.bar(techniques, effectiveness, color=self.colors['primary'], alpha=0.7)
        
        # Добавляем значения на столбцы
        for bar, value in zip(bars, effectiveness):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{value:.1f}', ha='center', va='bottom')
        
        # Настройка графика
        ax.set_title('Эффективность техник', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Техники', fontsize=12)
        ax.set_ylabel('Средняя эффективность', fontsize=12)
        ax.set_ylim(0, max(effectiveness) * 1.2 if effectiveness else 10)
        
        # Поворачиваем подписи техник
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Сохраняем в base64
        return self._save_chart_to_base64(fig)
    
    def create_weekly_summary_chart(self, weekly_data: Dict) -> str:
        """Создание недельной сводки"""
        if not weekly_data:
            return self._create_empty_chart("Недостаточно данных для недельной сводки")
        
        # Создаем график с несколькими подграфиками
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # График настроения
        if 'mood' in weekly_data:
            days = list(range(1, 8))
            mood_scores = weekly_data['mood']
            ax1.plot(days, mood_scores, color=self.colors['primary'], marker='o', linewidth=2)
            ax1.set_title('Настроение по дням недели', fontweight='bold')
            ax1.set_xlabel('День недели')
            ax1.set_ylabel('Оценка (1-10)')
            ax1.set_ylim(0, 10)
            ax1.grid(True, alpha=0.3)
        
        # График тревожности
        if 'anxiety' in weekly_data:
            days = list(range(1, 8))
            anxiety_scores = weekly_data['anxiety']
            ax2.plot(days, anxiety_scores, color=self.colors['secondary'], marker='o', linewidth=2)
            ax2.set_title('Тревожность по дням недели', fontweight='bold')
            ax2.set_xlabel('День недели')
            ax2.set_ylabel('Оценка (0-10)')
            ax2.set_ylim(0, 10)
            ax2.grid(True, alpha=0.3)
        
        # График сна
        if 'sleep' in weekly_data:
            days = list(range(1, 8))
            sleep_scores = weekly_data['sleep']
            ax3.bar(days, sleep_scores, color=self.colors['success'], alpha=0.7)
            ax3.set_title('Качество сна', fontweight='bold')
            ax3.set_xlabel('День недели')
            ax3.set_ylabel('Качество (1-10)')
            ax3.set_ylim(0, 10)
            ax3.grid(True, alpha=0.3)
        
        # Круговая диаграмма активности
        if 'activities' in weekly_data:
            activities = weekly_data['activities']
            labels = list(activities.keys())
            sizes = list(activities.values())
            colors = [self.colors['primary'], self.colors['secondary'], 
                     self.colors['success'], self.colors['warning']]
            
            ax4.pie(sizes, labels=labels, colors=colors[:len(labels)], autopct='%1.1f%%', startangle=90)
            ax4.set_title('Распределение активности', fontweight='bold')
        
        plt.tight_layout()
        
        # Сохраняем в base64
        return self._save_chart_to_base64(fig)
    
    def _create_empty_chart(self, message: str) -> str:
        """Создание пустого графика с сообщением"""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=14, 
                transform=ax.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return self._save_chart_to_base64(fig)
    
    def _save_chart_to_base64(self, fig) -> str:
        """Сохранение графика в base64"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return image_base64
    
    def create_progress_summary(self, user_data: Dict) -> str:
        """Создание сводки прогресса"""
        summary_parts = []
        
        # Общая статистика
        if 'total_days' in user_data:
            summary_parts.append(f"📅 Дней отслеживания: {user_data['total_days']}")
        
        if 'avg_mood' in user_data:
            summary_parts.append(f"😊 Среднее настроение: {user_data['avg_mood']:.1f}/10")
        
        if 'avg_anxiety' in user_data:
            summary_parts.append(f"😰 Средняя тревожность: {user_data['avg_anxiety']:.1f}/10")
        
        if 'completed_exercises' in user_data:
            summary_parts.append(f"💪 Выполнено упражнений: {user_data['completed_exercises']}")
        
        if 'goals_achieved' in user_data:
            summary_parts.append(f"🎯 Достигнуто целей: {user_data['goals_achieved']}")
        
        # Тренды
        if 'mood_trend' in user_data:
            trend_emoji = "📈" if user_data['mood_trend'] == "Растет" else "📉" if user_data['mood_trend'] == "Снижается" else "➡️"
            summary_parts.append(f"{trend_emoji} Тренд настроения: {user_data['mood_trend']}")
        
        if 'anxiety_trend' in user_data:
            trend_emoji = "📉" if user_data['anxiety_trend'] == "Снижается" else "📈" if user_data['anxiety_trend'] == "Растет" else "➡️"
            summary_parts.append(f"{trend_emoji} Тренд тревожности: {user_data['anxiety_trend']}")
        
        # Рекомендации
        if 'recommendations' in user_data:
            summary_parts.append("\n💡 Рекомендации:")
            for rec in user_data['recommendations']:
                summary_parts.append(f"• {rec}")
        
        return "\n".join(summary_parts)
    
    def create_situational_anxiety_chart(self, anxiety_data: List[Dict], days: int = 30) -> str:
        """Создание графика ситуативной тревожности (текущий момент)"""
        if not anxiety_data:
            return self._create_empty_chart("Недостаточно данных о ситуативной тревожности")
        
        # Фильтруем данные за последние N дней
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_data = [
            d for d in anxiety_data 
            if datetime.fromisoformat(d['timestamp']) >= cutoff_date
        ]
        
        if not recent_data:
            return self._create_empty_chart("Недостаточно данных за выбранный период")
        
        # Подготавливаем данные
        dates = [datetime.fromisoformat(d['timestamp']).date() for d in recent_data]
        levels = [d['level'] for d in recent_data]
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Основная линия тревожности
        ax.plot(dates, levels, color=self.colors['secondary'], linewidth=2, marker='o', markersize=6)
        
        # Зона комфорта (0-3) - серая
        ax.axhspan(0, 3, alpha=0.2, color='lightgray', label='Зона комфорта')
        
        # Зона умеренной тревоги (3-6) - жёлтая
        ax.axhspan(3, 6, alpha=0.2, color='yellow', label='Умеренная тревога')
        
        # Зона высокой тревоги (6-10) - красная
        ax.axhspan(6, 10, alpha=0.2, color='red', label='Высокая тревога')
        
        # Настройка графика
        ax.set_title('Ситуативная тревожность', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Дата', fontsize=12)
        ax.set_ylabel('Уровень тревожности (0-10)', fontsize=12)
        ax.set_ylim(0, 10)
        ax.grid(True, alpha=0.3)
        
        # Простое форматирование дат без переполнения
        # Создаем список дат для отображения
        if len(dates) <= 7:
            # Показываем все даты
            display_dates = dates
        elif len(dates) <= 14:
            # Показываем каждую вторую дату
            display_dates = dates[::2]
        elif len(dates) <= 30:
            # Показываем каждую третью дату
            display_dates = dates[::3]
        else:
            # Показываем каждую пятую дату
            display_dates = dates[::5]
        
        # Устанавливаем тики и подписи
        ax.set_xticks(display_dates)
        ax.set_xticklabels([d.strftime('%d.%m') for d in display_dates], rotation=45, ha='right')
        
        # Настройка размера шрифта
        ax.tick_params(axis='x', which='major', labelsize=8)
        plt.tight_layout()
        
        # Добавляем среднее значение
        avg_anxiety = np.mean(levels)
        ax.axhline(y=avg_anxiety, color=self.colors['neutral'], linestyle='--', alpha=0.7, 
                  label=f'Среднее: {avg_anxiety:.1f}')
        ax.legend()
        
        # Сохраняем в base64
        return self._save_chart_to_base64(fig)
    
    def create_general_anxiety_chart(self, anxiety_data: List[Dict], days: int = 30) -> str:
        """Создание графика общей тревожности (средний за день)"""
        if not anxiety_data:
            return self._create_empty_chart("Недостаточно данных об общей тревожности")
        
        # Фильтруем данные за последние N дней
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_data = [
            d for d in anxiety_data 
            if datetime.fromisoformat(d['timestamp']) >= cutoff_date
        ]
        
        if not recent_data:
            return self._create_empty_chart("Недостаточно данных за выбранный период")
        
        # Подготавливаем данные
        dates = [datetime.fromisoformat(d['timestamp']).date() for d in recent_data]
        levels = [d['level'] for d in recent_data]
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Основная линия тревожности
        ax.plot(dates, levels, color=self.colors['primary'], linewidth=2, marker='s', markersize=6)
        
        # Зона комфорта (0-3) - серая
        ax.axhspan(0, 3, alpha=0.2, color='lightgray', label='Зона комфорта')
        
        # Зона умеренной тревоги (3-6) - жёлтая
        ax.axhspan(3, 6, alpha=0.2, color='yellow', label='Умеренная тревога')
        
        # Зона высокой тревоги (6-10) - красная
        ax.axhspan(6, 10, alpha=0.2, color='red', label='Высокая тревога')
        
        # Настройка графика
        ax.set_title('Общая тревожность', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Дата', fontsize=12)
        ax.set_ylabel('Уровень тревожности (0-10)', fontsize=12)
        ax.set_ylim(0, 10)
        ax.grid(True, alpha=0.3)
        
        # Простое форматирование дат без переполнения
        # Создаем список дат для отображения
        if len(dates) <= 7:
            # Показываем все даты
            display_dates = dates
        elif len(dates) <= 14:
            # Показываем каждую вторую дату
            display_dates = dates[::2]
        elif len(dates) <= 30:
            # Показываем каждую третью дату
            display_dates = dates[::3]
        else:
            # Показываем каждую пятую дату
            display_dates = dates[::5]
        
        # Устанавливаем тики и подписи
        ax.set_xticks(display_dates)
        ax.set_xticklabels([d.strftime('%d.%m') for d in display_dates], rotation=45, ha='right')
        
        # Настройка размера шрифта
        ax.tick_params(axis='x', which='major', labelsize=8)
        plt.tight_layout()
        
        # Добавляем среднее значение
        avg_anxiety = np.mean(levels)
        ax.axhline(y=avg_anxiety, color=self.colors['neutral'], linestyle='--', alpha=0.7, 
                  label=f'Среднее: {avg_anxiety:.1f}')
        ax.legend()
        
        # Сохраняем в base64
        return self._save_chart_to_base64(fig)
