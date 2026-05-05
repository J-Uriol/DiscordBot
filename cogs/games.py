# ============================================================
#  cogs/games.py — Minijuegos de economía
# ============================================================

import random
import asyncio
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands
from discord.ui import Button, View
from database import UserEconomy
from config import ECO_CHANNEL_ID

# ── Cooldown de pesca en memoria ─────────────────────────────
_fish_cooldowns: dict[int, datetime] = {}
FISH_COOLDOWN_MINUTES = 20

# ── Preguntas de Trivia ──────────────────────────────────────
TRIVIA_QUESTIONS = [
    # --- Cultura General ---
    {"q": "¿Cuál es la capital de Francia?", "a": ["París", "Lyon", "Marsella", "Burdeos"], "c": 0},
    {"q": "¿En qué año terminó la Segunda Guerra Mundial?", "a": ["1943", "1945", "1948", "1950"], "c": 1},
    {"q": "¿Cuál es el planeta más grande del sistema solar?", "a": ["Tierra", "Marte", "Júpiter", "Saturno"], "c": 2},
    {"q": "¿Quién pintó la Mona Lisa?", "a": ["Van Gogh", "Picasso", "Da Vinci", "Dalí"], "c": 2},
    {"q": "¿Qué elemento químico tiene el símbolo 'O'?", "a": ["Oro", "Oxígeno", "Osmio", "Olmió"], "c": 1},
    {"q": "¿Cuál es el río más largo del mundo?", "a": ["Nilo", "Amazonas", "Misisipi", "Danubio"], "c": 1},
    {"q": "¿Cuántos huesos tiene el cuerpo humano adulto?", "a": ["206", "195", "215", "201"], "c": 0},
    {"q": "¿En qué país se encuentra la Torre Pisa?", "a": ["España", "Francia", "Italia", "Grecia"], "c": 2},
    {"q": "¿Cuál es el océano más grande?", "a": ["Atlántico", "Índico", "Ártico", "Pacífico"], "c": 3},
    {"q": "¿Quién escribió 'Don Quijote de la Mancha'?", "a": ["Lorca", "Cervantes", "Quevedo", "Góngora"], "c": 1},
    {"q": "¿Qué gas absorben las plantas para realizar la fotosíntesis?", "a": ["Oxígeno", "Nitrógeno", "Dióxido de Carbono", "Hidrógeno"], "c": 2},
    {"q": "¿Cuál es el país más grande del mundo por superficie?", "a": ["China", "Rusia", "Canadá", "EE.UU."], "c": 1},
    {"q": "¿En qué continente está el desierto del Sáhara?", "a": ["Asia", "América", "África", "Oceanía"], "c": 2},
    {"q": "¿Quién es el autor de 'Cien años de soledad'?", "a": ["Vargas Llosa", "García Márquez", "Julio Cortázar", "Isabel Allende"], "c": 1},
    {"q": "¿Cuál es el metal más caro del mundo?", "a": ["Oro", "Platino", "Rodio", "Paladio"], "c": 2},

    # --- Videojuegos General ---
    {"q": "¿Cómo se llama el protagonista de 'The Legend of Zelda'?", "a": ["Zelda", "Link", "Ganon", "Epona"], "c": 1},
    {"q": "¿Cuál es el videojuego más vendido de la historia?", "a": ["Minecraft", "Tetris", "GTA V", "Wii Sports"], "c": 0},
    {"q": "¿En qué año se lanzó la primera PlayStation en Japón?", "a": ["1992", "1994", "1996", "1990"], "c": 1},
    {"q": "¿Quién es el creador de Super Mario?", "a": ["Hideo Kojima", "Shigeru Miyamoto", "Tetsuya Nomura", "Masahiro Sakurai"], "c": 1},
    {"q": "¿Cómo se llama el mundo de 'The Witcher'?", "a": ["Azeroth", "Tamriel", "El Continente", "Hyrule"], "c": 2},
    {"q": "¿Qué empresa desarrolló 'Fortnite'?", "a": ["Valve", "Ubisoft", "Epic Games", "EA"], "c": 2},

    # --- ARK: Survival Evolved ---
    {"q": "¿Cuál es el dinosaurio por excelencia para recolectar metal en ARK?", "a": ["Trike", "Doedicurus", "Ankylosaurus", "Stego"], "c": 2},
    {"q": "¿Cómo se llama el primer mapa oficial de ARK?", "a": ["Ragnarok", "The Island", "Aberration", "Extinction"], "c": 1},
    {"q": "¿Qué recurso se obtiene al picar el cuerpo de un Tek Rex?", "a": ["Carne", "Polímero Orgánico", "Chatarra y Electrónicos", "Cristal"], "c": 2},
    {"q": "¿Qué criatura es conocida por robar objetos del inventario en la playa?", "a": ["Dilo", "Icthyornis", "Pegomastax", "Ambos B y C"], "c": 3},
    {"q": "¿Cuál es el boss final de 'The Island'?", "a": ["Broodmother", "Megapithecus", "Dragon", "Overseer"], "c": 3},
    {"q": "¿Qué material necesitas para fabricar gasolina en la forja?", "a": ["Aceite y Piel", "Aceite y Fibra", "Polímero y Metal", "Queratina y Piel"], "c": 0},
    {"q": "¿Qué dinosaurio es capaz de planear y escalar paredes en Aberration?", "a": ["Reaper", "Rock Drake", "Basilisk", "Karkinos"], "c": 1},
    {"q": "¿Cómo se llama la moneda o recurso especial que se usa en los terminales de HLN-A en Genesis?", "a": ["Monedas", "Hexágonos", "Elementos", "Puntos de Fe"], "c": 1},
    {"q": "¿Qué criatura voladora puede agarrar a un humano pero no a un Rex?", "a": ["Pteranodon", "Argentavis", "Quetzal", "Wyvern"], "c": 1},
    {"q": "¿Cuál es el nivel máximo natural de un dinosaurio salvaje en dificultad oficial?", "a": ["100", "120", "150", "180"], "c": 2},
    {"q": "¿Qué objeto se usa para dormir dinosaurios de forma más efectiva?", "a": ["Garrote", "Flechas de Piedra", "Dardos Tranquilizantes", "Bolas"], "c": 2},
    {"q": "¿Qué dinosaurio es el mejor para recolectar piedra?", "a": ["Ankylo", "Doedicurus", "Mammoth", "Castoroides"], "c": 1},
    {"q": "¿En qué mapa apareció por primera vez el Griffin?", "a": ["The Center", "Ragnarok", "Valguero", "Crystal Isles"], "c": 1},
    {"q": "¿Qué criatura se domestica de forma pasiva dándole cerveza?", "a": ["Chalicotherium", "Gigantopithecus", "Mesopithecus", "Lystrosaurus"], "c": 0},
]


# ════════════════════════════════════════════════════════════
#  Minas
# ════════════════════════════════════════════════════════════

class MinasView(View):
    """Vista interactiva del juego de minas."""

    def __init__(self, ctx: commands.Context, economy: UserEconomy, amount: int):
        super().__init__(timeout=60)
        self.ctx     = ctx
        self.economy = economy
        self.amount  = amount
        self.message = None
        self.grid    = [0] * 20  # 0: seguro, 1: mina (Tablero 5x4)
        self.revealed = [False] * 20
        self.mines_count = 5  # Aumentado según pedido
        self.multiplier_step = 0.50  # Aumentado según pedido
        self.safe_clicks = 0
        self.game_over = False

        # Colocar minas aleatoriamente
        mine_indices = random.sample(range(20), self.mines_count)
        for idx in mine_indices:
            self.grid[idx] = 1

        # Crear botones (5 filas x 4 columnas = 20 botones)
        for i in range(20):
            row = i // 4
            btn = Button(label="?", style=discord.ButtonStyle.secondary, row=row, custom_id=f"mina_{i}")
            btn.callback = self._create_callback(i)
            self.add_item(btn)

        # Botón para retirarse
        self.cashout_btn = Button(label="💰 Retirarse (1.0x)", style=discord.ButtonStyle.green, row=4, disabled=True)
        self.cashout_btn.callback = self.cashout_callback
        self.add_item(self.cashout_btn)

    def _create_callback(self, idx: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("No es tu partida.", ephemeral=True)
                return
            if self.game_over or self.revealed[idx]:
                await interaction.response.defer()
                return

            self.revealed[idx] = True
            if self.grid[idx] == 1:
                # Perder (El dinero ya se descontó al inicio)
                self.game_over = True
                for child in self.children:
                    if isinstance(child, Button) and child.custom_id and child.custom_id.startswith("mina_"):
                        i = int(child.custom_id.split("_")[1])
                        child.label = "💣" if self.grid[i] == 1 else ""
                        child.style = discord.ButtonStyle.danger if self.grid[i] == 1 else discord.ButtonStyle.secondary
                    child.disabled = True
                
                embed = discord.Embed(
                    title="💥 ¡BOOM! Perdiste",
                    description=f"Has pisado una mina. Perdiste **{self.amount:,} monedas**.",
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                # Continuar
                self.safe_clicks += 1
                current_mult = round(1.0 + (self.safe_clicks * self.multiplier_step), 2)
                for child in self.children:
                    if isinstance(child, Button) and child.custom_id == f"mina_{idx}":
                        child.label = "💎"
                        child.style = discord.ButtonStyle.primary
                        child.disabled = True
                
                self.cashout_btn.disabled = False
                self.cashout_btn.label = f"💰 Retirarse ({current_mult}x)"
                
                embed = discord.Embed(
                    title="💎 Minas",
                    description=f"¡Casilla segura! Multiplicador actual: **{current_mult}x**\n¿Quieres seguir o retirarte?",
                    color=discord.Color.blue()
                )
                await interaction.response.edit_message(embed=embed, view=self)

        return callback

    async def cashout_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author or self.game_over:
            await interaction.response.defer()
            return
        
        self.game_over = True
        current_mult = round(1.0 + (self.safe_clicks * self.multiplier_step), 2)
        win_amount = int(self.amount * current_mult)
        self.economy.update_balance(self.ctx.author.id, win_amount)
        
        for child in self.children:
            child.disabled = True
            if isinstance(child, Button) and child.custom_id and child.custom_id.startswith("mina_"):
                i = int(child.custom_id.split("_")[1])
                if self.grid[i] == 1:
                    child.label = "💣"
        
        embed = discord.Embed(
            title="💰 ¡Retirada Exitosa!",
            description=f"Te has retirado con un multiplicador de **{current_mult}x**.\nGanancia: **{win_amount:,} monedas**.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        """Deshabilitar todo al expirar el tiempo."""
        if not self.game_over:
            self.game_over = True
            for child in self.children:
                child.disabled = True
            
            if self.message:
                embed = discord.Embed(
                    title="⏰ Tiempo Agotado",
                    description=f"La partida ha terminado por inactividad. Perdiste **{self.amount:,} monedas**.",
                    color=discord.Color.red()
                )
                try:
                    await self.message.edit(embed=embed, view=self)
                except:
                    pass

# ════════════════════════════════════════════════════════════
#  Blackjack
# ════════════════════════════════════════════════════════════

SUITS  = ["♠️", "♥️", "♦️", "♣️"]
RANKS  = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def _new_deck() -> list[str]:
    deck = [f"{r}{s}" for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck

def _card_value(card: str) -> int:
    rank = card[:-2]  # quitar el emoji de palo (2 chars)
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 11
    return int(rank)

def _hand_value(hand: list[str]) -> int:
    total = sum(_card_value(c) for c in hand)
    aces  = sum(1 for c in hand if c.startswith("A"))
    while total > 21 and aces:
        total -= 10
        aces  -= 1
    return total

def _hand_str(hand: list[str], hide_second: bool = False) -> str:
    if hide_second:
        return f"{hand[0]}  🂠"
    return "  ".join(hand)


class BlackjackView(View):
    """Vista interactiva de la partida de blackjack."""

    def __init__(
        self,
        ctx: commands.Context,
        economy: UserEconomy,
        amount: int,
        deck: list[str],
        player_hand: list[str],
        dealer_hand: list[str],
    ):
        super().__init__(timeout=60)
        self.ctx         = ctx
        self.economy     = economy
        self.amount      = amount
        self.deck        = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.message: discord.Message | None = None

    def _build_embed(self, result: str | None = None) -> discord.Embed:
        """Construye el embed con el estado actual de la partida."""
        hide = result is None  # ocultamos segunda carta del dealer mientras se juega
        player_val = _hand_value(self.player_hand)
        dealer_val = _hand_value(self.dealer_hand)

        if result:
            colors = {"🏆 ¡Ganaste!": discord.Color.green(),
                      "🤝 Empate": discord.Color.blurple(),
                      "💀 ¡Perdiste!": discord.Color.red(),
                      "🎉 ¡Blackjack!": discord.Color.gold()}
            color = colors.get(result, discord.Color.orange())
            title = f"🃏 Blackjack — {result}"
        else:
            color = discord.Color.dark_green()
            title = "🃏 Blackjack — Tu turno"

        embed = discord.Embed(title=title, color=color)
        embed.add_field(
            name=f"🤖 Dealer {'(???)' if hide else f'({dealer_val})'}",
            value=_hand_str(self.dealer_hand, hide_second=hide),
            inline=False
        )
        embed.add_field(
            name=f"🧑 Tú ({player_val})",
            value=_hand_str(self.player_hand),
            inline=False
        )
        if result:
            new_bal = self.economy.get_balance(self.ctx.author.id)
            embed.add_field(
                name="💵 Balance",
                value=f"{new_bal:,} monedas",
                inline=False
            )
        else:
            embed.set_footer(text=f"Apuesta: {self.amount:,} monedas | Tienes 60s para jugar.")
        return embed

    async def _end_game(self, interaction: discord.Interaction, result: str) -> None:
        for child in self.children:
            child.disabled = True
        self.stop()
        await interaction.response.edit_message(embed=self._build_embed(result), view=self)

    async def _dealer_play(self) -> None:
        """El dealer roba cartas hasta llegar a 17 o más."""
        while _hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())

    async def _resolve(self, interaction: discord.Interaction) -> None:
        await self._dealer_play()
        p = _hand_value(self.player_hand)
        d = _hand_value(self.dealer_hand)

        if d > 21 or p > d:
            self.economy.update_balance(self.ctx.author.id, self.amount)
            await self._end_game(interaction, "🏆 ¡Ganaste!")
        elif p == d:
            await self._end_game(interaction, "🤝 Empate")
        else:
            self.economy.update_balance(self.ctx.author.id, -self.amount)
            await self._end_game(interaction, "💀 ¡Perdiste!")

    @discord.ui.button(label="👊 Pedir carta", style=discord.ButtonStyle.green, custom_id="bj_hit")
    async def hit(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("No es tu partida.", ephemeral=True)
            return

        self.player_hand.append(self.deck.pop())
        total = _hand_value(self.player_hand)

        if total > 21:
            self.economy.update_balance(self.ctx.author.id, -self.amount)
            await self._end_game(interaction, "💀 ¡Perdiste!")
        elif total == 21:
            await self._resolve(interaction)
        else:
            await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="🛑 Plantarse", style=discord.ButtonStyle.red, custom_id="bj_stand")
    async def stand(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("No es tu partida.", ephemeral=True)
            return
        await self._resolve(interaction)

    async def on_timeout(self) -> None:
        """Si el jugador no responde, pierde la apuesta."""
        self.economy.update_balance(self.ctx.author.id, -self.amount)
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                embed = self._build_embed("💀 ¡Perdiste!")
                embed.set_footer(text="⏰ Tiempo agotado — perdiste la apuesta.")
                await self.message.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass


# ════════════════════════════════════════════════════════════
#  Cog
# ════════════════════════════════════════════════════════════

class Games(commands.Cog):
    """Minijuegos de economía."""

    def __init__(self, bot: commands.Bot, economy: UserEconomy):
        self.bot     = bot
        self.economy = economy

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Restringe todos los minijuegos al canal de economía."""
        if ctx.channel.id != ECO_CHANNEL_ID:
            await ctx.send(
                f"❌ Los minijuegos solo pueden usarse en <#{ECO_CHANNEL_ID}>.",
                delete_after=8
            )
            return False
        return True

    # ── !blackjack ────────────────────────────────────────────
    @commands.command(name="blackjack", aliases=["bj"])
    async def blackjack(self, ctx: commands.Context, amount: int):
        """Juega al blackjack contra el bot. Objetivo: llegar a 21 sin pasarte."""
        if amount <= 0:
            await ctx.send("❌ La apuesta debe ser mayor que 0.")
            return

        balance = self.economy.get_balance(ctx.author.id)
        if balance < amount:
            await ctx.send(f"❌ No tienes suficientes monedas. Tienes **{balance:,}**.")
            return

        deck         = _new_deck()
        player_hand  = [deck.pop(), deck.pop()]
        dealer_hand  = [deck.pop(), deck.pop()]

        # ¿Blackjack natural? (21 con 2 cartas)
        if _hand_value(player_hand) == 21:
            winnings = int(amount * 1.5)
            self.economy.update_balance(ctx.author.id, winnings)
            embed = discord.Embed(
                title="🎉 ¡Blackjack!",
                description=(
                    f"Tus cartas: {_hand_str(player_hand)}\n"
                    f"¡Blackjack natural! Ganas **{winnings:,} monedas** (x1.5)."
                ),
                color=discord.Color.gold()
            )
            embed.add_field(name="💵 Balance", value=f"{self.economy.get_balance(ctx.author.id):,} monedas")
            await ctx.send(embed=embed)
            return

        view    = BlackjackView(ctx, self.economy, amount, deck, player_hand, dealer_hand)
        message = await ctx.send(embed=view._build_embed(), view=view)
        view.message = message

    # ── !dados ────────────────────────────────────────────────
    @commands.command(name="dados")
    async def dados(self, ctx: commands.Context, oponente: discord.Member, amount: int):
        """Duelo de dados contra otro usuario. El que saque más suma, gana."""
        if oponente == ctx.author:
            await ctx.send("❌ No puedes retarte a ti mismo.")
            return
        if oponente.bot:
            await ctx.send("❌ No puedes retar a un bot.")
            return
        if amount <= 0:
            await ctx.send("❌ La apuesta debe ser mayor que 0.")
            return

        bal_reto   = self.economy.get_balance(ctx.author.id)
        bal_opone  = self.economy.get_balance(oponente.id)

        if bal_reto < amount:
            await ctx.send(f"❌ No tienes suficientes monedas (**{bal_reto:,}**).")
            return
        if bal_opone < amount:
            await ctx.send(f"❌ {oponente.mention} no tiene suficientes monedas (**{bal_opone:,}**).")
            return

        # Pedir confirmación al oponente
        confirm_embed = discord.Embed(
            title="🎲 ¡Reto de Dados!",
            description=(
                f"{ctx.author.mention} te reta a un duelo de dados.\n"
                f"Apuesta: **{amount:,} monedas**\n\n"
                "¿Aceptas el reto? Tienes 30 segundos."
            ),
            color=discord.Color.orange()
        )

        accept_btn = Button(label="✅ Aceptar", style=discord.ButtonStyle.green, custom_id="dados_accept")
        reject_btn = Button(label="❌ Rechazar", style=discord.ButtonStyle.red,   custom_id="dados_reject")
        confirm_view = View(timeout=30)
        confirm_view.add_item(accept_btn)
        confirm_view.add_item(reject_btn)
        accepted = [False]

        async def on_accept(interaction: discord.Interaction):
            if interaction.user != oponente:
                await interaction.response.send_message("No es tu reto.", ephemeral=True)
                return
            accepted[0] = True
            confirm_view.stop()
            for child in confirm_view.children:
                child.disabled = True
            await interaction.response.edit_message(view=confirm_view)

        async def on_reject(interaction: discord.Interaction):
            if interaction.user != oponente:
                await interaction.response.send_message("No es tu reto.", ephemeral=True)
                return
            confirm_view.stop()
            for child in confirm_view.children:
                child.disabled = True
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="❌ Reto Rechazado",
                    description=f"{oponente.mention} ha rechazado el duelo.",
                    color=discord.Color.red()
                ),
                view=confirm_view
            )

        accept_btn.callback = on_accept
        reject_btn.callback = on_reject

        msg = await ctx.send(embed=confirm_embed, view=confirm_view)
        await confirm_view.wait()

        if not accepted[0]:
            return  # rechazado o timeout

        # ── Tirar dados ───────────────────────────────────────
        await asyncio.sleep(1)

        d1_r = [random.randint(1, 6), random.randint(1, 6)]
        d2_r = [random.randint(1, 6), random.randint(1, 6)]
        suma_r = sum(d1_r)
        suma_o = sum(d2_r)

        dados_emoji = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣"]

        result_embed = discord.Embed(title="🎲 Duelo de Dados — Resultado", color=discord.Color.blurple())
        result_embed.add_field(
            name=f"🎮 {ctx.author.display_name}",
            value=f"{dados_emoji[d1_r[0]-1]} + {dados_emoji[d1_r[1]-1]} = **{suma_r}**",
            inline=True
        )
        result_embed.add_field(
            name=f"🎮 {oponente.display_name}",
            value=f"{dados_emoji[d2_r[0]-1]} + {dados_emoji[d2_r[1]-1]} = **{suma_o}**",
            inline=True
        )

        if suma_r > suma_o:
            self.economy.update_balance(ctx.author.id, amount)
            self.economy.update_balance(oponente.id, -amount)
            result_embed.add_field(
                name="🏆 Ganador",
                value=f"{ctx.author.mention} gana **{amount:,} monedas**.",
                inline=False
            )
            result_embed.color = discord.Color.green()
        elif suma_o > suma_r:
            self.economy.update_balance(oponente.id, amount)
            self.economy.update_balance(ctx.author.id, -amount)
            result_embed.add_field(
                name="🏆 Ganador",
                value=f"{oponente.mention} gana **{amount:,} monedas**.",
                inline=False
            )
            result_embed.color = discord.Color.red()
        else:
            result_embed.add_field(
                name="🤝 Empate",
                value="Nadie gana ni pierde monedas.",
                inline=False
            )
            result_embed.color = discord.Color.blurple()

        await msg.edit(embed=result_embed, view=None)

    # ── !pesca ────────────────────────────────────────────────
    @commands.command(name="pesca", aliases=["pescar"])
    async def pesca(self, ctx: commands.Context):
        """Lanza la caña y a ver qué pescas. Cooldown de 20 minutos."""
        now    = datetime.now(timezone.utc)
        last   = _fish_cooldowns.get(ctx.author.id)
        cd_end = last + timedelta(minutes=FISH_COOLDOWN_MINUTES) if last else None

        if cd_end and now < cd_end:
            remaining = int((cd_end - now).total_seconds() / 60)
            await ctx.send(
                f"🎣 Aún tienes que esperar **{remaining} min** para volver a pescar.",
                delete_after=10
            )
            return

        _fish_cooldowns[ctx.author.id] = now

        # Animación
        wait_embed = discord.Embed(
            title="🎣 Lanzando la caña...",
            description="Esperando que pique algo...",
            color=discord.Color.blue()
        )
        msg = await ctx.send(embed=wait_embed)
        await asyncio.sleep(random.uniform(2.0, 3.5))

        # Tabla de capturas (ponderada)
        catches = [
            # (nombre, emoji, monedas_min, monedas_max, peso)
            ("Bota vieja",          "🥾", 0,    0,    15),
            ("Sardina",             "🐟", 30,   80,   35),
            ("Lubina",              "🐠", 80,   150,  25),
            ("Trucha arcoíris",     "🌈", 150,  300,  12),
            ("Pez espada",          "⚔️", 300,  600,   8),
            ("Tiburón",             "🦈", 600,  1200,  4),
            ("Cofre del tesoro",    "💎", 1200, 2500,  1),
        ]
        names  = [c[0] for c in catches]
        emojis = [c[1] for c in catches]
        mins   = [c[2] for c in catches]
        maxs   = [c[3] for c in catches]
        weights = [c[4] for c in catches]

        idx   = random.choices(range(len(catches)), weights=weights, k=1)[0]
        name  = names[idx]
        emoji = emojis[idx]
        coins = random.randint(mins[idx], maxs[idx])

        if coins == 0:
            color = discord.Color.dark_grey()
            title = f"{emoji} ¡Has pescado una {name}!"
            desc  = "Vaya... no hay monedas aquí. Mejor suerte la próxima vez."
        elif idx >= 5:
            color = discord.Color.gold()
            title = f"{emoji} ¡CAPTURA LEGENDARIA — {name}!"
            desc  = f"¡Increíble! Has conseguido **{coins:,} monedas**. 🎉"
            self.economy.update_balance(ctx.author.id, coins)
        else:
            color = discord.Color.green()
            title = f"{emoji} ¡Has pescado {name}!"
            desc  = f"La has vendido y has ganado **{coins:,} monedas**."
            self.economy.update_balance(ctx.author.id, coins)

        result_embed = discord.Embed(title=title, description=desc, color=color)
        result_embed.set_footer(
            text=f"Balance: {self.economy.get_balance(ctx.author.id):,} monedas | "
                 f"Próxima pesca en {FISH_COOLDOWN_MINUTES} min."
        )
        await msg.edit(embed=result_embed)

    # ── !trivia ───────────────────────────────────────────────
    @commands.command(name="trivia")
    async def trivia(self, ctx: commands.Context):
        """Responde una pregunta correctamente para ganar monedas."""
        item = random.choice(TRIVIA_QUESTIONS)
        question = item["q"]
        options  = item["a"]
        correct  = item["c"]
        reward   = 200

        embed = discord.Embed(
            title="🧠 Trivia",
            description=f"**Pregunta:** {question}\n\nResponde seleccionando un botón. Tienes 20 segundos.",
            color=discord.Color.blue()
        )

        view = View(timeout=20)
        answered = [False]

        for i, opt in enumerate(options):
            btn = Button(label=opt, style=discord.ButtonStyle.secondary, custom_id=f"trivia_{i}")

            async def callback(interaction: discord.Interaction, idx=i):
                if answered[0]: return
                if interaction.user != ctx.author:
                    await interaction.response.send_message("No es tu trivia.", ephemeral=True)
                    return
                
                answered[0] = True
                for child in view.children:
                    child.disabled = True
                    if int(child.custom_id.split("_")[1]) == correct:
                        child.style = discord.ButtonStyle.green
                    elif int(child.custom_id.split("_")[1]) == idx:
                        child.style = discord.ButtonStyle.red

                if idx == correct:
                    self.economy.update_balance(ctx.author.id, reward)
                    res_embed = discord.Embed(
                        title="✅ ¡Correcto!",
                        description=f"Has acertado y ganado **{reward:,} monedas**.",
                        color=discord.Color.green()
                    )
                else:
                    res_embed = discord.Embed(
                        title="❌ ¡Incorrecto!",
                        description=f"La respuesta correcta era: **{options[correct]}**.",
                        color=discord.Color.red()
                    )
                await interaction.response.edit_message(embed=res_embed, view=view)

            btn.callback = callback
            view.add_item(btn)

        await ctx.send(embed=embed, view=view)

    # ── !minas ────────────────────────────────────────────────
    @commands.command(name="minas")
    async def minas(self, ctx: commands.Context, amount: int):
        """Juego de minas. Revela casillas seguras para aumentar tu multiplicador."""
        if amount <= 0:
            await ctx.send("❌ La apuesta debe ser mayor que 0.")
            return

        balance = self.economy.get_balance(ctx.author.id)
        if balance < amount:
            await ctx.send(f"❌ No tienes suficientes monedas. Tienes **{balance:,}**.")
            return

        # Descontar apuesta al inicio
        self.economy.update_balance(ctx.author.id, -amount)

        embed = discord.Embed(
            title="💎 Minas",
            description=f"Apuesta: **{amount:,} monedas**\nRevela las gemas y evita las minas.\n\n*El dinero ha sido retirado de tu cuenta.*",
            color=discord.Color.blue()
        )
        view = MinasView(ctx, self.economy, amount)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ── !rasca ────────────────────────────────────────────────
    @commands.command(name="rasca")
    async def rasca(self, ctx: commands.Context, amount: int):
        """Juego de Rasca y Gana. Encuentra símbolos iguales para ganar."""
        if amount <= 0:
            await ctx.send("❌ La apuesta debe ser mayor que 0.")
            return

        balance = self.economy.get_balance(ctx.author.id)
        if balance < amount:
            await ctx.send(f"❌ No tienes suficientes monedas. Tienes **{balance:,}**.")
            return

        self.economy.update_balance(ctx.author.id, -amount)

        embed = discord.Embed(
            title="🎫 Rasca y Gana",
            description=f"Apuesta: **{amount:,} monedas**\n¡Haz clic en los botones para revelar los símbolos! Busca coincidencias.",
            color=discord.Color.gold()
        )
        view = RascaView(ctx, self.economy, amount)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


class RascaView(View):
    """Vista interactiva del Rasca y Gana."""
    def __init__(self, ctx, economy, amount):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.economy = economy
        self.amount = amount
        self.message = None
        self.symbols_pool = [
            "🍒", "🍋", "🍊", "🍇", "🍉", "🍓", "🍍", "🥝", "🥥", "🫐",
            "🍈", "🍐", "🍏", "🍎", "🍑", "🍌", "🍅", "🍆", "🥕", "🌽",
            "💎", "🔔", "7️⃣", "⭐", "💰"
        ]
        self.grid = [random.choice(self.symbols_pool) for _ in range(9)]
        self.revealed = [False] * 9
        self.clicks = 0

        for i in range(9):
            btn = Button(label="❓", style=discord.ButtonStyle.secondary, row=i//3, custom_id=f"rasca_{i}")
            btn.callback = self._create_callback(i)
            self.add_item(btn)

    def _create_callback(self, idx):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("No es tu cartón.", ephemeral=True)
                return
            if self.revealed[idx]:
                await interaction.response.defer()
                return

            self.revealed[idx] = True
            self.clicks += 1
            symbol = self.grid[idx]

            for child in self.children:
                if isinstance(child, Button) and child.custom_id == f"rasca_{idx}":
                    child.label = symbol
                    child.style = discord.ButtonStyle.primary
                    child.disabled = True

            if self.clicks == 9:
                # Calcular premio
                counts = {}
                for s in self.grid:
                    counts[s] = counts.get(s, 0) + 1
                
                max_rep = max(counts.values())
                win_mult = 0
                if max_rep >= 7: win_mult = 50
                elif max_rep == 6: win_mult = 20
                elif max_rep == 5: win_mult = 8
                elif max_rep == 4: win_mult = 2.5
                elif max_rep == 3: win_mult = 1.0
                
                win_amount = int(self.amount * win_mult)
                if win_amount > 0:
                    self.economy.update_balance(self.ctx.author.id, win_amount)
                    if win_mult > 1.0:
                        desc = f"🎉 ¡Felicidades! Tuviste {max_rep} coincidencias.\nGanaste: **{win_amount:,} monedas**."
                        color = discord.Color.green()
                    else:
                        desc = f"⚖️ Tuviste 3 coincidencias. Recuperas tu apuesta de **{win_amount:,} monedas**."
                        color = discord.Color.blue()
                else:
                    desc = "😢 No hubo suerte esta vez. Necesitas al menos 3 iguales para no perder."
                    color = discord.Color.red()

                embed = discord.Embed(title="🎫 Resultado: Rasca y Gana", description=desc, color=color)
                await interaction.response.edit_message(embed=embed, view=self)
                self.stop()
            else:
                await interaction.response.edit_message(view=self)
        return callback

    async def on_timeout(self) -> None:
        if self.message:
            for child in self.children:
                child.disabled = True
            embed = discord.Embed(
                title="⏰ Tiempo Agotado",
                description=f"El cartón ha caducado por inactividad. Perdiste **{self.amount:,} monedas**.",
                color=discord.Color.red()
            )
            try:
                await self.message.edit(embed=embed, view=self)
            except:
                pass


async def setup(bot: commands.Bot, economy: UserEconomy):
    await bot.add_cog(Games(bot, economy))
