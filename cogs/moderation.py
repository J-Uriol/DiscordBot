# ============================================================
#  cogs/moderation.py — Comandos de moderación
# ============================================================

import asyncio
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands
from database import get_warn_db, UserEconomy
from config import MOD_ROLE_ID, WARN_CHANNEL_ID


def _has_mod_role(ctx: commands.Context) -> bool:
    """Comprueba si el autor del mensaje tiene el rol de moderador."""
    return discord.utils.get(ctx.author.roles, id=MOD_ROLE_ID) is not None


class Moderation(commands.Cog):
    """Comandos de moderación y administración."""

    def __init__(self, bot: commands.Bot, economy: UserEconomy):
        self.bot     = bot
        self.economy = economy

    # ── !say ──────────────────────────────────────────────────
    @commands.command(name="say")
    @commands.has_permissions(administrator=True)
    async def say(self, ctx: commands.Context, *, message: str):
        """El bot repite el mensaje (solo administradores)."""
        await ctx.message.delete()
        await ctx.send(message)

    # ── !clear ────────────────────────────────────────────────
    @commands.command(name="clear")
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx: commands.Context, amount: int):
        """Elimina mensajes del canal (solo administradores)."""
        if amount < 1:
            await ctx.send("❌ Por favor, ingresa un número mayor que 0.")
            return
        # +1 para incluir el propio comando
        await ctx.channel.purge(limit=amount + 1)

    # ── !warn ─────────────────────────────────────────────────
    @commands.command(name="warn")
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Añade un warn a un usuario y lo notifica por DM."""
        if not _has_mod_role(ctx):
            await ctx.send("❌ No tienes permiso para usar este comando.")
            return

        conn, cursor = get_warn_db()
        try:
            cursor.execute(
                "INSERT INTO warnings (user_id, reason) VALUES (?, ?)",
                (member.id, reason)
            )
            conn.commit()

            # DM al usuario sancionado
            embed_dm = discord.Embed(
                title="⚠️ Has sido advertido",
                description=(
                    f"**Motivo:** {reason}\n\n"
                    "Si crees que esto es un error, contacta con un moderador."
                ),
                color=discord.Color.red()
            )
            from config import SERVER_NAME, SERVER_LOGO_URL
            embed_dm.set_footer(text=f"Servidor: {SERVER_NAME}")
            if SERVER_LOGO_URL:
                embed_dm.set_thumbnail(url=SERVER_LOGO_URL)
            try:
                await member.send(embed=embed_dm)
            except discord.Forbidden:
                await ctx.send("⚠️ No pude enviar un mensaje privado a este usuario.")

            # Aviso en canal de moderación
            embed_warn = discord.Embed(
                title="🚨 Advertencia aplicada",
                description=f"{member.mention} ha sido advertido.",
                color=discord.Color.orange()
            )
            embed_warn.add_field(name="👤 Usuario",    value=member.mention,     inline=True)
            embed_warn.add_field(name="👮 Moderador",  value=ctx.author.mention, inline=True)
            embed_warn.add_field(name="📌 Motivo",     value=reason,             inline=False)

            warn_channel = ctx.guild.get_channel(WARN_CHANNEL_ID)
            if warn_channel:
                await warn_channel.send(embed=embed_warn)
            else:
                await ctx.send("⚠️ No se encontró el canal de advertencias.")
        finally:
            conn.close()

    # ── !historial ────────────────────────────────────────────
    @commands.command(name="historial")
    async def historial(self, ctx: commands.Context, member: discord.Member):
        """Muestra el historial de warns de un usuario."""
        if not _has_mod_role(ctx):
            await ctx.send("❌ No tienes permiso para usar este comando.")
            return

        conn, cursor = get_warn_db()
        try:
            cursor.execute("SELECT reason FROM warnings WHERE user_id = ?", (member.id,))
            user_warnings = cursor.fetchall()

            if not user_warnings:
                await ctx.send(f"✅ {member.mention} no tiene advertencias previas.")
                return

            embed = discord.Embed(
                title=f"📋 Historial de advertencias de {member.name}",
                color=discord.Color.red()
            )
            for idx, (reason,) in enumerate(user_warnings, start=1):
                embed.add_field(name=f"Advertencia {idx}", value=reason, inline=False)
            await ctx.send(embed=embed)
        finally:
            conn.close()

    # ── !addmoney ─────────────────────────────────────────────
    @commands.command(name="addmoney")
    @commands.has_permissions(administrator=True)
    async def add_money(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Añade monedas a un usuario (solo administradores)."""
        if amount <= 0:
            await ctx.send("❌ La cantidad debe ser mayor que 0.")
            return
        self.economy.update_balance(member.id, amount)
        embed = discord.Embed(
            title="✅ Monedas Añadidas",
            description=f"Se han añadido **{amount:,} monedas** a {member.mention}.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Nuevo balance: {self.economy.get_balance(member.id):,} monedas")
        await ctx.send(embed=embed)

    # ── !removemoney ──────────────────────────────────────────
    @commands.command(name="removemoney")
    @commands.has_permissions(administrator=True)
    async def remove_money(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Elimina monedas de un usuario (solo administradores)."""
        if amount <= 0:
            await ctx.send("❌ La cantidad debe ser mayor que 0.")
            return
        current_balance = self.economy.get_balance(member.id)
        # No puede quedar en negativo
        actual_amount = min(amount, current_balance)
        self.economy.update_balance(member.id, -actual_amount)
        embed = discord.Embed(
            title="✅ Monedas Eliminadas",
            description=f"Se han eliminado **{actual_amount:,} monedas** de {member.mention}.",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Nuevo balance: {self.economy.get_balance(member.id):,} monedas")
        await ctx.send(embed=embed)

    # ── !verificar_roles ──────────────────────────────────────
    @commands.command(name="verificar_roles")
    @commands.has_permissions(administrator=True)
    async def verificar_roles(self, ctx: commands.Context):
        """Verifica y asigna los roles automáticos a todos los miembros."""
        from config import ROLES_IDS
        roles = [role for role_id in ROLES_IDS
                 if (role := ctx.guild.get_role(role_id)) is not None]
        if not roles:
            await ctx.send("❌ Ninguno de los roles especificados existe. Revisa la configuración.")
            return

        count = 0
        for member in ctx.guild.members:
            missing = [r for r in roles if r not in member.roles]
            if missing:
                await member.add_roles(*missing)
                count += 1

        await ctx.send(f"✅ Se ha verificado y corregido el rol en **{count}** miembros.")


    # ── !purgar ───────────────────────────────────────────────
    @commands.command(name="purgar")
    @commands.has_permissions(administrator=True)
    async def purgar(self, ctx: commands.Context, member: discord.Member):
        """Elimina mensajes de un usuario en todos los canales (4 días) y lo bloquea 3 días."""
        DAYS_BACK    = 4
        TIMEOUT_DAYS = 3
        cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)

        # Confirmación visual
        status_embed = discord.Embed(
            title="⏳ Purgando mensajes...",
            description=f"Buscando mensajes de {member.mention} en los últimos {DAYS_BACK} días.",
            color=discord.Color.orange()
        )
        status_msg = await ctx.send(embed=status_embed)

        total_deleted = 0
        channels_affected = 0

        for channel in ctx.guild.text_channels:
            # Comprobar permisos del bot en el canal
            perms = channel.permissions_for(ctx.guild.me)
            if not (perms.read_message_history and perms.manage_messages):
                continue

            try:
                deleted = await channel.purge(
                    limit=500,
                    check=lambda m, u=member: m.author.id == u.id,
                    after=cutoff,
                    bulk=True
                )
                if deleted:
                    total_deleted += len(deleted)
                    channels_affected += 1
                    await asyncio.sleep(0.5)  # Evitar rate-limit
            except (discord.Forbidden, discord.HTTPException) as e:
                print(f"[WARN] No se pudo purgar en #{channel.name}: {e}")

        # Timeout al usuario por TIMEOUT_DAYS días
        timeout_until = datetime.now(timezone.utc) + timedelta(days=TIMEOUT_DAYS)
        try:
            await member.timeout(
                timeout_until,
                reason=f"Spam detectado — purgado por {ctx.author}"
            )
        except discord.Forbidden:
            await ctx.send("⚠️ No tengo permisos para silenciar a este usuario.")

        # DM de aviso al usuario
        dm_embed = discord.Embed(
            title="🚨 Aviso de seguridad",
            description=(
                f"Hola {member.display_name},\n\n"
                "Hemos detectado actividad inusual en tu cuenta (posible spam automatizado). "
                "Es posible que tu cuenta haya sido **hackeada o comprometida**.\n\n"
                "**Te recomendamos:**\n"
                "🔒 Cambiar tu contraseña de Discord inmediatamente.\n"
                "📧 Activar la verificación en dos pasos (2FA).\n"
                "📩 Contactar con el soporte de Discord si crees que han accedido a tu cuenta.\n\n"
                f"Tu cuenta ha sido silenciada en el servidor durante **{TIMEOUT_DAYS} días** "
                "mientras se investiga el incidente. Si crees que es un error, contacta con un moderador."
            ),
            color=discord.Color.red()
        )
        from config import SERVER_NAME, SERVER_LOGO_URL
        dm_embed.set_footer(text=f"{SERVER_NAME} — Equipo de moderación")
        if SERVER_LOGO_URL:
            dm_embed.set_thumbnail(url=SERVER_LOGO_URL)
        try:
            await member.send(embed=dm_embed)
            dm_sent = True
        except discord.Forbidden:
            dm_sent = False

        # Resumen final
        result_embed = discord.Embed(
            title="✅ Purga completada",
            color=discord.Color.green()
        )
        result_embed.add_field(name="👤 Usuario",           value=member.mention,            inline=True)
        result_embed.add_field(name="🗑️ Mensajes eliminados", value=str(total_deleted),       inline=True)
        result_embed.add_field(name="📢 Canales afectados",  value=str(channels_affected),    inline=True)
        result_embed.add_field(name="⏱️ Silenciado hasta",  value=f"<t:{int(timeout_until.timestamp())}:F>", inline=False)
        result_embed.add_field(name="📩 DM enviado",         value="Sí" if dm_sent else "No (DMs cerrados)", inline=True)
        await status_msg.edit(embed=result_embed)


async def setup(bot: commands.Bot, economy: UserEconomy):
    await bot.add_cog(Moderation(bot, economy))
