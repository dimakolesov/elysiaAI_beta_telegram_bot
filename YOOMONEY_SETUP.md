# 🔧 Настройка YooMoney для бота

## 📋 Пошаговая инструкция

### 1. Получение Secret Key

1. **Зайдите в личный кабинет YooMoney:**
   - Перейдите на https://yoomoney.ru/
   - Войдите в свой аккаунт

2. **Перейдите в раздел "Для разработчиков":**
   - В меню выберите "Для разработчиков"
   - Или перейдите напрямую: https://yoomoney.ru/developers

3. **Создайте приложение:**
   - Нажмите "Создать приложение"
   - Заполните данные:
     - **Название:** Elysia AI Bot
     - **Описание:** Telegram бот для виртуальной подруги
     - **Redirect URI:** `https://t.me/elysia_ai_bot`

4. **Получите ключи:**
   - После создания приложения вы получите:
     - **Client ID:** `906B63FC5E6BD7825970D5ADFAF70203BE667B5359729D1162A7E33D0CFF38A1` ✅
     - **Secret Key:** `ваш_секретный_ключ` ❌ (нужно получить)

### 2. Настройка Webhook URL

#### Для локальной разработки:

1. **Запустите webhook сервер:**
   ```bash
   cd bot
   python3 webhook_server.py
   ```

2. **Используйте ngrok для публичного доступа:**
   ```bash
   # Установите ngrok
   brew install ngrok  # macOS
   # или скачайте с https://ngrok.com/
   
   # Запустите туннель
   ngrok http 8080
   ```

3. **Получите публичный URL:**
   - ngrok покажет URL вида: `https://abc123.ngrok.io`
   - Используйте: `https://abc123.ngrok.io/webhook/yoomoney`

#### Для продакшена:

1. **Разместите бота на сервере**
2. **Настройте домен и SSL**
3. **Используйте URL:** `https://ваш-домен.com/webhook/yoomoney`

### 3. Обновление конфигурации

Отредактируйте файл `config.env`:

```env
# YooMoney Configuration
YOOMONEY_CLIENT_ID=906B63FC5E6BD7825970D5ADFAF70203BE667B5359729D1162A7E33D0CFF38A1
YOOMONEY_SECRET_KEY=ваш_секретный_ключ_от_yoomoney
YOOMONEY_WEBHOOK_URL=https://ваш-домен.com/webhook/yoomoney
```

### 4. Настройка в личном кабинете YooMoney

1. **В настройках приложения:**
   - Укажите **Webhook URL**
   - Выберите события: `payment.succeeded`, `payment.canceled`
   - Сохраните настройки

### 5. Тестирование

1. **Запустите webhook сервер:**
   ```bash
   python3 webhook_server.py
   ```

2. **Запустите бота:**
   ```bash
   python3 main.py
   ```

3. **Протестируйте платеж:**
   - Отправьте `/start` боту
   - Нажмите "🛒 Магазин"
   - Выберите "⭐ Премиум подписка"
   - Следуйте инструкциям

## 🔍 Проверка статуса

Запустите проверку:
```bash
python3 -c "
from config import config
print(f'Client ID: {config.yoomoney.client_id}')
print(f'Secret Key: {\"✅ Установлен\" if config.yoomoney.secret_key != \"your_secret_key_here\" else \"❌ НЕ установлен\"}')
print(f'Webhook URL: {config.yoomoney.webhook_url}')
"
```

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи webhook сервера
2. Убедитесь, что URL доступен извне
3. Проверьте настройки в личном кабинете YooMoney
