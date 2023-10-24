# —LEER SENSOR LM35 para la pico---
import datetime
from firebase_admin import db, credentials, initialize_app


# ——Guardar datos en Realtime database para la pi 4————

# Inicializa Firebase con las credenciales
cred = credentials.Certificate('path a las credenciales.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://casaiot-ff526-default-rtdb.firebaseio.com/'
})

# Obtiene una referencia a la raíz de la base de datos
ref = db.reference('Registros_temp/')


def guardar_temperatura(temperatura):
    # Obtiene el timestamp actual como una cadena en formato ISO
    timestamp = datetime.datetime.now().isoformat()

    # Crea una nueva entrada en la base de datos
    ref.child(timestamp).set({
        'temperatura': temperatura
    })

# falta la llamada a la función como cada 10 seg aprox y el código que reciba la temperatura por wifi
