# ============================================================
#  bot.py — Entry point del bot
# ============================================================

import asyncio
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from database import init_economy_db, UserEconomy

load_dotenv()

# ── Intents ───────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_message(message):
    # Procesamos los comandos aquí de forma centralizada para evitar duplicados.
    # Los listeners de los cogs (como el de protección de menciones) se ejecutarán en paralelo.
    await bot.process_commands(message)


async def main():
    # Inicializar la base de datos de economía
    eco_conn, eco_cursor = init_economy_db()
    economy = UserEconomy(eco_conn, eco_cursor)

    async with bot:
        print("[STARTUP] Cargando cogs...")
        # Cargar todos los cogs manualmente (pasando economy cuando es necesario)

        # Cogs que necesitan economy
        from cogs.events      import setup as setup_events
        from cogs.general     import setup as setup_general
        from cogs.economy     import setup as setup_economy
        from cogs.casino      import setup as setup_casino
        from cogs.moderation  import setup as setup_moderation
        from cogs.games       import setup as setup_games
        from cogs.tickets     import setup as setup_tickets
        from cogs.fun         import setup as setup_fun

        await setup_events(bot, economy)
        await setup_general(bot, economy)
        await setup_economy(bot, economy)
        await setup_casino(bot, economy)
        await setup_moderation(bot, economy)
        await setup_games(bot, economy)
        await setup_tickets(bot)
        await setup_fun(bot)
        print("[STARTUP] Todos los cogs cargados correctamente.")

        # Token desde variable de entorno (.env o sistema)
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("[ERROR] No se encontró DISCORD_TOKEN. Crea un archivo .env con tu token.")
            return
        print("[STARTUP] Iniciando sesión en Discord...")
        
        try:
            await bot.start(token)
        except discord.errors.LoginFailure:
            print("[ERROR] El Token de Discord es inválido. Revisa tus variables de entorno.")
        except Exception as e:
            print(f"[ERROR] No se pudo iniciar el bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())