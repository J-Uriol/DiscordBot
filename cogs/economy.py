# ============================================================
#  cogs/economy.py — Comandos de economía
# ============================================================

import random
from datetime import timedelta
import discord
from discord.ext import commands
from database import UserEconomy
from config import DAILY_AMOUNT, WORK_MIN, WORK_MAX, ECO_CHANNEL_ID


class Economy(commands.Cog):
    """Comandos del sistema de economía."""

    def __init__(self, bot: commands.Bot, economy: UserEconomy):
        self.bot     = bot
        self.economy = economy

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Restringe todos los comandos de economía al canal designado."""
        if ctx.channel.id != ECO_CHANNEL_ID:
            await ctx.send(
                f"❌ Los comandos de economía solo pueden usarse en <#{ECO_CHANNEL_ID}>.",
                delete_after=8
            )
            return False
        return True


    # ── !balance ──────────────────────────────────────────────
    @commands.command(name="balance", aliases=["bal"])
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """Muestra el balance de un usuario."""
        member  = member or ctx.author
        balance = self.economy.get_balance(member.id)
        bank    = self.economy.get_bank_balance(member.id)
        embed = discord.Embed(
            title=f"💰 Finanzas de {member.display_name}",
            color=discord.Color.gold()
        )
        embed.add_field(name="💵 Cartera", value=f"{balance:,} monedas", inline=True)
        embed.add_field(name="🏦 Banco",   value=f"{bank:,} monedas",    inline=True)
        embed.add_field(name="📊 Total",   value=f"{balance + bank:,} monedas", inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await ctx.send(embed=embed)

    # ── !deposit ──────────────────────────────────────────────
    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx: commands.Context, amount: str):
        """Mueve dinero de tu cartera al banco."""
        user_id = ctx.author.id
        balance = self.economy.get_balance(user_id)

        if amount.lower() == "all":
            amount_int = balance
        else:
            try:
                amount_int = int(amount)
            except ValueError:
                await ctx.send("❌ Cantidad no válida.")
                return

        if amount_int <= 0:
            await ctx.send("❌ La cantidad debe ser mayor que 0.")
            return

        if balance < amount_int:
            await ctx.send("❌ No tienes suficientes monedas en la cartera.")
            return

        self.economy.deposit_bank(user_id, amount_int)
        await ctx.send(f"✅ Has depositado **{amount_int:,} monedas** en el banco.")

    # ── !withdraw ─────────────────────────────────────────────
    @commands.command(name="withdraw", aliases=["with"])
    async def withdraw(self, ctx: commands.Context, amount: str):
        """Mueve dinero de tu banco a tu cartera."""
        user_id = ctx.author.id
        bank    = self.economy.get_bank_balance(user_id)

        if amount.lower() == "all":
            amount_int = bank
        else:
            try:
                amount_int = int(amount)
            except ValueError:
                await ctx.send("❌ Cantidad no válida.")
                return

        if amount_int <= 0:
            await ctx.send("❌ La cantidad debe ser mayor que 0.")
            return

        if bank < amount_int:
            await ctx.send("❌ No tienes suficientes monedas en el banco.")
            return

        self.economy.withdraw_bank(user_id, amount_int)
        await ctx.send(f"✅ Has retirado **{amount_int:,} monedas** del banco.")

    # ── !daily ────────────────────────────────────────────────
    @commands.command(name="daily")
    async def daily(self, ctx: commands.Context):
        """Reclama tu recompensa diaria."""
        if not self.economy.can_claim_daily(ctx.author.id):
            await ctx.send("❌ Ya has reclamado tu recompensa diaria hoy. Vuelve mañana.")
            return

        self.economy.update_balance(ctx.author.id, DAILY_AMOUNT)
        self.economy.set_last_daily(ctx.author.id)
        embed = discord.Embed(
            title="🎉 Recompensa Diaria",
            description=f"Has recibido **{DAILY_AMOUNT:,} monedas**. ¡Vuelve mañana por más!",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Balance actual: {self.economy.get_balance(ctx.author.id):,} monedas")
        await ctx.send(embed=embed)

    # ── !work ─────────────────────────────────────────────────
    @commands.command(name="work")
    async def work(self, ctx: commands.Context):
        """Trabaja para ganar monedas."""
        if not self.economy.can_work(ctx.author.id):
            await ctx.send("❌ Necesitas descansar. Puedes trabajar de nuevo en 1 hora.")
            return

        earnings = random.randint(WORK_MIN, WORK_MAX)
        self.economy.update_balance(ctx.author.id, earnings)
        self.economy.set_last_work(ctx.author.id)

        jobs = [
            "fue camarero en un bar", "programó un bot de Discord",
            "vendió limonada en la calle", "hizo streaming en Twitch",
            "dio clases particulares", "vendió artículos usados",
            "participó en un estudio de mercado", "hizo de repartidor",
        ]
        embed = discord.Embed(
            title="💼 Trabajo Completado",
            description=f"{ctx.author.mention} {random.choice(jobs)} y ganó **{earnings:,} monedas**.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Balance actual: {self.economy.get_balance(ctx.author.id):,} monedas")
        await ctx.send(embed=embed)

    # ── !transfer ─────────────────────────────────────────────
    @commands.command(name="transfer", aliases=["pay"])
    async def transfer(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Transfiere monedas a otro usuario."""
        if amount <= 0:
            await ctx.send("❌ La cantidad debe ser mayor que 0.")
            return
        if member == ctx.author:
            await ctx.send("❌ No puedes transferirte monedas a ti mismo.")
            return

        sender_balance = self.economy.get_balance(ctx.author.id)
        if sender_balance < amount:
            await ctx.send("❌ No tienes suficientes monedas para realizar esta transferencia.")
            return

        self.economy.update_balance(ctx.author.id, -amount)
        self.economy.update_balance(member.id, amount)

        embed = discord.Embed(
            title="✅ Transferencia Exitosa",
            description=f"{ctx.author.mention} ha transferido **{amount:,} monedas** a {member.mention}.",
            color=discord.Color.green()
        )
        embed.add_field(name=f"Balance de {ctx.author.display_name}",
                        value=f"{self.economy.get_balance(ctx.author.id):,} monedas", inline=False)
        embed.add_field(name=f"Balance de {member.display_name}",
                        value=f"{self.economy.get_balance(member.id):,} monedas", inline=False)
        await ctx.send(embed=embed)

    # ── !gift ─────────────────────────────────────────────────
    @commands.command(name="gift")
    async def gift(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Regala monedas a otro usuario."""
        if amount <= 0:
            await ctx.send("❌ La cantidad debe ser mayor que 0.")
            return
        if member == ctx.author:
            await ctx.send("❌ No puedes regalarte monedas a ti mismo.")
            return

        sender_balance = self.economy.get_balance(ctx.author.id)
        if sender_balance < amount:
            await ctx.send("❌ No tienes suficientes monedas para ser tan generoso.")
            return

        self.economy.update_balance(ctx.author.id, -amount)
        self.economy.update_balance(member.id, amount)

        embed = discord.Embed(
            title="🎁 ¡Regalo Enviado!",
            description=f"{ctx.author.mention} ha regalado **{amount:,} monedas** a {member.mention}. ¡Qué generoso!",
            color=discord.Color.green()
        )
        embed.add_field(name=f"Balance de {ctx.author.display_name}",
                        value=f"💵 {self.economy.get_balance(ctx.author.id):,} monedas", inline=True)
        embed.add_field(name=f"Balance de {member.display_name}",
                        value=f"💵 {self.economy.get_balance(member.id):,} monedas", inline=True)
        await ctx.send(embed=embed)

    # ── !leaderboard ──────────────────────────────────────────
    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context):
        """Muestra los 10 usuarios con más monedas."""
        top_users = self.economy.get_top_users(limit=10)

        embed = discord.Embed(
            title="🏆 Los Más Ricos del Servidor",
            description="¡Los 10 usuarios con más monedas! 💰" if top_users
                        else "ℹ️ No hay usuarios registrados todavía.",
            color=discord.Color.gold()
        )
        embed.set_footer(
            text=f"Solicitado por {ctx.author.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )

        for idx, (user_id, bal) in enumerate(top_users, 1):
            user      = self.bot.get_user(user_id)
            user_name = user.display_name if user else f"Usuario desconocido ({user_id})"
            medal     = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🏅"
            embed.add_field(
                name=f"{medal} {idx}. {user_name}",
                value=f"💵 {bal:,} monedas",
                inline=False
            )

        await ctx.send(embed=embed)

    # ── !halloffame ───────────────────────────────────────────
    @commands.command(name="halloffame", aliases=["hof"])
    async def halloffame(self, ctx: commands.Context):
        """Muestra los ganadores mensuales."""
        rows = self.economy.get_hall_of_fame()

        if not rows:
            await ctx.send("📜 No hay ganadores registrados aún.")
            return

        meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                 "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        embed = discord.Embed(
            title="🏆 Hall of Fame - Ganadores Mensuales",
            color=discord.Color.gold()
        )
        for month, year, user_id, bal in rows:
            user   = self.bot.get_user(user_id)
            nombre = user.name if user else f"Usuario {user_id}"
            embed.add_field(
                name=f"{meses[month - 1]} {year}",
                value=f"{nombre} — 💵 {bal:,} monedas",
                inline=False
            )
        await ctx.send(embed=embed)

    # ── !steal ────────────────────────────────────────────────
    @commands.command(name="steal")
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def steal(self, ctx: commands.Context, member: discord.Member):
        """Intenta robar monedas a otro usuario (35 % de éxito)."""
        if member == ctx.author:
            embed = discord.Embed(
                title="🚫 Error",
                description="No puedes robarte a ti mismo, ¡eso sería demasiado fácil!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        target_balance = self.economy.get_balance(member.id)
        if target_balance < 300:
            embed = discord.Embed(
                title="🚫 Pobreza Detectada",
                description=f"{member.mention} no tiene suficientes monedas para ser robado (mínimo 300).",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        thief_balance = self.economy.get_balance(ctx.author.id)
        if thief_balance < 500:
            embed = discord.Embed(
                title="🚫 Sin Fondos para Multas",
                description="Necesitas al menos 500 monedas para intentar un robo (por si te atrapan).",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        SUCCESS_CHANCE      = 0.35
        MAX_STEAL_PERCENT   = 0.30
        steal_amount = random.randint(100, max(100, int(target_balance * MAX_STEAL_PERCENT)))

        if random.random() < SUCCESS_CHANCE:
            self.economy.update_balance(ctx.author.id, steal_amount)
            self.economy.update_balance(member.id, -steal_amount)
            embed = discord.Embed(
                title="💰 ¡Robo Exitoso!",
                description=(
                    f"{ctx.author.mention} ha logrado burlar la seguridad "
                    f"y robó **{steal_amount:,} monedas** a {member.mention}!"
                ),
                color=discord.Color.green()
            )
            embed.add_field(name="💰 Dinero robado",   value=f"{steal_amount:,} monedas", inline=False)
            embed.add_field(name="💵 Tu nuevo balance", value=f"{self.economy.get_balance(ctx.author.id):,} monedas", inline=False)
            embed.set_footer(text="Probabilidad de éxito: 35% | Cooldown: 10 minutos")
        else:
            fine = random.randint(500, 1500)
            actual_fine = min(fine, thief_balance)
            self.economy.update_balance(ctx.author.id, -actual_fine)
            embed = discord.Embed(
                title="🚨 ¡Atrapado y Multado!",
                description=(
                    f"{ctx.author.mention} intentó robar a {member.mention} "
                    f"pero fue capturado y multado con **{actual_fine:,} monedas**."
                ),
                color=discord.Color.red()
            )
            embed.add_field(name="💸 Multa aplicada",   value=f"{actual_fine:,} monedas", inline=False)
            embed.add_field(name="💵 Tu nuevo balance", value=f"{self.economy.get_balance(ctx.author.id):,} monedas", inline=False)
            embed.set_footer(text="Probabilidad de éxito: 35% | Cooldown: 10 minutos")

        await ctx.send(embed=embed)

    @steal.error
    async def steal_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            remaining = str(timedelta(seconds=int(error.retry_after)))
            embed = discord.Embed(
                title="⏳ Enfriamiento",
                description=f"Debes esperar **{remaining}** antes de intentar otro robo.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Debes mencionar a un usuario. Ejemplo: `!steal @usuario`")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ No pude encontrar al usuario mencionado.")
        else:
            print(f"[ERROR steal] {error}")
            await ctx.send("❌ Ocurrió un error inesperado.")


async def setup(bot: commands.Bot, economy: UserEconomy):
    await bot.add_cog(Economy(bot, economy))
