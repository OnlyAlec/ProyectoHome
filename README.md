
<div align='center'>
  <a>
    <img src="https://raw.githubusercontent.com/EduardoCC-bot/App_IoT/main/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png" alt="Icon">
  </a>
  <h1>❰ 𝙄𝙤𝙩 𝙃𝙤𝙢𝙚 ❱</h1>
</div>


# Acerca del proyecto

Home IoT es un proyecto queconsiste en el desarrollo de una casa inteligente a escala mediante el uso de componentes electrónicos fácilmente accesibles disponiendo de una aplicación que permite controlar dispositivos como luces, alarmas y motores, además, está equipada con sensores de humedad, temperatura, gas y luz que posibilitan la automatización de acciones específicas en la casa, como el encendido de una alarma.

El objetivo es proporcionar una plataforma para experimentar y aprender sobre la implementación de la Internet de las cosas (IoT) en un entorno doméstico implementando adaptatividad de espacios sin tener algún limite. De igual forma se busco integrar los conocimientos obtenidos en las materias de: Sistemas Operativos, Bases de Datos, Microcontroladores y Comunicación de Datos.

La ejecución del proyecto se realizo usando una Raspberry Pi Pico W y dos Raspberry Pi 4 Modelo
B, cada una de ellas ejecuta operaciones particulares referentes al control y monitoreo de la casa, esta
característica refleja el concepto de “multiprocesamiento”, un término que plantea que distintas partes
que conforman a un sistema realizan tareas específicas de forma simultánea o independiente.
Sin embargo, es posible realizar el proyecto usando únicamente Raspberry Pi Pico W ya que se puede adaptar el código para aprovechar la funcionalidad de la conexión a una red de la Raspberry para conectarse directamente a la API.

---

# Contenido del Repositorio
Este repositorio contiene la **API** que facilita la comunicación entre la Raspberry Pi y las bases de datos, así como la programación relacionada con los **sensores, LEDs y servo motores** que emplea la Raspberry Pi Pico W.
SI quieres consultar el código de la **aplicación** desarrollada con Dart, ve el siguiente [repositorio](https://github.com/EduardoCC-bot/App_IoT).

### Estructuración del archivos
- `API/`: Carpeta con todo lo relacionada con la API.
- `HomeSensors/`: Carpeta relacionada con la programación de los componentes electrónicos.
	- `PICO/`: Carpeta relacionada con la obtención de datos usando la Raspberry Pi Pico W.
	- `RPI/`: Carpeta relacionada con el procesamiento de datos obtenidos.
	- `backup/`: Carpeta de respaldo
	- `util/`: Carpeta con códigos de prueba para algunos componentes.
- `SQL/`: Carpeta con algunos querys que se usaron en la base de datos.
- `.vscode/`: Carpeta para el IDE Visual Studio Code.

### Tecnologías Utilizadas
- **Python**: Lenguaje principal para el proyecto principalmente se ocupa en lo relacionado con la API.
- **Micropython**: Siendo una versión compacta de Python se usa para la interacción con los sensores y componentes electrónicos.
- **Flask, Gunicorn, Ngrok**: Utilizado para la creación de un servidor web HTTP exponiendo la API a Internet.

---

# Arquitectura del proyecto
### Diagrama de conexión
![Diagrama de conexión](https://i.imgur.com/o3yuL9J.png)

### Diagrama de actividades (Resumido)
![Diagrama de Actividades](https://i.imgur.com/s1hrXoJ.png)

---

# Contribuciones

¡Las contribuciones son bienvenidas! Si tienes sugerencias, problemas o mejoras, por favor crea un _issue_ o envía una _pull request_.

# Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](https://chat.openai.com/c/LICENSE.md) para detalles.

