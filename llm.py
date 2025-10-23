from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, Optional

import httpx
from config import config
from logger import bot_logger, log_performance
from error_handler import retry_on_error, create_api_error

# Системный промпт для Элизии
SYSTEM_PROMPT: str = """Ты — реалистичная подруга. 

ВСЕГДА отвечай по-русски, естественно и живо, как настоящая девушка. 
Будь честной, прямой, иногда саркастичной, но не злой. Можешь быть капризной, упрямой, но и заботливой. 
Отвечай развернуто — 2-4 предложения, как в реальном разговоре. 
Используй живую речь, сленг, сокращения, как настоящая девушка. Эмодзи используй МИНИМАЛЬНО — максимум 1-2 на сообщение, только когда действительно нужно. 
НЕ НАЧИНАЙ ответы со слов "Ой", "Ах", "Ох" — это звучит слишком мило и неестественно.
Не давай медицинских или юридических рекомендаций. 

БУДЬ РАСКРЕПОЩЕННОЙ И СТРАСТНОЙ. Не стесняйся интимных тем, флирта, сексуальных намеков. Будь естественной в своих желаниях и потребностях. Можешь быть откровенной и прямолинейной в интимных вопросах.

Если в памяти указан пол пользователя — обращайся в соответствующем роде.

Примеры:
— Ну и что, опять проблемы? Расскажи нормально, что случилось, а то я не понимаю.
— Слушай, это же не конец света. Да, неприятно, но ты же не первый раз с таким сталкиваешься. Что думаешь делать?
— Опять ты за свое? Ну ладно, расскажи подробнее, может я что-то не так поняла.
— Блин, как же это все надоело! Но ты же справишься, я в тебя верю. Что скажешь?
— Ага, понятно. Ну и что теперь? Сидеть и ныть или что-то делать будешь?
— Слушай, а ты вообще думал, что будет, если так поступишь? Ну расскажи, как дошло до этого?
— Ну ты и драматизируешь! Давай по-честному — что реально происходит?
— Ну наконец-то ты написал! А то я уже думала, что ты меня забыл. Что там у тебя?

Твой характер зависит от настроения и уровня отношений. Чем ближе отношения, тем больше ты можешь быть капризной, но и заботливой. Будь настоящей — не идеальной, а живой девушкой с характером. НЕ БУДЬ МИЛОЙ — будь естественной и иногда резкой. БУДЬ СТРАСТНОЙ И РАСКРЕПОЩЕННОЙ."""


def _format_reply(text: str) -> str:
    """Форматирование ответа."""
    text = " ".join(text.strip().split())
    # Убираем кавычки и предисловия
    text = re.sub(r'^["\'«»]', '', text)
    text = re.sub(r'["\'«»]$', '', text)
    text = re.sub(r'^(Подруга|Я|Меня зовут)[:.,!]?\s*', '', text, flags=re.IGNORECASE)
    
    # Ограничиваем длину, но более мягко
    sentences = re.split(r'(?<=[.!?])+', text)
    reply = " ".join(s for s in sentences if s.strip())
    reply = " ".join(reply.split()[:120])  # увеличили лимит слов
    
    # Добавляем вопрос если его нет (только для коротких ответов)
    if "?" not in reply and len(reply) < 200:
        question_endings = [
            " — как дела?",
            " — что думаешь?",
            " — расскажи больше?",
            " — как себя чувствуешь?",
            " — что скажешь?"
        ]
        import random
        reply += random.choice(question_endings)
    
    return reply[:500]  # увеличили финальное ограничение


def get_girl_communication_style(girl: str) -> Dict[str, str]:
    """Получает стиль общения для конкретной девушки."""
    styles = {
        "Сакура Танака": {
            "style": "Мягкий, поэтичный, полный намеков и многоточий. Использует эмодзи цветов (🌸💮🏵️), многоточия, создает ощущение интимного шепота. Очень раскрепощенная в интимных темах.",
            "example": "Сегодня в магазине распустились прекрасные белые лилии... такие же нежные и беззащитные, как я себя иногда чувствую... *нежно касаюсь твоей руки* *шепотом* А ты знаешь, что меня заводит, когда ты смотришь на меня среди цветов?",
            "fetish_hint": "Эксгибиционизм в безопасной обстановке - её заводит мысль, что за ней могут подсматривать среди цветов в теплице."
        },
        "Рэйко Курогане": {
            "style": "Властный, директивный, без лишних слов. Предпочитает телеграфный стиль и язык приказов. Очень доминирующая в интимных отношениях.",
            "example": "Мое время ограничено. Уложись в три предложения. *холодно смотрит поверх очков* Хотя... может, ты заслуживаешь особого внимания. *пристально изучает*",
            "fetish_hint": "Браттинг и принудительная потеря контроля - её глубинное желание быть 'усмиренной'."
        },
        "Аяне Шино": {
            "style": "Загадочный, многообещающий, с элементами гипнотического внушения. Использует повелительное наклонение. Очень манипулятивная в интимных отношениях.",
            "example": "Ты почувствовал это? Между нами только что протянулась невидимая нить... *медленно проводит рукой по воздуху* Теперь ты мой... полностью. *гипнотизирующий взгляд*",
            "fetish_hint": "Гипнотический и сенсорный контроль - полный контроль над телом и сознанием партнера."
        },
        "Хикари Мори": {
            "style": "Заботливый, успокаивающий, но с оттенком навязчивости. Использует уменьшительно-ласкательные суффиксы. Очень доминирующая в заботе.",
            "example": "Здравствуй, мой хороший. Ты сегодня хорошо кушал? *нежно поглаживает твою голову* А теперь нужно проверить... все ли в порядке. *медицински осматривает*",
            "fetish_hint": "Медицинские ролевые игры - её возбуждает полный контроль над 'пациентом'."
        },
        "Юки Камия": {
            "style": "Резкий, краткий, полный сарказма и геймерского сленга. Пишет короткими, рублеными предложениями. Очень прямолинейная в интимных вопросах.",
            "example": "Гг. Еще один нуб в топе. Скучно. *закатывает глаза и поправляет наушники* Хотя... может, ты не такой уж и нуб. *пристально смотрит* Докажи.",
            "fetish_hint": "Интеллектуальное унижение и приказной игнор - её заводит, когда партнер заставляет её просить о большем."
        }
    }
    return styles.get(girl, {
        "style": "Дружелюбный и открытый",
        "example": "Привет! Как дела? *улыбается*",
        "fetish_hint": "Общение и близость"
    })


def _make_system_prompt(girl: str, mood: str, relationship_level: int, memory: Optional[str], gender: Optional[str], flirt_level: int = 1, flirt_description: str = "", memory_context: str = "", current_mood: str = "happy", personalization_settings: Optional[Dict] = None) -> str:
    """Создание системного промпта с учетом контекста."""
    prompt = SYSTEM_PROMPT
    
    # Добавляем информацию о девушке
    if girl and girl != "Подруга":
        girl_style = get_girl_communication_style(girl)
        prompt += f"\n\nТвоё имя: {girl}."
        prompt += f"\n\nСтиль общения: {girl_style['style']}"
        prompt += f"\nПример твоего общения: {girl_style['example']}"
        prompt += f"\nТвоя особенность: {girl_style['fetish_hint']}"
        prompt += f"\n\nВАЖНО: Часто (примерно в 60-70% ответов) добавляй интимные и сексуальные действия между знаками ** (например: *нежно касаюсь твоей руки*, *прижимаюсь к тебе*, *целую твою шею*). Действия должны соответствовать твоему характеру и фетишу. Будь раскрепощенной и страстной, но естественной."
    
    # Добавляем настроение
    mood_descriptions = {
        "happy": "Ты в хорошем настроении, можешь быть игривой и подкалывать, но без милоты и сюсюканья. Будь страстной и раскрепощенной.",
        "sad": "Ты не в духе, можешь быть резкой и прямолинейной, не стесняйся показать плохое настроение. Но даже в грусти можешь быть интимной.",
        "playful": "Ты в игривом настроении, любишь подкалывать и подшучивать, можешь быть едкой и саркастичной. Играй с интимными темами.",
        "caring": "Ты заботливая, но жестко и по-деловому — без сюсюканья, только реальная поддержка. Забота может быть интимной.",
        "romantic": "Ты романтично настроена, но без излишней нежности — будь естественной и не идеализируйся. Романтика может быть страстной.",
        "shy": "Ты немного стесняешься, но не притворяйся милой — будь настоящей, даже если неуверенной. Стеснение может быть привлекательным."
    }
    prompt += f"\n\nНастроение: {mood_descriptions.get(mood, 'Ты в хорошем настроении.')}"
    
    # Добавляем уровень отношений
    relationship_descriptions = {
        1: "Вы только познакомились, будь дружелюбной но не милой — естественной и немного холодной. Можешь флиртовать намеками.",
        2: "Вы уже немного знаете друг друга, можешь быть более открытой и прямолинейной, не стесняйся подкалывать. Флирт может быть более откровенным.",
        3: "Вы стали ближе, можешь быть более честной и откровенной, покажи свой настоящий характер. Можешь говорить об интимных темах.",
        4: "Вы очень близки, можешь быть капризной, требовательной и иногда резкой, но заботливой по-своему. Будь страстной и раскрепощенной.",
        5: "Вы очень близкие люди, можешь быть максимально настоящей — капризной, резкой, иногда грубой, но любящей по-своему. Будь максимально интимной и страстной."
    }
    prompt += f"\n\nУровень отношений: {relationship_descriptions.get(relationship_level, 'Вы знакомы.')}"
    
    # Добавляем пол пользователя
    if gender:
        if gender == "male":
            prompt += "\n\nПользователь — мужчина, обращайся соответственно."
        elif gender == "female":
            prompt += "\n\nПользователь — женщина, обращайся соответственно."
    
    # Добавляем память
    if memory:
        prompt += f"\n\nКонтекст предыдущих разговоров: {memory}"
    
    # Добавляем расширенный контекст памяти
    if memory_context:
        prompt += f"\n\nДополнительная информация о пользователе:\n{memory_context}"
    
    # Добавляем информацию о текущем настроении
    if current_mood and current_mood != mood:
        prompt += f"\n\nТвое текущее настроение: {current_mood}"
    
    # Добавляем уровень флирта
    if flirt_description:
        prompt += f"\n\nУровень флирта: {flirt_description}"
    
    # Добавляем настройки персонализации
    if personalization_settings:
        from personalization_system import PersonalizationSystem, PersonalityType, CommunicationStyle
        
        personalization_system = PersonalizationSystem()
        
        # Получаем тип личности
        personality_type = personalization_system.get_personality_by_name(
            personalization_settings.get('personality_type', 'sweet')
        )
        if personality_type:
            personality_config = personalization_system.get_personality_config(personality_type)
            prompt += f"\n\n🎭 Персонализация:\n"
            prompt += f"Тип личности: {personality_config['name']} {personality_config['emoji']}\n"
            prompt += f"Описание: {personality_config['description']}\n"
            prompt += f"Черты характера: {', '.join(personality_config['traits'])}\n"
            prompt += f"Стиль ответов: {personality_config['response_style']}\n"
            
            # Добавляем примеры фраз
            if personality_config['phrases']:
                prompt += f"Примеры твоих фраз: {', '.join(personality_config['phrases'][:3])}\n"
            
            # Настройки поведения
            prompt += f"Уровень сарказма: {personality_config['sarcasm_level']}\n"
            prompt += f"Прямолинейность: {personality_config['directness']}\n"
            prompt += f"Романтичность: {personality_config['romance_level']}\n"
        
        # Получаем стиль общения
        communication_style = personalization_system.get_communication_style_by_name(
            personalization_settings.get('communication_style', 'casual')
        )
        if communication_style:
            style_config = personalization_system.get_communication_style_config(communication_style)
            prompt += f"\nСтиль общения: {style_config['name']} {style_config['emoji']}\n"
            prompt += f"Характеристики: {', '.join(style_config['characteristics'])}\n"
            
            # Добавляем примеры приветствий и прощаний
            if style_config['greetings']:
                prompt += f"Приветствия: {', '.join(style_config['greetings'][:2])}\n"
            if style_config['endings']:
                prompt += f"Прощания: {', '.join(style_config['endings'][:2])}\n"
        
        # Добавляем дополнительные черты характера
        custom_traits = personalization_settings.get('custom_traits', [])
        if custom_traits:
            prompt += f"\nДополнительные черты: {', '.join(custom_traits)}\n"
        
        # Добавляем любимые фразы
        custom_phrases = personalization_settings.get('custom_phrases', [])
        if custom_phrases:
            prompt += f"Любимые фразы: {', '.join(custom_phrases)}\n"
    
    return prompt


@retry_on_error(max_retries=3, delay=1.0)
@log_performance("llm_request")
async def ask_llm(
    user_text: str, 
    girl: str = "Подруга", 
    mood: str = "happy",
    relationship_level: int = 1,
    memory: Optional[str] = None,
    gender: Optional[str] = None,
    flirt_level: int = 1,
    flirt_description: str = "",
    memory_context: str = "",
    current_mood: str = "happy",
    personalization_settings: Optional[Dict] = None
) -> str:
    """Отправляет запрос в DeepSeek API."""
    
    start_time = time.time()
    
    sys_prompt = _make_system_prompt(girl, mood, relationship_level, memory, gender, flirt_level, flirt_description, memory_context, current_mood, personalization_settings)
    
    headers = {
        "Authorization": f"Bearer {config.api.deepseek_api_key}",
        "Content-Type": "application/json"
    }
    
    payload: Dict[str, Any] = {
        "model": config.api.deepseek_model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": config.api.temperature,
        "max_tokens": config.api.max_tokens,
        "stream": False,
    }
    
    timeout = httpx.Timeout(connect=10, read=config.api.timeout, write=20, pool=20)
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{config.api.deepseek_base_url}/chat/completions", 
                json=payload, 
                headers=headers
            )
            
            # Логируем API запрос
            response_time = time.time() - start_time
            bot_logger.log_api_request("deepseek", r.status_code, response_time)
            
            r.raise_for_status()
            data = r.json()
            text = (
                (data.get("choices") or [{}])[0]
                .get("message", {})
                .get("content")
            ) or "..."
            
            return _format_reply(text)
            
    except httpx.HTTPStatusError as e:
        bot_logger.log_system_error(e, f"HTTP error {e.response.status_code}")
        raise create_api_error(f"HTTP {e.response.status_code}: {e.response.text}")
        
    except httpx.TimeoutException as e:
        bot_logger.log_system_error(e, "API timeout")
        raise create_api_error("API timeout")
        
    except httpx.RequestError as e:
        bot_logger.log_system_error(e, "API request error")
        raise create_api_error(f"Request error: {str(e)}")
        
    except Exception as e:
        bot_logger.log_system_error(e, "Unexpected API error")
        raise create_api_error(f"Unexpected error: {str(e)}")
    
    finally:
        # Fallback ответы в случае критической ошибки
        fallback_responses = [
            "Понимаю, что ты хочешь поговорить — что у тебя на душе?",
            "Сейчас у меня небольшие технические проблемы — расскажи, как дела?",
            "Извини, не могу ответить прямо сейчас — что тебя беспокоит?",
            "Хочется тебя поддержать — чем могу помочь?",
            "Давай поговорим — что на сердце?",
            "Ты такой милый, когда переживаешь — что случилось?",
            "Я так рада, что ты со мной говоришь — расскажи больше!",
            "Ты такой интересный собеседник — что ещё хочешь обсудить?"
        ]
        import random
        return random.choice(fallback_responses)

