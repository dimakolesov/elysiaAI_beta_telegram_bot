"""
Обработчики платежей для бота
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from payment_system import payment_processor, PaymentPlans, PaymentType
from locales import locale_manager, Language
from logger import bot_logger, log_performance
from error_handler import handle_errors, handle_telegram_errors
from validation import validator
from rate_limiter import rate_limiter

# Создаем роутер для платежей
payment_router = Router()

class PaymentStates(StatesGroup):
    """Состояния для платежей"""
    selecting_plan = State()
    confirming_payment = State()
    processing_payment = State()

@payment_router.callback_query(F.data == "shop")
@handle_errors
@handle_telegram_errors
async def shop_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки магазина."""
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(callback.from_user.id, 'callback'):
        await callback.answer("⏰ Слишком много запросов. Подождите немного.", show_alert=True)
        return
    
    # Логирование
    bot_logger.log_callback(callback.from_user.id, "shop")
    
    await state.set_state(PaymentStates.selecting_plan)
    
    # Создаем клавиатуру с планами
    keyboard = create_plans_keyboard()
    
    shop_text = locale_manager.get_text("shop_welcome") if locale_manager.get_text("shop_welcome") != "shop_welcome" else "🛒 Магазин\n\nВыберите план для покупки:"
    
    await callback.message.edit_text(
        shop_text,
        reply_markup=keyboard
    )
    await callback.answer()

@payment_router.callback_query(F.data.startswith("plan_"))
@handle_errors
@handle_telegram_errors
async def plan_selection_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора плана."""
    
    plan_id = callback.data.replace("plan_", "")
    plan = PaymentPlans.get_plan(plan_id)
    
    if not plan:
        await callback.answer("❌ План не найден", show_alert=True)
        return
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(callback.from_user.id, 'callback'):
        await callback.answer("⏰ Слишком много запросов. Подождите немного.", show_alert=True)
        return
    
    # Логирование
    bot_logger.log_callback(callback.from_user.id, f"plan_selected_{plan_id}")
    
    await state.set_state(PaymentStates.confirming_payment)
    await state.update_data(selected_plan=plan_id)
    
    # Создаем сообщение с деталями плана
    plan_text = f"""
💳 {plan.name}

💰 Стоимость: {plan.amount:.0f} ₽
📝 Описание: {plan.description}

🎁 Что вы получите:
"""
    
    for benefit in plan.benefits:
        plan_text += f"• {benefit}\n"
    
    plan_text += f"\n💳 Оплата через YooMoney (ЮMoney)"
    
    # Создаем клавиатуру подтверждения
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", callback_data=f"pay_{plan_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shop")]
        ]
    )
    
    await callback.message.edit_text(
        plan_text,
        reply_markup=keyboard
    )
    await callback.answer()

@payment_router.callback_query(F.data.startswith("pay_"))
@handle_errors
@handle_telegram_errors
@log_performance("payment_creation")
async def payment_confirmation_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик подтверждения платежа."""
    
    plan_id = callback.data.replace("pay_", "")
    plan = PaymentPlans.get_plan(plan_id)
    
    if not plan:
        await callback.answer("❌ План не найден", show_alert=True)
        return
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(callback.from_user.id, 'callback'):
        await callback.answer("⏰ Слишком много запросов. Подождите немного.", show_alert=True)
        return
    
    # Логирование
    bot_logger.log_callback(callback.from_user.id, f"payment_confirmed_{plan_id}")
    
    await state.set_state(PaymentStates.processing_payment)
    
    try:
        # Создаем платеж
        payment_result = await payment_processor.create_payment(
            user_id=callback.from_user.id,
            plan_id=plan_id
        )
        
        if not payment_result["success"]:
            await callback.message.edit_text(
                f"❌ Ошибка создания платежа: {payment_result.get('error', 'Неизвестная ошибка')}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shop")]
                    ]
                )
            )
            await callback.answer()
            return
        
        # Отправляем информацию о платеже
        payment_text = f"""
💳 Платеж создан

💰 Сумма: {payment_result['amount']:.0f} ₽
📝 Описание: {payment_result['description']}

🔗 Для оплаты перейдите по ссылке:
{payment_result.get('confirmation_url', 'Ссылка будет отправлена отдельно')}

⏰ Платеж действителен в течение 24 часов
"""
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить статус", callback_data=f"check_payment_{payment_result['payment_id']}")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_payment_{payment_result['payment_id']}")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shop")]
            ]
        )
        
        await callback.message.edit_text(
            payment_text,
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Payment creation failed for user {callback.from_user.id}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании платежа. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shop")]
                ]
            )
        )
        await callback.answer()

@payment_router.callback_query(F.data.startswith("check_payment_"))
@handle_errors
@handle_telegram_errors
async def check_payment_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик проверки статуса платежа."""
    
    payment_id = callback.data.replace("check_payment_", "")
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(callback.from_user.id, 'callback'):
        await callback.answer("⏰ Слишком много запросов. Подождите немного.", show_alert=True)
        return
    
    try:
        # Проверяем статус платежа
        payment_info = await payment_processor.payment_manager.check_payment_status(payment_id)
        
        if payment_info["paid"]:
            # Обрабатываем успешный платеж
            result = await payment_processor.process_payment_success(
                user_id=callback.from_user.id,
                payment_id=payment_id
            )
            
            if result["success"]:
                success_text = f"""
✅ Платеж успешно обработан!

🎁 Полученные бонусы:
"""
                for benefit in result["benefits_applied"]:
                    success_text += f"• {benefit}\n"
                
                success_text += "\n💖 Спасибо за покупку!"
                
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                    ]
                )
                
                await callback.message.edit_text(
                    success_text,
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    f"❌ Ошибка обработки платежа: {result.get('error', 'Неизвестная ошибка')}"
                )
        else:
            status_text = f"""
⏳ Статус платежа

💰 Сумма: {payment_info['amount']['value']} {payment_info['amount']['currency']}
📊 Статус: {payment_info['status']}
⏰ Создан: {payment_info['created_at']}

💳 Платеж еще не оплачен. Пожалуйста, завершите оплату.
"""
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Проверить еще раз", callback_data=f"check_payment_{payment_id}")],
                    [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_payment_{payment_id}")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shop")]
                ]
            )
            
            await callback.message.edit_text(
                status_text,
                reply_markup=keyboard
            )
        
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Payment check failed for user {callback.from_user.id}")
        await callback.answer("❌ Ошибка проверки платежа", show_alert=True)

@payment_router.callback_query(F.data.startswith("cancel_payment_"))
@handle_errors
@handle_telegram_errors
async def cancel_payment_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик отмены платежа."""
    
    payment_id = callback.data.replace("cancel_payment_", "")
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(callback.from_user.id, 'callback'):
        await callback.answer("⏰ Слишком много запросов. Подождите немного.", show_alert=True)
        return
    
    try:
        # Отменяем платеж
        result = await payment_processor.cancel_payment(
            user_id=callback.from_user.id,
            payment_id=payment_id
        )
        
        if result["success"]:
            await callback.message.edit_text(
                "❌ Платеж отменен",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад в магазин", callback_data="shop")]
                    ]
                )
            )
        else:
            await callback.message.edit_text(
                f"❌ Ошибка отмены платежа: {result.get('error', 'Неизвестная ошибка')}"
            )
        
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Payment cancellation failed for user {callback.from_user.id}")
        await callback.answer("❌ Ошибка отмены платежа", show_alert=True)

@payment_router.callback_query(F.data == "back_to_shop")
@handle_errors
@handle_telegram_errors
async def back_to_shop_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик возврата в магазин."""
    
    await state.set_state(PaymentStates.selecting_plan)
    
    keyboard = create_plans_keyboard()
    shop_text = "🛒 Магазин\n\nВыберите план для покупки:"
    
    await callback.message.edit_text(
        shop_text,
        reply_markup=keyboard
    )
    await callback.answer()

def create_plans_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с планами"""
    plan = PaymentPlans.get_plan("premium_month")
    
    if not plan:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
            ]
        )
    
    buttons = [
        [InlineKeyboardButton(
            text=f"{plan.name} - {plan.amount:.0f} ₽",
            callback_data=f"plan_{plan.id}"
        )],
        [InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="main_menu"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
