# ============================================================
#  cogs/general.py — Comandos generales
# ============================================================

import asyncio
import discord
from discord.ext import commands
from discord.ui import Button, View
from database import UserEconomy


# ── Lista de comandos para !ayuda ─────────────────────────────
COMANDOS = {
    "General": [
        ("!ping",        "Comprueba si el bot está online y muestra la latencia."),
        ("!info",        "Muestra información sobre el bot."),
        ("!stats",       "Muestra las estadísticas del servidor."),
        ("!userinfo",    "Muestra información detallada de un usuario."),
        ("!redes",       "Muestra los enlaces y redes del servidor."),
        ("!recordar",    "Recordatorio personal (ej: !recordar 10m descansar)."),
        ("!encuesta",    "Crea una encuesta interactiva con botones."),
    ],
    "Economía": [
        ("!balance [usuario]",          "Muestra el balance de un usuario."),
        ("!daily",                      "Reclama tu recompensa diaria de monedas."),
        ("!work",                       "Trabaja para ganar monedas."),
        ("!deposit <cantidad|all>",      "Mueve monedas de la cartera al banco."),
        ("!withdraw <cantidad|all>",     "Saca monedas del banco a la cartera."),
        ("!transfer @usuario cantidad", "Transfiere monedas a otro usuario."),
        ("!gift @usuario cantidad",     "Regala monedas a otro usuario."),
        ("!steal @usuario",             "Intenta robar monedas a otro usuario."),
        ("!leaderboard",                "Ranking de usuarios con más monedas."),
        ("!pesca",                      "Lanza la caña (cooldown 20 min)."),
        ("!trivia",                     "Responde preguntas para ganar monedas."),
    ],
    "Casino": [
        ("!coinflip cantidad",          "Apuesta en cara o cruz."),
        ("!slots cantidad",             "Juega a las tragamonedas."),
        ("!roulette cantidad color",    "Apuesta a rojo o negro en la ruleta."),
        ("!blackjack cantidad",         "Juega al blackjack contra el bot."),
        ("!dados @usuario cantidad",    "Duelo de dados contra otro usuario."),
        ("!minas cantidad",             "Juego de minas con multiplicador."),
        ("!rasca cantidad",             "Rasca y gana premios."),
        ("!carrera cantidad",           "Apuesta en una carrera de caballos."),
    ],
    "Diversión": [
        ("!moneda",        "Tira una moneda (cara o cruz)."),
        ("!suerte",        "Pregunta a la bola mágica."),
        ("!memide",        "El bot te dice cuánto te mide, aleatoriamente."),
        ("!rps",           "Piedra, papel o tijera contra el bot."),
        ("!ship @usuario", "Calcula la compatibilidad amorosa con otro usuario."),
    ],
    "Administración": [
        ("!warn @usuario motivo",  "Advierte a un usuario y notifica por DM."),
        ("!historial @usuario",    "Historial de warns de un usuario."),
        ("!clear cantidad",        "Borra mensajes del canal."),
        ("!purgar @usuario",       "Purga spam y silencia al usuario 3 días."),
        ("!say mensaje",           "El bot repite el mensaje."),
        ("!addmoney @u cantidad",  "Añade monedas a un usuario."),
        ("!removemoney @u cant.",  "Elimina monedas de un usuario."),
        ("!ticket",                "Publica el panel de tickets."),
        ("!verificar_roles",       "Asigna roles automáticos a todos los miembros."),
    ],
}

PAGES = ["Home", "General", "Economía", "Casino", "Diversión", "Administración"]


class General(commands.Cog):
    """Comandos generales de información y diversión."""

    def __init__(self, bot: commands.Bot, economy: UserEconomy):
        self.bot     = bot
        self.economy = economy

    # ── !ping ─────────────────────────────────────────────────
    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Muestra la latencia del bot."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"{ctx.author.mention} Pong 🏓 Latencia: {latency} ms.")

    # ── !redes ────────────────────────────────────────────────
    @commands.command(name="redes")
    async def redes(self, ctx: commands.Context):
        """Muestra los enlaces del servidor."""
        from config import SERVER_NAME, SERVER_LOGO_URL
        embed = discord.Embed(
            title=f"Redes y enlaces de {SERVER_NAME}",
            description="Aquí puedes encontrar todos nuestros enlaces oficiales:",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"¡Gracias por tu apoyo, {ctx.author.name}!")
        if SERVER_LOGO_URL:
            embed.set_thumbnail(url=SERVER_LOGO_URL)
        await ctx.send(embed=embed)

    # ── !info ─────────────────────────────────────────────────
    @commands.command(name="info")
    async def info(self, ctx: commands.Context):
        """Muestra información sobre el bot."""
        from config import SERVER_NAME
        embed = discord.Embed(
            title="Información sobre el bot",
            description=f"Soy el bot oficial de {SERVER_NAME}. 😄",
            color=discord.Color.orange()
        )
        embed.add_field(name="Creador",          value="jav1ermzn",    inline=False)
        embed.add_field(name="Versión",          value="2.0.0",         inline=False)
        embed.add_field(name="Fecha de creación", value="Enero 2025",  inline=False)
        embed.set_footer(text="¡Gracias por ser parte de nuestra comunidad! 🌟")
        await ctx.send(embed=embed)

    # ── !pc (eliminado — era específico del Youtuber) ───────────────────────────────────

    # ── !userinfo ─────────────────────────────────────────────
    @commands.command(name="userinfo", aliases=["ui"])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Muestra información detallada de un usuario."""
        member = member or ctx.author
        balance = self.economy.get_balance(member.id)
        bank    = self.economy.get_bank_balance(member.id)
        warns   = self.economy.count_warns(member.id)

        roles = [role.mention for role in member.roles[1:]]  # Excluir @everyone
        roles_str = " ".join(roles) if roles else "Ninguno"

        embed = discord.Embed(title=f"👤 Info de Usuario: {member.name}", color=member.color)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        embed.add_field(name="🆔 ID",            value=str(member.id), inline=True)
        embed.add_field(name="🏷️ Nickname",      value=member.display_name, inline=True)
        embed.add_field(name="📅 Cuenta creada",  value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📥 Unido al server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="💰 Cartera",       value=f"{balance:,} monedas", inline=True)
        embed.add_field(name="🏦 Banco",         value=f"{bank:,} monedas", inline=True)
        embed.add_field(name="⚠️ Warns",         value=str(warns), inline=True)
        embed.add_field(name="🎭 Roles",         value=roles_str, inline=False)
        
        await ctx.send(embed=embed)

    # ── !serverinfo ───────────────────────────────────────────
    @commands.command(name="serverinfo", aliases=["si"])
    async def serverinfo(self, ctx: commands.Context):
        """Muestra información detallada del servidor."""
        guild = ctx.guild
        embed = discord.Embed(title=f"🏰 {guild.name}", color=discord.Color.orange())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="🆔 ID",            value=str(guild.id), inline=True)
        embed.add_field(name="👑 Dueño",         value=str(guild.owner), inline=True)
        embed.add_field(name="📅 Creado el",      value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=True)
        embed.add_field(name="👥 Miembros",      value=str(guild.member_count), inline=True)
        embed.add_field(name="💬 Canales",       value=f"Texto: {len(guild.text_channels)}\nVoz: {len(guild.voice_channels)}", inline=True)
        embed.add_field(name="🚀 Boosts",        value=f"Nivel {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
        
        await ctx.send(embed=embed)

    # ── !stats (alias de serverinfo) ──────────────────────────
    @commands.command(name="stats")
    async def stats(self, ctx: commands.Context):
        """Muestra las estadísticas del servidor."""
        await self.serverinfo(ctx)

    # ── !recordar ─────────────────────────────────────────────
    @commands.command(name="recordar", aliases=["remindme", "r"])
    async def recordar(self, ctx: commands.Context, tiempo: str, *, recordatorio: str):
        """Establece un recordatorio personal."""
        unit = tiempo[-1].lower()
        try:
            val = int(tiempo[:-1])
        except ValueError:
            await ctx.send("❌ Formato inválido. Usa por ejemplo: `10m`, `1h`, `30s`.")
            return

        seconds = 0
        if unit == "s": seconds = val
        elif unit == "m": seconds = val * 60
        elif unit == "h": seconds = val * 3600
        else:
            await ctx.send("❌ Unidad no válida. Usa `s` (segundos), `m` (minutos) o `h` (horas).")
            return

        if seconds > 86400: # 24h max
            await ctx.send("❌ El recordatorio no puede superar las 24 horas.")
            return

        await ctx.send(f"✅ Vale {ctx.author.mention}, te recordaré: **{recordatorio}** en `{tiempo}`.")
        await asyncio.sleep(seconds)
        
        try:
            embed = discord.Embed(
                title="⏰ ¡Recordatorio!",
                description=f"Hola {ctx.author.mention}, me pediste que te recordara:\n**{recordatorio}**",
                color=discord.Color.gold()
            )
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(f"⏰ {ctx.author.mention}, ¡aquí está tu recordatorio!: **{recordatorio}** (No pude enviarte un MD).")

    # ── !encuesta ─────────────────────────────────────────────
    @commands.command(name="encuesta", aliases=["poll"])
    async def encuesta(self, ctx: commands.Context, pregunta: str, *opciones):
        """Crea una encuesta rápida con botones."""
        if len(opciones) < 2:
            await ctx.send("❌ Debes dar al menos 2 opciones. Ej: `!encuesta \"¿Qué comemos?\" Pizza Hamburguesa`")
            return
        if len(opciones) > 5:
            await ctx.send("❌ El máximo de opciones es 5.")
            return

        embed = discord.Embed(
            title="📊 Encuesta",
            description=f"**{pregunta}**\n\n" + "\n".join([f"🔹 {opt}" for opt in opciones]),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Encuesta creada por {ctx.author.display_name}")

        view = View(timeout=None)
        votos = {opt: 0 for opt in opciones}
        usuarios_votaron = set()

        for opt in opciones:
            btn = Button(label=opt, style=discord.ButtonStyle.secondary)

            async def callback(interaction: discord.Interaction, o=opt):
                if interaction.user.id in usuarios_votaron:
                    await interaction.response.send_message("❌ Ya has votado en esta encuesta.", ephemeral=True)
                    return
                
                usuarios_votaron.add(interaction.user.id)
                votos[o] += 1
                
                # Actualizar embed
                new_desc = f"**{pregunta}**\n\n"
                for k, v in votos.items():
                    new_desc += f"🔹 {k}: **{v} votos**\n"
                
                embed.description = new_desc
                await interaction.response.edit_message(embed=embed)

            btn.callback = callback
            view.add_item(btn)

        await ctx.send(embed=embed, view=view)

    # ── !ayuda ────────────────────────────────────────────────
    @commands.command(name="ayuda", aliases=["help", "h"])
    async def ayuda(self, ctx: commands.Context):
        """Muestra el menú de ayuda interactivo."""
        from config import SERVER_NAME, SERVER_LOGO_URL
        
        def build_embed(category: str) -> discord.Embed:
            if category == "Home":
                embed = discord.Embed(
                    title=f"🚀 Bot de {SERVER_NAME} — Menú de Ayuda",
                    description=(
                        "¡Bienvenido al sistema de ayuda interactivo!\n\n"
                        f"Soy el bot oficial de **{SERVER_NAME}**, diseñado para gestionar la "
                        "economía, diversión y moderación del servidor.\n\n"
                        "💡 **Usa el menú desplegable de abajo** para explorar los comandos.\n\n"
                        "📌 **Prefijo:** `!`\n"
                        "🔗 **Redes:** `!redes`"
                    ),
                    color=discord.Color.gold()
                )
                if SERVER_LOGO_URL:
                    embed.set_thumbnail(url=SERVER_LOGO_URL)
                
                guild_stats = f"Miembros: {ctx.guild.member_count}" if ctx.guild else "Disponible en MD"
                embed.add_field(name="📊 Estadísticas", value=f"{guild_stats}\nCategorías: {len(COMANDOS)}", inline=True)
                embed.set_footer(text="Desarrollado con ❤️ por jav1ermzn")
                return embed

            embed = discord.Embed(
                title=f"📂 Categoría: {category}",
                description=f"Aquí tienes los comandos disponibles en **{category}**:",
                color=discord.Color.orange()
            )
            if SERVER_LOGO_URL:
                embed.set_thumbnail(url=SERVER_LOGO_URL)
            
            cmd_list = COMANDOS.get(category, [])
            if cmd_list:
                val = "\n".join(f"`{cmd}`: {desc}" for cmd, desc in cmd_list)
                embed.add_field(name="Lista de Comandos", value=val, inline=False)
            
            embed.set_footer(text=f"Solicitado por {ctx.author.name} | Total: {len(cmd_list)} comandos")
            return embed

        class HelpDropdown(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label="Inicio",          description="Volver a la página principal",  emoji="🏠", value="Home"),
                    discord.SelectOption(label="General",         description="Info, recordatorios, encuestas", emoji="📋", value="General"),
                    discord.SelectOption(label="Economía",        description="Balance, trabajo, robos...",     emoji="💰", value="Economía"),
                    discord.SelectOption(label="Casino",          description="Apuestas y juegos de azar",      emoji="🎰", value="Casino"),
                    discord.SelectOption(label="Diversión",       description="Minijuegos y entretenimiento",   emoji="🎮", value="Diversión"),
                    discord.SelectOption(label="Administración",  description="Moderación y gestión",          emoji="🛠️", value="Administración"),
                ]
                super().__init__(placeholder="Selecciona una categoría...", min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("No puedes usar este menú.", ephemeral=True)
                    return
                await interaction.response.edit_message(embed=build_embed(self.values[0]))

        view = View(timeout=180)
        view.add_item(HelpDropdown())
        await ctx.send(embed=build_embed("Home"), view=view)


async def setup(bot: commands.Bot, economy: UserEconomy):
    await bot.add_cog(General(bot, economy))
