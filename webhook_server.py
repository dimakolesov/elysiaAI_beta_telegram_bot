"""
Простой webhook сервер для YooMoney
Запускается локально для тестирования платежей
"""

import asyncio
import json
from aiohttp import web, web_request
from aiohttp.web import Request, Response
import logging
from yoomoney import payment_manager
from logger import bot_logger

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookServer:
    """Сервер для обработки webhook от YooMoney"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Настройка маршрутов"""
        self.app.router.add_post('/webhook/yoomoney', self.handle_yoomoney_webhook)
        self.app.router.add_get('/health', self.health_check)
    
    async def handle_yoomoney_webhook(self, request: Request) -> Response:
        """Обработка webhook от YooMoney"""
        try:
            # Получаем данные
            data = await request.json()
            logger.info(f"Received webhook: {json.dumps(data, indent=2)}")
            
            # Проверяем тип события
            event_type = data.get('event')
            
            if event_type == 'payment.succeeded':
                await self.handle_payment_success(data)
            elif event_type == 'payment.canceled':
                await self.handle_payment_canceled(data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
            
            return web.Response(text="OK", status=200)
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.Response(text="Error", status=500)
    
    async def handle_payment_success(self, data: dict):
        """Обработка успешного платежа"""
        try:
            payment_id = data.get('object', {}).get('id')
            user_id = data.get('object', {}).get('metadata', {}).get('user_id')
            
            if not payment_id or not user_id:
                logger.error("Missing payment_id or user_id in webhook data")
                return
            
            logger.info(f"Payment succeeded: {payment_id} for user {user_id}")
            
            # Обрабатываем успешный платеж
            await payment_manager.handle_payment_success(payment_id, int(user_id))
            
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
    
    async def handle_payment_canceled(self, data: dict):
        """Обработка отмененного платежа"""
        try:
            payment_id = data.get('object', {}).get('id')
            user_id = data.get('object', {}).get('metadata', {}).get('user_id')
            
            if not payment_id or not user_id:
                logger.error("Missing payment_id or user_id in webhook data")
                return
            
            logger.info(f"Payment canceled: {payment_id} for user {user_id}")
            
            # Обрабатываем отмену платежа
            await payment_manager.handle_payment_canceled(payment_id, int(user_id))
            
        except Exception as e:
            logger.error(f"Error handling payment cancel: {e}")
    
    async def health_check(self, request: Request) -> Response:
        """Проверка здоровья сервера"""
        return web.Response(text="Webhook server is running", status=200)
    
    async def start(self):
        """Запуск сервера"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        logger.info(f"Webhook server started on http://localhost:{self.port}")
        logger.info(f"Webhook URL: http://localhost:{self.port}/webhook/yoomoney")
        
        # Держим сервер запущенным
        try:
            await asyncio.Future()  # Запускаем бесконечный цикл
        except KeyboardInterrupt:
            logger.info("Shutting down webhook server...")
        finally:
            await runner.cleanup()

async def main():
    """Главная функция"""
    server = WebhookServer(port=8080)
    await server.start()

if __name__ == "__main__":
    print("🚀 Запуск webhook сервера для YooMoney...")
    print("📡 Webhook URL: http://localhost:8080/webhook/yoomoney")
    print("🔗 Для публичного доступа используйте ngrok:")
    print("   ngrok http 8080")
    print("   Затем используйте полученный URL в настройках YooMoney")
    print("\n⏹️  Для остановки нажмите Ctrl+C")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Webhook сервер остановлен")
