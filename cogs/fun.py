# ============================================================
#  cogs/fun.py — Comandos de diversión
# ============================================================

import random
import discord
from discord.ext import commands


class Fun(commands.Cog):
    """Comandos de diversión."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── !moneda ───────────────────────────────────────────────
    @commands.command(name="moneda")
    async def moneda(self, ctx: commands.Context):
        """Lanza una moneda."""
        resultado = random.choice(["Cara", "Cruz"])
        await ctx.send(f"{ctx.author.mention} La moneda ha salido: **{resultado}**")

    # ── !suerte ───────────────────────────────────────────────
    @commands.command(name="suerte")
    async def suerte(self, ctx: commands.Context):
        """El bot responde preguntas al estilo de la bola mágica."""
        respuestas = [
            "La bola dice que: Bien.", "La bola dice que: Mal.", "La bola dice que: Tal vez.",
            "La bola dice que: Definitivamente sí.", "La bola dice que: No cuentes con ello.",
            "La bola dice que: Claro que sí.", "La bola dice que: Parece que sí.",
            "La bola dice que: Mejor no te digo nada.",
            "La bola dice que: No estoy seguro, vuelve a intentarlo.",
            "La bola dice que: Es probable.", "La bola dice que: Lo dudo.",
            "La bola dice que: ¡Claro que no!",
            "La bola dice que: La respuesta es incierta.",
            "La bola dice que: La suerte está de tu lado.",
            "La bola dice que: La fortuna te sonríe.",
            "La bola dice que: Todo depende de ti.",
            "La bola dice que: No es un buen momento para eso.",
            "La bola dice que: ¡Sí, sin duda!",
            "La bola dice que: No te preocupes, todo saldrá bien.",
            "La bola dice que: ¡Lo conseguirás!",
            "La bola dice que: Los astros están alineados a tu favor.",
            "La bola dice que: Mejor espera un poco.",
            "La bola dice que: El futuro es incierto, pero tal vez.",
            "La bola dice que: Confía en tu instinto.",
        ]
        await ctx.send(f"{ctx.author.mention} {random.choice(respuestas)}")

    # ── !memide ───────────────────────────────────────────────
    @commands.command(name="memide")
    async def memide(self, ctx: commands.Context):
        """El bot te dice cuánto te mide aleatoriamente."""
        tamaños = ["2 cm 😳", "5 cm 😢", "10 cm 🪯", "15 cm 😏", "20 cm 😎", "30 cm 🔥"]
        await ctx.send(f"{ctx.author.mention} La bola mágica dice que te mide **{random.choice(tamaños)}**")

    # ── !rps ──────────────────────────────────────────────────
    @commands.command(name="rps")
    async def rps(self, ctx: commands.Context, eleccion: str):
        """Juega a piedra, papel o tijera contra el bot."""
        opciones = ["piedra", "papel", "tijeras"]
        eleccion = eleccion.lower()

        if eleccion not in opciones:
            await ctx.send("✋ Opciones válidas: `piedra`, `papel` o `tijeras`.")
            return

        bot_choice = random.choice(opciones)

        if eleccion == bot_choice:
            resultado = "🤝 Empate."
        elif (
            (eleccion == "piedra"  and bot_choice == "tijeras") or
            (eleccion == "papel"   and bot_choice == "piedra")  or
            (eleccion == "tijeras" and bot_choice == "papel")
        ):
            resultado = "🎉 ¡Ganaste!"
        else:
            resultado = "😢 Perdiste."

        await ctx.send(
            f"🆚 {ctx.author.mention} eligió `{eleccion}`. "
            f"Yo elegí `{bot_choice}`. {resultado}"
        )

    # ── !ship ─────────────────────────────────────────────────
    @commands.command(name="ship")
    async def ship(self, ctx: commands.Context, u1: discord.Member, u2: discord.Member = None):
        """Calcula la compatibilidad entre dos usuarios."""
        if u2 is None:
            u2 = u1
            u1 = ctx.author
        
        if u1 == u2:
            await ctx.send("❤️ Te quieres mucho a ti mismo, ¡eso es bueno!")
            return

        # Generar porcentaje basado en los IDs para que sea consistente
        random.seed(u1.id + u2.id)
        percent = random.randint(0, 100)
        random.seed() # Reset seed

        bar_filled = int(percent / 10)
        bar = "❤️" * bar_filled + "🖤" * (10 - bar_filled)

        if percent < 20:   msg = "Mejor que seáis solo amigos... 🥶"
        elif percent < 50: msg = "Hay algo de chispa, pero falta leña. 🧱"
        elif percent < 80: msg = "¡Vaya, aquí hay tema! 🔥"
        else:              msg = "¡Almas gemelas! Casaros ya. 💍"

        embed = discord.Embed(
            title="❤️ Medidor de Amor ❤️",
            description=f"Compatibilidad entre **{u1.display_name}** y **{u2.display_name}**",
            color=discord.Color.red()
        )
        embed.add_field(name=f"{percent}%", value=bar, inline=False)
        embed.set_footer(text=msg)
        
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
