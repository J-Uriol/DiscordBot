# ============================================================
#  cogs/casino.py — Comandos de casino
# ============================================================

import random
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button
from database import UserEconomy
from config import ECO_CHANNEL_ID


class Casino(commands.Cog):
    """Comandos de casino y apuestas."""

    def __init__(self, bot: commands.Bot, economy: UserEconomy):
        self.bot     = bot
        self.economy = economy

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Restringe todos los comandos del casino al canal de economía."""
        if ctx.channel.id != ECO_CHANNEL_ID:
            await ctx.send(
                f"❌ Los comandos del casino solo pueden usarse en <#{ECO_CHANNEL_ID}>.",
                delete_after=8
            )
            return False
        return True


    # ── Helper: comprobar saldo ───────────────────────────────
    async def _check_bet(self, ctx: commands.Context, amount: int) -> bool:
        """Verifica que la apuesta sea válida. Devuelve False si hay error."""
        if amount <= 0:
            await ctx.send("❌ La apuesta debe ser mayor que 0.")
            return False
        balance = self.economy.get_balance(ctx.author.id)
        if balance < amount:
            embed = discord.Embed(
                title="🚫 Saldo Insuficiente",
                description=f"Necesitas **{amount:,} monedas** pero solo tienes **{balance:,}**.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
        return True

    # ── !coinflip ─────────────────────────────────────────────
    @commands.command(name="coinflip")
    async def coinflip(self, ctx: commands.Context, amount: int):
        """Apuesta en cara o cruz."""
        if not await self._check_bet(ctx, amount):
            return

        embed = discord.Embed(
            title="🎲 Lanzando la Moneda...",
            description=f"{ctx.author.mention} apostó **{amount:,} monedas**.",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)
        await asyncio.sleep(2)

        result = random.choice(["Cara", "Cruz"])
        if random.random() < 0.5:
            self.economy.update_balance(ctx.author.id, amount)
            embed.title       = "🎉 ¡Ganaste!"
            embed.description = f"Salió **{result}**. ¡Ganaste **{amount:,} monedas**!"
            embed.color       = discord.Color.green()
        else:
            self.economy.update_balance(ctx.author.id, -amount)
            embed.title       = "😢 Perdiste"
            embed.description = f"Salió **{result}**. Perdiste **{amount:,} monedas**."
            embed.color       = discord.Color.red()

        embed.add_field(
            name="Tu nuevo balance",
            value=f"💵 {self.economy.get_balance(ctx.author.id):,} monedas",
            inline=False
        )
        await message.edit(embed=embed)

    # ── !slots ────────────────────────────────────────────────
    @commands.command(name="slots")
    async def slots(self, ctx: commands.Context, amount: int):
        """Juega a las tragamonedas."""
        if not await self._check_bet(ctx, amount):
            return

        symbols = ["🍒", "🍋", "🍊", "💎", "🔔", "7️⃣"]
        result  = [random.choice(symbols) for _ in range(3)]

        embed = discord.Embed(
            title="🎰 Girando las Tragamonedas...",
            description=f"{ctx.author.mention} apostó **{amount:,} monedas**.\n\n| ❓ | ❓ | ❓ |",
            color=discord.Color.purple()
        )
        message = await ctx.send(embed=embed)
        await asyncio.sleep(2)

        slot_display = f"| {' | '.join(result)} |"

        if result[0] == result[1] == result[2]:
            winnings = amount * 5
            net      = winnings - amount
            self.economy.update_balance(ctx.author.id, net)
            embed.title       = "🎰 ¡Jackpot!"
            embed.color       = discord.Color.green()
            embed.description = f"{slot_display}\n¡Ganaste **{winnings:,} monedas** (x5)!"
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            winnings = amount * 2
            net      = winnings - amount
            self.economy.update_balance(ctx.author.id, net)
            embed.title       = "🎰 ¡Ganaste!"
            embed.color       = discord.Color.green()
            embed.description = f"{slot_display}\n¡Ganaste **{winnings:,} monedas** (x2)!"
        else:
            self.economy.update_balance(ctx.author.id, -amount)
            embed.title       = "🎰 Perdiste"
            embed.color       = discord.Color.red()
            embed.description = f"{slot_display}\nPerdiste **{amount:,} monedas**."

        embed.add_field(
            name="Tu nuevo balance",
            value=f"💵 {self.economy.get_balance(ctx.author.id):,} monedas",
            inline=False
        )
        await message.edit(embed=embed)

    # ── !roulette ─────────────────────────────────────────────
    @commands.command(name="roulette")
    async def roulette(self, ctx: commands.Context, amount: int, color: str):
        """Apuesta a rojo o negro en la ruleta."""
        if not await self._check_bet(ctx, amount):
            return

        color = color.lower()
        if color not in ("rojo", "negro"):
            await ctx.send("❌ Debes elegir `rojo` o `negro`.")
            return

        embed = discord.Embed(
            title="🎡 Girando la Ruleta...",
            description=f"{ctx.author.mention} apostó **{amount:,} monedas** al **{color}**.",
            color=discord.Color.dark_purple()
        )
        message = await ctx.send(embed=embed)
        await asyncio.sleep(2)

        result = random.choice(["rojo", "negro"])
        if result == color:
            self.economy.update_balance(ctx.author.id, amount)
            embed.title       = "🎉 ¡Ganaste!"
            embed.description = f"La ruleta cayó en **{result}**. ¡Ganaste **{amount:,} monedas**!"
            embed.color       = discord.Color.green()
        else:
            self.economy.update_balance(ctx.author.id, -amount)
            embed.title       = "😢 Perdiste"
            embed.description = f"La ruleta cayó en **{result}**. Perdiste **{amount:,} monedas**."
            embed.color       = discord.Color.red()

        embed.add_field(
            name="Tu nuevo balance",
            value=f"💵 {self.economy.get_balance(ctx.author.id):,} monedas",
            inline=False
        )
        await message.edit(embed=embed)

    # ── !carrera ──────────────────────────────────────────────
    @commands.command(name="carrera")
    async def carrera(self, ctx: commands.Context, amount: int):
        """Apuesta en una carrera de caballos."""
        if not await self._check_bet(ctx, amount):
            return

        horses = ["🐎", "🏇", "🐎", "🏇"]
        names  = ["Rayo", "Trueno", "Viento", "Fuego"]
        positions = [0, 0, 0, 0]
        finish_line = 12

        # Descontar apuesta al inicio
        self.economy.update_balance(ctx.author.id, -amount)

        embed = discord.Embed(
            title="🐎 Carrera de Caballos",
            description=f"{ctx.author.mention} apostó **{amount:,} monedas**.\nSelecciona tu caballo abajo.",
            color=discord.Color.blue()
        )
        
        # Selección del caballo (por ahora simplificado a elegir uno al azar para el user o dejar que apueste)
        # Vamos a hacer que el usuario simplemente apueste y si el caballo 1 (Rayo) gana, él gana.
        # Mejor: El usuario elige un caballo mediante botones.
        
        class HorseView(View):
            def __init__(self):
                super().__init__(timeout=30)
                self.choice = None

            @discord.ui.button(label="Rayo", style=discord.ButtonStyle.primary, emoji="🐎")
            async def rayo(self, interaction: discord.Interaction, button: Button):
                self.choice = 0
                self.stop()
                await interaction.response.defer()

            @discord.ui.button(label="Trueno", style=discord.ButtonStyle.primary, emoji="🏇")
            async def trueno(self, interaction: discord.Interaction, button: Button):
                self.choice = 1
                self.stop()
                await interaction.response.defer()

            @discord.ui.button(label="Viento", style=discord.ButtonStyle.primary, emoji="🐎")
            async def viento(self, interaction: discord.Interaction, button: Button):
                self.choice = 2
                self.stop()
                await interaction.response.defer()

            @discord.ui.button(label="Fuego", style=discord.ButtonStyle.primary, emoji="🏇")
            async def fuego(self, interaction: discord.Interaction, button: Button):
                self.choice = 3
                self.stop()
                await interaction.response.defer()

        view = HorseView()
        msg = await ctx.send("🏇 **Selecciona tu caballo para la carrera:**", view=view)
        await view.wait()

        if view.choice is None:
            self.economy.update_balance(ctx.author.id, amount) # Reembolsar
            await msg.edit(content="❌ Tiempo agotado. Carrera cancelada y apuesta devuelta.", view=None)
            return

        user_choice = view.choice
        await msg.edit(content=f"🏇 Has elegido a **{names[user_choice]}**. ¡Que empiece la carrera!", view=None)

        while max(positions) < finish_line:
            for i in range(len(positions)):
                positions[i] += random.randint(1, 3)
            
            race_track = ""
            for i in range(len(horses)):
                line = ["—"] * finish_line
                if positions[i] < finish_line:
                    line[positions[i]] = horses[i]
                else:
                    line[finish_line-1] = horses[i]
                race_track += f"**{names[i]}**: `{''.join(line)}` 🏁\n"
            
            embed.description = f"🏇 **¡En marcha!**\n\n{race_track}"
            try:
                await msg.edit(embed=embed)
            except:
                break
            await asyncio.sleep(1.0)

        winner_idx = positions.index(max(positions))
        winner_name = names[winner_idx]

        if winner_idx == user_choice:
            winnings = amount * 3
            self.economy.update_balance(ctx.author.id, winnings)
            embed.title = f"🏆 ¡Ganó {winner_name}!"
            embed.color = discord.Color.green()
            embed.description = f"¡Tu caballo **{winner_name}** ha ganado la carrera! 🏁\nGanaste **{winnings:,} monedas**."
        else:
            # No se devuelve nada (ya se descontó al inicio)
            embed.title = f"🏁 Ganó {winner_name}"
            embed.color = discord.Color.red()
            embed.description = f"Tu caballo quedó atrás. El ganador fue **{winner_name}**.\nPerdiste **{amount:,} monedas**."

        embed.add_field(name="Nuevo Balance", value=f"💵 {self.economy.get_balance(ctx.author.id):,} monedas")
        await msg.edit(embed=embed)


async def setup(bot: commands.Bot, economy: UserEconomy):
    await bot.add_cog(Casino(bot, economy))
