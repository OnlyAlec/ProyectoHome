
def sGas(**kwargs):
    # results = [kwargs["Smoke"], kwargs["LPG"],
    #            kwargs["Methane"], kwargs["Hydrogen"]]
    results = kwargs["Methane"]
    if results > 10000:
        action = {
            "function": "buzzerAction", "args": {
                "buzzer": "BUZZER_COCINA", "state": "ON"
            }
        }
        notification = {
            "type": "notification",
            "title": "¡Alerta de Gas!",
            "message": "Se ha detectado una fuga de gas en la cocina."
        }
        return action, {"gas": results, "notification": notification}
    action = {
        "function": "buzzerAction", "args": {
            "buzzer": "BUZZER_COCINA", "state": "OFF"
        }
    }
    return action, {"gas": results}


def sHumedad(**kwargs):
    vAnalog = kwargs["valueAnalog"]
    humedad = 100 - ((vAnalog / 65535) * 100)
    print(f'\t\t◈  Humedad: {humedad}')
    if 15 > humedad > 30:
        notification = {
            "type": "notification",
            "title": "¡Recomedacion sobre Jardin!",
            "message": "Es momento de regar el jardín, la humedad de la tierra esta baja."
        }
        return False, {"humedad": humedad, "notification": notification}
    return False, {"humedad": humedad}


def sRFID(**kwargs):
    card = kwargs["card"]
    print(f'\t\t◈  RFID: {card}')
    if card == 4276175027:
        action = [
            {
                "function": "servoAction",
                "args": {"servo": "SERVO_ENTRADA", "state": "ON"}
            }
        ]
        notification = {
            "type": "notification",
            "title": "¡Notification de entrada!",
            "message": "Se ha detectado un acceso autorizado."
        }
    elif card != "null":
        action = {
            "function": "buzzerAction",
            "args": {"buzzer": "BUZZER_ENTRADA", "state": "ON"}
        }
        notification = {
            "type": "notification",
            "title": "¡Notification de entrada!",
            "message": "Se ha detectado un acceso no autorizado."
        }
        return action, {"RFID": card,  "notification": notification}
    return False, False


def sLuz(**kwargs):
    maxDark = 65535
    minLight = 0
    vAnalog = kwargs["valueAnalog"]

    porcentaje = ((vAnalog - minLight) / (maxDark - minLight)) * 100
    porcentaje = 100 - porcentaje
    porcentaje = max(0, min(100, porcentaje))
    print(f'\t\t◈  Luz: {porcentaje}%')

    if porcentaje < 30:
        action = [
            {
                "function": "ledChange",
                "args": {"led": "LED_HABITACION", "state": "ON"}
            },
            {
                "function": "ledChange",
                "args": {"led": "LED_JARDIN_LUZ", "state": "ON"}
            }
        ]
    else:
        action = [
            {
                "function": "ledChange",
                "args": {"led": "LED_HABITACION", "state": "OFF"}
            },
            {
                "function": "ledChange",
                "args": {"led": "LED_JARDIN_LUZ", "state": "OFF"}
            }
        ]
    return action, {"luz": porcentaje}


def sIR(**kwargs):
    status = kwargs["status"]
    print(f'\t\t◈  IR: {status}')
    if status == "True":
        action = {
            "function": "ledChange",
            "args": {"led": "LED_ENTRADA", "state": "ON"}
        }
        notification = {
            "type": "notification",
            "title": "¡Hay alguien afuera!",
            "message": "Se ha detectado un movimiento en la entrada de la casa."
        }
        return action, {"IR": status, "notification": notification}
    action = {
        "function": "ledChange",
        "args": {"led": "LED_ENTRADA", "state": "OFF"}
    }
    return action, {"IR": status}


def sTemp(**kwargs):
    vAnalog = kwargs["valueAnalog"]
    conversionFactor = 3.3 / (65535)
    v = vAnalog * conversionFactor
    temp = 27 - (v - 0.706)/0.001721
    print(f'\t\t◈  Temperatura: {temp}')
    if temp >= 30:
        notification = {
            "type": "notification",
            "title": "¡Recomedacion de Temperatura!",
            "message": "Lleva ropa ligera, la temperatura del dia de hoy es alta."
        }
        return False, {"temperatura": temp,  "notification": notification}
    if temp <= 20:
        notification = {
            "type": "notification",
            "title": "¡Recomedacion de Temperatura!",
            "message": "Está haciendo mucho frío, no olvides abrigarte al salir."
        }
        return False, {"temperatura": temp,  "notification": notification}
    return False, {"temperatura": temp}
