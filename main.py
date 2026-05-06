from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# ==========================================
# СИМУЛЯЦИЯ БАЗЫ ДАННЫХ UZCARD
# ==========================================
CARDS_DB = {
    "8600123456789012": {
        "status": "blocked",
        "response_code": "818",
        "response_text": "Заблокирована по решению Центрального банка",
        "bank": "Kapitalbank",
        "type": "local",
        "holder": "ALISHER KARIMOV",
        "action": "Обратитесь в Центральный банк Узбекистана для разблокировки."
    },
    "8600987654321098": {
        "status": "active",
        "response_code": "000",
        "response_text": "Карта активна",
        "bank": "Xalq Bank",
        "type": "local",
        "holder": "NILUFAR RASHIDOVA",
        "action": "Карта работает в штатном режиме."
    },
    "8600111222333444": {
        "status": "blocked",
        "response_code": "205",
        "response_text": "Заблокирована банком-эмитентом",
        "bank": "Hamkorbank",
        "type": "local",
        "holder": "ZAFAR YUSUPOV",
        "action": "Перенаправляю к специалисту операционного отдела."
    },
    "9860111222333444": {
        "status": "expired",
        "response_code": "101",
        "response_text": "Срок действия карты истёк",
        "bank": "Ipoteka Bank",
        "type": "local",
        "holder": "SARDOR NAZAROV",
        "action": "Необходимо перевыпустить карту в банке-эмитенте."
    },
    "5614123456789012": {
        "status": "active",
        "response_code": "000",
        "response_text": "Карта активна",
        "bank": "TBC Bank",
        "type": "international",
        "holder": "ASAL JUMANAZAROVA",
        "action": "Карта работает. Перенаправляю в отдел международных карт."
    },
    "5440987654321098": {
        "status": "blocked",
        "response_code": "119",
        "response_text": "Превышено количество попыток PIN",
        "bank": "Aloqabank",
        "type": "international",
        "holder": "BOBUR TASHMATOV",
        "action": "Карта заблокирована из-за 3 неверных PIN. Разблокировка через отделение банка."
    },
}

# Справочник отделов
DEPARTMENTS = {
    "банкомат": "Отдел по работе с банкоматами · внутренний номер 201",
    "терминал": "Технический отдел эквайринга · внутренний номер 205",
    "pos": "Технический отдел эквайринга · внутренний номер 205",
    "транзакция": "Отдел расчётов и транзакций · внутренний номер 210",
    "платёж": "Отдел расчётов и транзакций · внутренний номер 210",
    "международная": "Отдел международных карт · внутренний номер 215",
    "канцелярия": "Канцелярия · внутренний номер 100",
    "бухгалтерия": "Бухгалтерия · внутренний номер 103",
}

def check_card(card_number):
    """Проверить карту в базе Uzcard"""
    # Убираем пробелы и дефисы
    clean_number = card_number.replace(" ", "").replace("-", "")
    
    if clean_number in CARDS_DB:
        card = CARDS_DB[clean_number]
        return {
            "found": True,
            "card_number": clean_number,
            "status": card["status"],
            "response_code": card["response_code"],
            "response_text": card["response_text"],
            "bank": card["bank"],
            "type": card["type"],
            "holder": card["holder"],
            "action": card["action"]
        }
    
    # Если карта не найдена — определяем тип по первым цифрам
    if clean_number.startswith("8600") or clean_number.startswith("9860"):
        return {
            "found": False,
            "card_number": clean_number,
            "type": "local",
            "message": "Карта не найдена в базе Uzcard. Перенаправляю к специалисту."
        }
    elif clean_number.startswith("5614") or clean_number.startswith("5440"):
        return {
            "found": False,
            "card_number": clean_number,
            "type": "international",
            "message": "Международная карта. Перенаправляю в отдел международных карт."
        }
    else:
        return {
            "found": False,
            "card_number": clean_number,
            "type": "unknown",
            "message": "Номер карты не распознан. Перенаправляю к специалисту."
        }

def format_card_response(card_data):
    """Форматировать ответ для AI"""
    if not card_data["found"]:
        return card_data.get("message", "Карта не найдена. Перенаправляю к специалисту.")
    
    status_map = {
        "active": "✅ АКТИВНА",
        "blocked": "🔴 ЗАБЛОКИРОВАНА",
        "expired": "⚠️ ИСТЁК СРОК ДЕЙСТВИЯ"
    }
    
    status_display = status_map.get(card_data["status"], card_data["status"])
    
    response = f"Карта найдена. "
    response += f"Статус: {card_data['response_text']} (код {card_data['response_code']}). "
    response += f"Держатель: {card_data['holder']}. "
    response += card_data["action"]
    
    return response

# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "SmartRoute · Uzcard AI System",
        "status": "running",
        "version": "1.0",
        "endpoints": {
            "check_card": "POST /check-card",
            "get_department": "POST /get-department",
            "vapi_webhook": "POST /vapi-webhook"
        }
    })

@app.route('/check-card', methods=['POST'])
def check_card_endpoint():
    """Проверка карты — вызывается из Vapi"""
    data = request.get_json()
    
    card_number = data.get('card_number', '')
    if not card_number:
        return jsonify({
            "error": "Номер карты не указан",
            "message": "Пожалуйста, назовите номер карты."
        }), 400
    
    card_data = check_card(card_number)
    response_text = format_card_response(card_data)
    
    return jsonify({
        "card_data": card_data,
        "message": response_text,
        "route_to": get_routing(card_data)
    })

def get_routing(card_data):
    """Определить куда маршрутизировать"""
    if not card_data.get("found"):
        return "specialist"
    
    if card_data["status"] == "active":
        return "resolved"
    elif card_data["status"] == "blocked":
        code = card_data.get("response_code", "")
        if code == "818":
            return "central_bank"  # Центральный банк
        else:
            return "specialist"    # Специалист
    else:
        return "specialist"

@app.route('/get-department', methods=['POST'])
def get_department_endpoint():
    """Получить отдел по ключевому слову"""
    data = request.get_json()
    keyword = data.get('keyword', '').lower()
    
    for key, dept in DEPARTMENTS.items():
        if key in keyword:
            return jsonify({
                "department": dept,
                "message": f"Перенаправляю ваш звонок. {dept}. Оставайтесь на линии."
            })
    
    return jsonify({
        "department": "Операционный отдел · внутренний номер 200",
        "message": "Перенаправляю к дежурному специалисту операционного отдела. Оставайтесь на линии."
    })

@app.route('/vapi-webhook', methods=['POST'])
def vapi_webhook():
    """
    Главный webhook для Vapi.
    Vapi вызывает этот endpoint когда нужно проверить карту.
    """
    data = request.get_json()
    
    # Vapi передаёт данные в формате tool call
    tool_call = data.get('message', {}).get('toolCalls', [{}])[0]
    function_name = tool_call.get('function', {}).get('name', '')
    arguments = tool_call.get('function', {}).get('arguments', '{}')
    
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except:
            arguments = {}
    
    tool_call_id = tool_call.get('id', 'unknown')
    
    if function_name == 'check_card':
        card_number = arguments.get('card_number', '')
        card_data = check_card(card_number)
        response_text = format_card_response(card_data)
        
        return jsonify({
            "results": [{
                "toolCallId": tool_call_id,
                "result": response_text
            }]
        })
    
    elif function_name == 'get_department':
        keyword = arguments.get('keyword', '')
        for key, dept in DEPARTMENTS.items():
            if key in keyword.lower():
                return jsonify({
                    "results": [{
                        "toolCallId": tool_call_id,
                        "result": f"Перенаправляю. {dept}. Оставайтесь на линии."
                    }]
                })
        
        return jsonify({
            "results": [{
                "toolCallId": tool_call_id,
                "result": "Перенаправляю к дежурному специалисту. Оставайтесь на линии."
            }]
        })
    
    return jsonify({"results": [{"toolCallId": tool_call_id, "result": "Запрос обработан."}]})

@app.route('/cards', methods=['GET'])
def list_cards():
    """Список тестовых карт для демо"""
    cards_list = []
    for number, info in CARDS_DB.items():
        cards_list.append({
            "number": number,
            "status": info["status"],
            "bank": info["bank"],
            "response_code": info["response_code"],
            "description": info["response_text"]
        })
    return jsonify({
        "test_cards": cards_list,
        "note": "Используйте эти номера для тестирования системы"
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
