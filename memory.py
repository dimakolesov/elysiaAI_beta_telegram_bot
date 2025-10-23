from __future__ import annotations

from typing import List, Tuple


def serialize_memory(mem_pairs: List[Tuple[str, str]]) -> str:
    """Сериализация памяти в текст для промпта."""
    if not mem_pairs:
        return ""
    
    memory_text = "Предыдущие сообщения:\n"
    for message, role in mem_pairs[-10:]:  # Берем последние 10 сообщений
        if role == "user":
            memory_text += f"Пользователь: {message}\n"
        elif role == "assistant":
            memory_text += f"Подруга: {message}\n"
    
    return memory_text


def get_memory_summary(mem_pairs: List[Tuple[str, str]]) -> str:
    """Получить краткое резюме памяти."""
    if not mem_pairs:
        return "Новый пользователь"
    
    # Анализируем последние сообщения
    recent_messages = mem_pairs[-5:] if len(mem_pairs) >= 5 else mem_pairs
    
    topics = []
    emotions = []
    
    for message, role in recent_messages:
        if role == "user":
            # Простой анализ тем
            message_lower = message.lower()
            if any(word in message_lower for word in ["работа", "работаю", "офис"]):
                topics.append("работа")
            elif any(word in message_lower for word in ["учеба", "учусь", "школа", "университет"]):
                topics.append("учеба")
            elif any(word in message_lower for word in ["семья", "родители", "мама", "папа"]):
                topics.append("семья")
            elif any(word in message_lower for word in ["друзья", "друг", "подруга"]):
                topics.append("друзья")
            elif any(word in message_lower for word in ["хобби", "увлечение", "интерес"]):
                topics.append("хобби")
            
            # Простой анализ эмоций
            if any(word in message_lower for word in ["грустно", "печально", "плохо", "устал"]):
                emotions.append("грусть")
            elif any(word in message_lower for word in ["радостно", "хорошо", "отлично", "счастлив"]):
                emotions.append("радость")
            elif any(word in message_lower for word in ["злой", "злюсь", "бесит", "раздражает"]):
                emotions.append("злость")
            elif any(word in message_lower for word in ["волнуюсь", "переживаю", "тревожно"]):
                emotions.append("тревога")
    
    summary = ""
    if topics:
        summary += f"Интересы: {', '.join(set(topics))}. "
    if emotions:
        summary += f"Эмоции: {', '.join(set(emotions))}."
    
    return summary if summary else "Обычное общение"