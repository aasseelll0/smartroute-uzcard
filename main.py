from flask import Flask, request, jsonify
import json
import requests
from datetime import datetime

app = Flask(__name__)

# ==========================================
# КОНФИГ
# ==========================================
TELEGRAM_BOT_TOKEN = "8614127017:AAHfkyT7bXF1KIdjdJH8eqYsSeV6r6Wsgpw"
TELEGRAM_CHAT_ID = "-5256347531"

# ==========================================
# БАЗА ДАННЫХ КАРТ UZCARD
# ==========================================
CARDS_DB = {
    "8600123456789012": {
        "status": "blocked", "response_code": "818",
        "response_text": "Заблокирована по решению Центрального банка",
        "bank": "Kapitalbank", "type": "local", "holder": "ALISHER KARIMOV",
        "action": "Обратитесь в Центральный банк Узбекистана для разблокировки."
    },
    "8600987654321098": {
        "status": "active", "response_code": "000",
        "response_text": "Карта активна",
        "bank": "Xalq Bank", "type": "local", "holder": "NILUFAR RASHIDOVA",
        "action": "Карта работает в штатном режиме."
    },
    "8600111222333444": {
        "status": "blocked", "response_code": "205",
        "response_text": "Заблокирована банком-эмитентом",
        "bank": "Hamkorbank", "type": "local", "holder": "ZAFAR YUSUPOV",
        "action": "Перенаправляю к специалисту операционного отдела."
    },
    "9860111222333444": {
        "status": "expired", "response_code": "101",
        "response_text": "Срок действия карты истёк",
        "bank": "Ipoteka Bank", "type": "local", "holder": "SARDOR NAZAROV",
        "action": "Необходимо перевыпустить карту в банке-эмитенте."
    },
    "5614123456789012": {
        "status": "active", "response_code": "000",
        "response_text": "Карта активна",
        "bank": "TBC Bank", "type": "international", "holder": "ASAL JUMANAZAROVA",
        "action": "Перенаправляю в отдел международных карт."
    },
    "5440987654321098": {
        "status": "blocked", "response_code": "119",
        "response_text": "Превышено количество попыток PIN",
        "bank": "Aloqabank", "type": "international", "holder": "BOBUR TASHMATOV",
        "action": "Разблокировка через отделение банка."
    },
}

DEPARTMENTS = {
    "банкомат": "Отдел по работе с банкоматами · номер 201",
    "терминал": "Технический отдел эквайринга · номер 205",
    "pos": "Технический отдел эквайринга · номер 205",
    "транзакция": "Отдел расчётов и транзакций · номер 210",
    "платёж": "Отдел расчётов и транзакций · номер 210",
    "канцелярия": "Канцелярия · номер 100",
    "бухгалтерия": "Бухгалтерия · номер 103",
}

# ==========================================
# TELEGRAM УВЕДОМЛЕНИЯ
# ==========================================
def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def send_missed_call_notification(bank, mfo, caller_name, problem, phone):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    msg = (
        f"🔔 <b>ПРОПУЩЕННЫЙ ЗВОНОК — ТРЕБУЕТ ПЕРЕЗВОНА</b>\n\n"
        f"🏦 <b>Банк:</b> {bank}\n"
        f"🔢 <b>МФО:</b> {mfo}\n"
        f"👤 <b>Сотрудник:</b> {caller_name}\n"
        f"❓ <b>Проблема:</b> {problem}\n"
        f"📱 <b>Номер для перезвона:</b> {phone}\n"
        f"🕐 <b>Время звонка:</b> {now}\n\n"
        f"⚠️ <i>Необходимо перезвонить до конца рабочего дня!</i>"
    )
    return send_telegram(msg)

def send_new_call_notification(bank, mfo, caller_name, problem):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    msg = (
        f"📞 <b>ВХОДЯЩИЙ ЗВОНОК</b>\n\n"
        f"🏦 <b>Банк:</b> {bank}\n"
        f"🔢 <b>МФО:</b> {mfo}\n"
        f"👤 <b>Сотрудник:</b> {caller_name}\n"
        f"❓ <b>Проблема:</b> {problem}\n"
        f"🕐 <b>Время:</b> {now}\n\n"
        f"✅ <i>Звонок маршрутизирован AI</i>"
    )
    return send_telegram(msg)

def send_resolved_notification(bank, problem, result):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    msg = (
        f"✅ <b>РЕШЕНО АВТОМАТИЧЕСКИ</b>\n\n"
        f"🏦 <b>Банк:</b> {bank}\n"
        f"❓ <b>Проблема:</b> {problem}\n"
        f"📋 <b>Результат:</b> {result}\n"
        f"🕐 <b>Время:</b> {now}\n\n"
        f"🤖 <i>Решено AI без участия сотрудника</i>"
    )
    return send_telegram(msg)

# ==========================================
# ПРОВЕРКА КАРТЫ
# ==========================================
def check_card(card_number):
    clean = card_number.replace(" ", "").replace("-", "")
    if clean in CARDS_DB:
        card = CARDS_DB[clean]
        return {"found": True, **card, "card_number": clean}
    if clean.startswith("8600") or clean.startswith("9860"):
        return {"found": False, "type": "local", "message": "Карта не найдена. Перенаправляю к специалисту."}
    elif clean.startswith("5614") or clean.startswith("5440"):
        return {"found": False, "type": "international", "message": "Международная карта не найдена. Перенаправляю в отдел международных карт."}
    return {"found": False, "type": "unknown", "message": "Номер карты не распознан. Перенаправляю к специалисту."}

def format_card_response(card_data):
    if not card_data.get("found"):
        return card_data.get("message", "Карта не найдена.")
    status_map = {"active": "АКТИВНА ✅", "blocked": "ЗАБЛОКИРОВАНА 🔴", "expired": "СРОК ИСТЁК ⚠️"}
    status = status_map.get(card_data["status"], card_data["status"])
    return (
        f"Карта найдена. Держатель: {card_data['holder']}. "
        f"Статус: {card_data['response_text']}, код {card_data['response_code']}. "
        f"{card_data['action']}"
    )

# ==========================================
# API ENDPOINTS
# ==========================================
@app.route('/', methods=['GET'])
def home():
    return jsonify({"service": "SmartRoute · Uzcard AI System", "status": "running", "version": "2.0"})

@app.route('/cards', methods=['GET'])
def list_cards():
    cards = [{"number": n, "status": c["status"], "bank": c["bank"],
              "response_code": c["response_code"], "description": c["response_text"]}
             for n, c in CARDS_DB.items()]
    return jsonify({"test_cards": cards})

@app.route('/check-card', methods=['POST'])
def check_card_endpoint():
    data = request.get_json() or {}
    card_number = data.get('card_number', '')
    if not card_number:
        return jsonify({"error": "Номер карты не указан"}), 400
    card_data = check_card(card_number)
    return jsonify({"card_data": card_data, "message": format_card_response(card_data)})

@app.route('/missed-call', methods=['POST'])
def missed_call():
    data = request.get_json() or {}
    bank = data.get('bank', 'Неизвестно')
    mfo = data.get('mfo', 'Неизвестно')
    caller = data.get('caller_name', 'Неизвестно')
    problem = data.get('problem', 'Неизвестно')
    phone = data.get('phone_number', 'Не указан')
    ok = send_missed_call_notification(bank, mfo, caller, problem, phone)
    return jsonify({"success": ok, "message": "Заявка зарегистрирована. Перезвоним до конца дня."})

@app.route('/new-call', methods=['POST'])
def new_call():
    data = request.get_json() or {}
    ok = send_new_call_notification(
        data.get('bank', '?'), data.get('mfo', '?'),
        data.get('caller_name', '?'), data.get('problem', '?')
    )
    return jsonify({"success": ok})

@app.route('/resolved', methods=['POST'])
def resolved():
    data = request.get_json() or {}
    ok = send_resolved_notification(
        data.get('bank', '?'), data.get('problem', '?'), data.get('result', '?')
    )
    return jsonify({"success": ok})

@app.route('/vapi-webhook', methods=['POST'])
def vapi_webhook():
    data = request.get_json() or {}
    tool_calls = data.get('message', {}).get('toolCalls', [])
    if not tool_calls:
        return jsonify({"results": []})

    results = []
    for tool_call in tool_calls:
        fn = tool_call.get('function', {})
        name = fn.get('name', '')
        args = fn.get('arguments', '{}')
        tool_id = tool_call.get('id', 'unknown')

        if isinstance(args, str):
            try: args = json.loads(args)
            except: args = {}

        if name == 'check_card':
            card_data = check_card(args.get('card_number', ''))
            response_text = format_card_response(card_data)
            # Уведомить в Telegram если решено автоматически
            if card_data.get('found'):
                send_resolved_notification(
                    card_data.get('bank', '?'),
                    'Проверка карты',
                    response_text
                )
            results.append({"toolCallId": tool_id, "result": response_text})

        elif name == 'notify_missed_call':
            ok = send_missed_call_notification(
                args.get('bank', '?'), args.get('mfo', '?'),
                args.get('caller_name', '?'), args.get('problem', '?'),
                args.get('phone_number', 'не указан')
            )
            results.append({"toolCallId": tool_id, "result": "Заявка зарегистрирована. Наш специалист свяжется с вами до конца рабочего дня."})

        elif name == 'notify_new_call':
            send_new_call_notification(
                args.get('bank', '?'), args.get('mfo', '?'),
                args.get('caller_name', '?'), args.get('problem', '?')
            )
            results.append({"toolCallId": tool_id, "result": "ok"})

        else:
            results.append({"toolCallId": tool_id, "result": "Запрос обработан."})

    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

