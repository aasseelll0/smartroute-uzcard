# SmartRoute · Uzcard AI Backend

## Тестовые карты для демо

| Номер карты | Статус | Банк | Код |
|-------------|--------|------|-----|
| 8600123456789012 | 🔴 Заблокирована (ЦБ) | Kapitalbank | 818 |
| 8600987654321098 | ✅ Активна | Xalq Bank | 000 |
| 8600111222333444 | 🔴 Заблокирована (банк) | Hamkorbank | 205 |
| 9860111222333444 | ⚠️ Истёк срок | Ipoteka Bank | 101 |
| 5614123456789012 | ✅ Активна (межд.) | TBC Bank | 000 |
| 5440987654321098 | 🔴 Заблокирована (PIN) | Aloqabank | 119 |

## Как задеплоить на Render.com (бесплатно)

1. Иди на github.com → создай новый репозиторий "smartroute-uzcard"
2. Загрузи файлы: main.py, requirements.txt, render.yaml
3. Иди на render.com → New → Web Service
4. Подключи свой GitHub репозиторий
5. Render автоматически задеплоит
6. Получишь URL типа: https://smartroute-uzcard.onrender.com

## API Endpoints

### Проверить карту
POST /check-card
{"card_number": "8600123456789012"}

### Получить отдел
POST /get-department  
{"keyword": "банкомат"}

### Список тестовых карт
GET /cards
