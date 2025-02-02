# 🤖 Bot de Discord - EjemploBot 🎉

## 📌 Descripción
EjemploBot es un bot para Discord con múltiples funcionalidades, incluyendo administración, juegos y sistema de tickets. 🎮⚙️

## 🚀 Características
✅ Bienvenida a nuevos miembros.
✅ Sistema de tickets.
✅ Comandos de administración.
✅ Juegos y comandos de entretenimiento.
✅ Sistema de advertencias y sugerencias.

## 🛠️ Requisitos
🔹 Python 3.8 o superior.
🔹 Librerías necesarias:
  ```sh
  pip install discord.py
  ```

## 📥 Instalación
1️⃣ Clona el repositorio:
   ```sh
   git clone https://github.com/tuusuario/tu-repositorio.git
   cd tu-repositorio
   ```
2️⃣ Instala las dependencias:
   ```sh
   pip install -r requirements.txt
   ```
3️⃣ Configura las variables de entorno o edita el archivo para agregar el token de tu bot.
4️⃣ 🔍 Revisa el código y asegúrate de añadir las configuraciones necesarias, como `Bearer tokens` u otros ajustes personalizados.
5️⃣ Ejecuta el bot:
   ```sh
   python Bot.py
   ```

## 🏗️ Configuración de los ID de canales
📌 En el código del bot, varios identificadores de canales y roles deben configurarse correctamente para que las funcionalidades trabajen según lo esperado. Estos identificadores son:

🔹 `WELCOME_CHANNEL_ID` → Canal donde se envían los mensajes de bienvenida a los nuevos miembros.
🔹 `TICKET_CATEGORY_ID` → Categoría donde se crean los canales de tickets.
🔹 `MOD_ROLE_ID` → Rol de moderador, necesario para comandos administrativos.
🔹 `CANAL_SUGERENCIAS_ID` → Canal donde los usuarios pueden enviar sugerencias.
🔹 `WARN_CHANNEL_ID` → Canal donde se registran las advertencias enviadas a los usuarios.

🛑 **IMPORTANTE:** Estos valores deben reemplazarse con los ID reales de tu servidor de Discord para que el bot funcione correctamente. Además, revisa el código para asegurarte de que todos los permisos y configuraciones necesarias están correctamente implementados.

## 🎮 Uso
📜 Los comandos del bot incluyen:
- `!ping` 🏓 - Muestra la latencia del bot.
- `!info` ℹ️ - Información sobre el bot.
- `!redes` 🌐 - Muestra redes sociales.
- `!ticket` 🎟️ - Sistema de soporte mediante tickets.
- `!warn @usuario [razón]` ⚠️ - Agrega una advertencia a un usuario.
- `!historial @usuario` 📜 - Muestra advertencias de un usuario.

## 🤝 Contribución
Si deseas contribuir, haz un fork del repositorio y envía un pull request. 🛠️✨

## 📜 Licencia
📄 Este proyecto está bajo la licencia **MIT**.

