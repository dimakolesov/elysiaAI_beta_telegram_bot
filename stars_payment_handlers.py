"""
Обработчики платежей в Telegram Stars
"""

from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from telegram_stars import stars_payment
from logger import bot_logger
from error_handler import handle_errors, handle_telegram_errors
from db import grant_access
from admin_system import admin_system
from referral_system import referral_system

stars_router = Router()

@stars_router.message(Command("premium"))
@handle_errors
@handle_telegram_errors
async def premium_subscription_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /premium для покупки подписки"""
    
    # Проверяем, является ли пользователь админом
    if admin_system.is_admin(message.from_user.username):
        await message.answer(
            "👑 Админ-доступ\n\n"
            "У вас есть полный доступ ко всем функциям бота без подписки!\n"
            "Используйте команду /admin для управления ботом."
        )
        return
    
    # Логирование
    bot_logger.log_command(message.from_user.id, "premium")
    
    try:
        # Получаем данные для выставления счета
        invoice_data = stars_payment.create_payment_invoice_data()
        
        # Выставляем счет
        await message.answer_invoice(**invoice_data)
        
        bot_logger.log_info(f"Payment invoice sent to user {message.from_user.id}")
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to send payment invoice to user {message.from_user.id}")
        await message.answer(
            "❌ Ошибка при создании платежа. Попробуйте позже или обратитесь в поддержку."
        )

@stars_router.pre_checkout_query()
@handle_errors
@handle_telegram_errors
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery) -> None:
    """Обработчик предпродажной проверки"""
    
    try:
        # Логируем запрос на предпродажную проверку
        bot_logger.log_info(f"Pre-checkout query from user {pre_checkout_query.from_user.id}")
        
        # Проверяем payload
        if pre_checkout_query.invoice_payload != stars_payment.premium_payload:
            await pre_checkout_query.answer(
                ok=False,
                error_message="Неверный тип платежа"
            )
            return
        
        # Подтверждаем платеж
        await pre_checkout_query.answer(ok=True)
        
        bot_logger.log_info(f"Pre-checkout approved for user {pre_checkout_query.from_user.id}")
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Pre-checkout error for user {pre_checkout_query.from_user.id}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Ошибка обработки платежа"
        )

@stars_router.message(F.successful_payment)
@handle_errors
@handle_telegram_errors
async def successful_payment_handler(message: Message, state: FSMContext) -> None:
    """Обработчик успешного платежа"""
    
    try:
        user_id = message.from_user.id
        payment = message.successful_payment
        
        # Логируем успешный платеж
        bot_logger.log_info(f"Successful payment from user {user_id}: {payment.total_amount} {payment.currency}")
        
        # Проверяем тип платежа
        if payment.invoice_payload == stars_payment.premium_payload:
            # Предоставляем премиум доступ на 30 дней
            await grant_access(user_id, 30)
            
            # Обрабатываем реферальную комиссию
            referrer_id = await referral_system.process_subscription_purchase(user_id)
            if referrer_id:
                # Уведомляем реферера о получении комиссии
                try:
                    await bot.send_message(
                        referrer_id,
                        f"💰 Ты получил комиссию!\n\n"
                        f"Твой реферал оформил подписку и ты получил {referral_system.SUBSCRIPTION_PRICE * referral_system.COMMISSION_RATE:.2f} ₽!\n\n"
                        f"Продолжай приглашать друзей и зарабатывай больше! 💎"
                    )
                except Exception as e:
                    bot_logger.log_system_error(e, f"Failed to notify referrer {referrer_id} about commission")
            
            # Отправляем сообщение об успехе
            success_text = f"""
🎉 Платеж успешно обработан!

✅ Что вы получили:
• Премиум подписка на 30 дней
• Неограниченные сообщения
• Доступ ко всем функциям бота
• Приоритетная поддержка

💎 Детали платежа:
• Сумма: {payment.total_amount} ⭐
• ID платежа: {payment.telegram_payment_charge_id}
• Дата: {payment.date}

Спасибо за покупку! Наслаждайтесь премиум функциями! 💖
"""
            
            await message.answer(success_text)
            
            # Логируем предоставление доступа
            bot_logger.log_admin_action("premium_granted", {
                "user_id": user_id,
                "payment_id": payment.telegram_payment_charge_id,
                "amount": payment.total_amount,
                "days": 30
            })
            
        else:
            await message.answer("❌ Неизвестный тип платежа")
            
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to process successful payment for user {message.from_user.id}")
        await message.answer(
            "❌ Ошибка обработки платежа. Обратитесь в поддержку: @d_kolesov"
        )

@stars_router.message(Command("paysupport"))
@handle_errors
@handle_telegram_errors
async def pay_support_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /paysupport"""
    
    # Логирование
    bot_logger.log_command(message.from_user.id, "paysupport")
    
    try:
        support_text = """
💳 ПОДДЕРЖКА ПЛАТЕЖЕЙ

📞 Связь с поддержкой:
• Telegram: @d_kolesov
• Время ответа: до 24 часов

❓ Частые вопросы:
• Как купить подписку? → /premium
• Как получить возврат? → Читайте условия ниже
• Технические проблемы? → Обратитесь в поддержку

📋 Условия возврата средств:
"""
        
        refund_terms = stars_payment.get_refund_terms()
        
        await message.answer(
            support_text + refund_terms,
            reply_markup=stars_payment.create_pay_support_keyboard()
        )
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to send pay support info to user {message.from_user.id}")
        await message.answer("❌ Ошибка загрузки информации о поддержке")

@stars_router.callback_query(F.data == "refund_terms")
@handle_errors
@handle_telegram_errors
async def refund_terms_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки условий возврата"""
    
    try:
        refund_terms = stars_payment.get_refund_terms()
        
        await callback.message.edit_text(
            refund_terms,
            reply_markup=stars_payment.create_pay_support_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        bot_logger.log_system_error(e, f"Failed to show refund terms for user {callback.from_user.id}")
        await callback.answer("❌ Ошибка загрузки условий возврата", show_alert=True)
