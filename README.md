# **📋 Lista Bot (Telegram)**

Un bot de Telegram minimalista y eficiente para gestionar listas compartidas en grupos o canales. Cada chat mantiene su propia lista independiente persistente.

## **🚀 Funcionalidades**

* **Persistencia:** Las listas se guardan en una base de datos SQLite local (/data/lists.db).  
* **Aislamiento:** Cada grupo/chat tiene su propia lista.  
* **Dockerizado:** Listo para desplegar en cualquier VPS con Docker Compose.

## **🤖 Comandos**

* `/add \<texto\>`: Añade un nuevo elemento al final de la lista.  
* `/del \<número\>`: Elimina el elemento en la posición indicada.  
* `/lista`: Muestra todos los elementos numerados.  
* `/reset \<item1\>, \<item2\>`: Borra la lista actual y crea una nueva con los elementos separados por comas.

## **🛠️ Despliegue Rápido**

### **Requisitos**

* Docker  
* Docker Compose

### **Pasos**

1. **Clona el repositorio:**
   ```
   git clone https://github.com/javilopezg/nuestralistabot.git
   cd nuestralistabot
   ```
2. Configura el entorno:  
   Crea un archivo .env en la raíz con tu token de BotFather:  
   ```
   TELEGRAM\_TOKEN=123456:ABC-DEF...
   ```
4. **Arranca el servicio:**  
   ```
   docker compose up \-d \--build
   ```
## **📂 Estructura del Proyecto**
```
.  
├── main.py            \# Lógica del bot y gestión de SQLite  
├── Dockerfile         \# Definición de la imagen Python  
├── docker-compose.yml \# Orquestación del contenedor  
├── requirements.txt   \# Dependencias (python-telegram-bot)  
└── data/              \# Volumen persistente para la BBDD
```
## **credits / autoría**

* **Código e Intelecto Artificial:** [Gemini](https://google.com) (Google).  
* **Mecanismo de Despliegue Biológico:** Javi.

*Este código fue generado por una IA bajo la supervisión de un humano que sabe copiar y pegar comandos de terminal muy bien.*
