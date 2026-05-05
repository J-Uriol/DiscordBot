# 🤖 **DiscordBot — Bot Multifuncional para Discord**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.4+-purple?logo=discord)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Un bot todo-en-uno para comunidades de Discord con sistema de economía, moderación, tickets y entretenimiento.

## ✨ **Características**

| Módulo | Funcionalidades |
|---|---|
| **🎉 Bienvenida** | Roles automáticos • Mensajes personalizados • Embeds configurables |
| **💰 Economía** | Banco SQLite • Trabajos • Robos • Apuestas • Hall of Fame mensual |
| **🛡️ Moderación** | Warns • Anti-menciones • Limpieza de chat • Registro de infracciones |
| **🎟️ Tickets** | Sistema interactivo • Categorías dedicadas • Cierre automático |
| **🎮 Diversión** | 8-Ball • Ruleta • Tragamonedas • Memes • Piedra/Papel/Tijeras |

## 🚀 **Instalación**

### 1. Clona el repositorio

```bash
git clone https://github.com/J-Uriol/DiscordBot.git
cd DiscordBot
```

### 2. Instala dependencias

```bash
pip install -r requirements.txt
```

### 3. Configura las variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus valores:

```env
DISCORD_TOKEN=tu_token_aqui

WELCOME_CHANNEL_ID=123456789
WARN_CHANNEL_ID=123456789
ECO_CHANNEL_ID=123456789

TICKET_CATEGORY_ID=123456789
MOD_ROLE_ID=123456789
ROLES_IDS=111111111,222222222

USER_ID_NO_MENCIONAR=

BOT_STREAMING_NAME=Mi Bot
BOT_STREAMING_URL=https://www.twitch.tv/tu_canal

SERVER_NAME=Mi Servidor
WELCOME_IMAGE_URL=https://example.com/banner.jpg
SERVER_LOGO_URL=https://example.com/logo.jpg

DAILY_AMOUNT=200
WORK_MIN=100
WORK_MAX=500
```

> ⚠️ **Nunca subas tu archivo `.env` a GitHub.** Ya está incluido en `.gitignore`.

### 4. Inicia el bot

```bash
python bot.py
```

## 🌟 **Comandos Destacados**

```bash
!daily            # Reclama monedas diarias
!work             # Gana dinero trabajando
!shop             # Tienda de artículos
!warn @user       # Advertencia a usuarios
!roulette         # Juega a la ruleta
!ping             # Verifica la latencia con el bot
!ayuda            # Menú de ayuda interactivo
```

## 🤝 **Contribuir**

¡Se aceptan PRs! Sigue estos pasos:
1. Haz fork del proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcion`)
3. Haz commit (`git commit -m "Añade X función"`)
4. Haz push (`git push origin feature/nueva-funcion`)
5. Abre un Pull Request

## 📜 **Licencia**

MIT © 2025 Javier Uriol (https://github.com/J-Uriol)

## 📬 **Contacto**

Si tienes dudas, sugerencias o quieres reportar un bug, contáctame por Discord:

**Discord:** `jav1ermzn`

---

<p align="center">
  ⭐ <strong>Dale una estrella si te gustó el proyecto</strong> ⭐
</p>

---

### 🔗 **Enlaces Útiles**
[📚 Documentación de discord.py](https://discordpy.readthedocs.io/)

---

✨ **Hecho con Python y ❤️ para comunidades de Discord**
