# ============================================================
#  cogs/tickets.py — Sistema de tickets
# ============================================================

import discord
from discord.ext import commands
from discord.ui import Button, View
from config import TICKET_CATEGORY_ID, MOD_ROLE_ID


class CloseTicketView(View):
    """Vista con el botón para cerrar un ticket."""

    def __init__(self, channel: discord.TextChannel = None):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(
        label="🔒 Cerrar Ticket",
        style=discord.ButtonStyle.red,
        custom_id="close_ticket"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        # Usar el canal de la interacción si no se fijó en el constructor
        channel = self.channel or interaction.channel
        await interaction.response.send_message("⏳ Cerrando ticket...", ephemeral=True)
        await channel.delete()


class TicketView(View):
    """Vista con el botón para abrir un ticket."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📩 Abrir Ticket",
        style=discord.ButtonStyle.blurple,
        custom_id="open_ticket"
    )
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user  = interaction.user

        # Comprobar si ya existe un ticket abierto
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
        if existing:
            await interaction.response.send_message(
                "❌ Ya tienes un ticket abierto.", ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user:               discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        mod_role = guild.get_role(MOD_ROLE_ID)
        if mod_role:
            overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.name.lower()}",
            category=guild.get_channel(TICKET_CATEGORY_ID),
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Ticket de Soporte",
            description=(
                f"Hola {user.mention}, un moderador te atenderá pronto.\n\n"
                "**🔸 Regla básica:** Sé claro con tu solicitud y respeta al staff."
            ),
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url="https://i.ibb.co/rscspsR/Reportes-aka.png")
        embed.set_footer(text="🛠️ Usa el botón de abajo para cerrar el ticket.")

        await ticket_channel.send(embed=embed, view=CloseTicketView(ticket_channel))
        await interaction.response.send_message(
            f"✅ Ticket creado: {ticket_channel.mention}", ephemeral=True
        )


class Tickets(commands.Cog):
    """Sistema de tickets de soporte."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Registrar vistas persistentes
        bot.add_view(TicketView())
        bot.add_view(CloseTicketView())

    # ── !ticket ───────────────────────────────────────────────
    @commands.command(name="ticket")
    @commands.has_permissions(administrator=True)
    async def ticket(self, ctx: commands.Context):
        """Publica el panel de tickets (solo administradores)."""
        embed = discord.Embed(
            title="📌 Sistema de Tickets - AKA",
            description=(
                "Si necesitas ayuda, abre un ticket con el botón de abajo.\n\n"
                "🔸 **Soporte técnico**\n"
                "🔸 **Reportes y quejas**\n"
                "🔸 **Consultas generales**"
            ),
            color=discord.Color.orange()
        )
        embed.set_image(url="https://i.ibb.co/rscspsR/Reportes-aka.png")
        embed.set_footer(text="📌 Nuestro staff responderá lo antes posible.")
        await ctx.send(embed=embed, view=TicketView())


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
