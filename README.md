# 🤖 **DiscordBot - Bot Multifuncional para Discord**  

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)  
[![Discord.py](https://img.shields.io/badge/discord.py-2.0+-purple?logo=discord)](https://discordpy.readthedocs.io/)  
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)  

Un bot todo-en-uno para comunidades de Discord con sistema de economía, moderación, tickets y entretenimiento.  

## ✨ **Características**  

| Módulo         | Funcionalidades                                                                 |
|----------------|---------------------------------------------------------------------------------|
| **🎉 Bienvenida** | Roles automáticos • Mensajes personalizados • Embeds con imágenes               |
| **💰 Economía**   | Banco SQLite • Trabajos • Tienda • Robos • Apuestas • Hall of Fame mensual      |
| **🛡️ Moderación** | Warns • Anti-mentions • Limpieza de chat • Registro de infracciones             |
| **🎟️ Tickets**    | Sistema interactivo • Categorías dedicadas • Cierre automático                  |
| **🎮 Diversión**  | 8-Ball • Ruleta • Tragamonedas • Memes • Piedra/Papel/Tijeras                  |

## 🚀 **Instalación**  

1. **Clona el repositorio:**  
```bash
git clone https://github.com/J-Uriol/DiscordBot.git
cd DiscordBot
```

2. **Instala dependencias:**  
```bash
pip install -r requirements.txt
```

3. **Configura el bot:**  
Edita `config.py` con tus IDs de Discord:  
```python
TOKEN = "tu_token_de_bot"
WELCOME_CHANNEL_ID = 123456789
TICKET_CATEGORY_ID = 987654321
# ... (ver archivo completo)
```

4. **Inicia el bot:**  
```bash
python bot.py
```

## 📸 **Capturas**  

| Bienvenida Automática | Sistema de Tickets |  
|-----------------------|--------------------|  
| ![Welcome](https://i.imgur.com/welcome.png) | ![Tickets](https://i.imgur.com/tickets.png) |  

| Economía | Moderación |  
|----------|------------|  
| ![Economy](https://i.imgur.com/economy.png) | ![Mod](https://i.imgur.com/mod.png) |  

## ⚙️ **Estructura del Proyecto**  

```bash
.
├── bot.py                # Código principal del bot
├── config.py             # Configuración (token, IDs)
├── economy.db            # Base de datos SQLite (automática)
├── README.md             # Este archivo
└── requirements.txt      # Dependencias
```

## 🌟 **Comandos Destacados**  

```bash
!daily       # Reclama monedas diarias
!work        # Gana dinero trabajando
!shop        # Tienda de artículos
!ticket      # Abre un ticket de soporte
!warn @user  # Advertencia a usuarios
!roulette    # Juega a la ruleta
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

---

<p align="center">
  ⭐ <strong>Dale una estrella si te gustó el proyecto</strong> ⭐
</p>

---

### 🔗 **Enlaces Útiles**  
[📚 Documentación de discord.py](https://discordpy.readthedocs.io/) •  
[🐛 Reportar Issues](https://github.com/tu-usuario/DiscordBot/issues)  

---

✨ **Hecho con Python y ❤️ para comunidades de Discord**
