# ============================================================
#  cogs/events.py — Eventos del bot
# ============================================================

import discord
from discord.ext import commands, tasks
from datetime import datetime
from database import UserEconomy
from config import (
    WELCOME_CHANNEL_ID, ROLES_IDS,
    USER_ID_NO_MENCIONAR, MOD_ROLE_ID,
    BOT_STREAMING_NAME, BOT_STREAMING_URL,
    SERVER_NAME, WELCOME_IMAGE_URL, SERVER_LOGO_URL,
)


class Events(commands.Cog):
    """Maneja todos los eventos del bot."""

    def __init__(self, bot: commands.Bot, economy: UserEconomy):
        self.bot     = bot
        self.economy = economy

    # ── on_ready ──────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ {self.bot.user.name} ha iniciado sesión.")
        await self.bot.change_presence(
            activity=discord.Streaming(
                name=BOT_STREAMING_NAME,
                url=BOT_STREAMING_URL
            )
        )
        self.check_monthly_winner.start()

    # ── on_command_error ──────────────────────────────────────
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        # Ignorar errores de comprobación (ya manejados en los cogs)
        if isinstance(error, commands.CheckFailure):
            return

        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Comando no encontrado. Usa `!ayuda` para ver los disponibles.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ No tienes permisos para usar este comando.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Argumentos faltantes. Revisa la sintaxis del comando.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Argumento inválido. Revisa la sintaxis del comando.")
        else:
            await ctx.send("❌ Ha ocurrido un error inesperado.")
            print(f"[ERROR] {error}")

    # ── on_member_join ────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        try:
            roles = [
                role for role_id in ROLES_IDS
                if (role := member.guild.get_role(role_id)) is not None
            ]
            if roles:
                await member.add_roles(*roles)
                print(f"[INFO] Roles añadidos a {member.name}.")

            channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
            if channel:
                await channel.send(f"**¿Qué te trae por aquí {member.mention}?**")
                avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
                embed = discord.Embed(
                    title=f"¡Bienvenido a {SERVER_NAME}!",
                    description=(
                        f"¡Nos alegra tenerte con nosotros, {member.name}!\n\n"
                        "- No olvides leer las reglas y pasar por los canales "
                        "de presentación para conocerte mejor con los demás."
                    ),
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=avatar_url)
                if WELCOME_IMAGE_URL:
                    embed.set_image(url=WELCOME_IMAGE_URL)
                await channel.send(embed=embed)
        except Exception as e:
            print(f"[ERROR] Bienvenida de {member.name}: {e}")

    # ── on_message ────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Protección: nadie puede mencionar al usuario protegido (salvo mods)
        if str(USER_ID_NO_MENCIONAR) in [str(u.id) for u in message.mentions]:
            mod_role = message.guild.get_role(MOD_ROLE_ID) if message.guild else None
            if not (mod_role and mod_role in message.author.roles):
                try:
                    await message.delete()
                except discord.NotFound:
                    pass

                embed = discord.Embed(
                    title="⚠️ Mensaje Eliminado",
                    description=(
                        "Motivo: \nNo puedes mencionar a este usuario. \n"
                        "Por favor, no lo vuelvas a repetir."
                    ),
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Servidor: {SERVER_NAME}")
                if SERVER_LOGO_URL:
                    embed.set_thumbnail(url=SERVER_LOGO_URL)
                try:
                    await message.author.send(embed=embed)
                except discord.Forbidden:
                    await message.channel.send(
                        f"{message.author.mention}, no puedes mencionar a este usuario. "
                        "Tu mensaje ha sido eliminado.",
                        delete_after=10
                    )

    # ── on_disconnect ─────────────────────────────────────────
    @commands.Cog.listener()
    async def on_disconnect(self):
        print("[INFO] Bot desconectado. Esperando reconexión...")

    # ── Tarea mensual ─────────────────────────────────────────
    @tasks.loop(hours=24)
    async def check_monthly_winner(self):
        now = datetime.now()
        if now.day != 1:
            return

        current_month = f"{now.year}-{now.month}"
        row = self.economy.get_task_state("monthly_winner")
        if row and row[0] == current_month:
            return  # Ya se procesó este mes

        # Reiniciar todos los balances
        self.economy.reset_all_balances()
        self.economy.set_task_state("monthly_winner", current_month)
        print(f"[INFO] Economía reseteada para {current_month}.")


    @check_monthly_winner.before_loop
    async def before_check_monthly_winner(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot, economy: UserEconomy):
    await bot.add_cog(Events(bot, economy))
