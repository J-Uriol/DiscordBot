import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import asyncio
import json
import sqlite3

# Configuración del bot (reemplaza con valores de ejemplo)
WELCOME_CHANNEL_ID = 123456789012345678  # ID de ejemplo para el canal de bienvenida
TICKET_CATEGORY_ID = 123456789012345678  # ID de ejemplo para la categoría de tickets
MOD_ROLE_ID = 123456789012345678  # ID de ejemplo para el rol de moderador
CANAL_SUGERENCIAS_ID = 123456789012345678  # ID de ejemplo para el canal de sugerencias
WARN_CHANNEL_ID = 123456789012345678  # ID de ejemplo para el canal de advertencias

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)  # Prefijo del bot

@bot.event
async def on_ready():
    bot.add_view(TicketView())  # Registrar vista de tickets
    bot.add_view(CloseTicketView(None))  # Registrar vista para cerrar tickets
    print(f'{bot.user.name} ha iniciado sesión.')
    await bot.change_presence(activity=discord.Streaming(name="EjemploBot", url="https://www.twitch.tv/ejemplo"))

@bot.event
async def on_member_join(member):
    try:
        channel = await bot.fetch_channel(WELCOME_CHANNEL_ID)
        if channel:
            await channel.send(f"**¿Qué te trae por aquí {member.mention}?** ")
            embed = discord.Embed(
                title="¡Bienvenido a la Comunidad de Ejemplo!",
                description=f"¡Nos alegra tenerte con nosotros, {member.name}!\n\n"
                            "- No olvides leer las reglas y pasar por los canales de presentación para conocerte mejor con los demás.",
                color=discord.Color.orange()
            )
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)
            embed.set_image(url="https://example.com/welcome-image.jpg")  # Imagen de bienvenida de ejemplo
            await channel.send(embed=embed)
    except Exception as e:
        print(f"Error al enviar mensaje de bienvenida: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando no encontrado. Usa `!ayuda` para ver los disponibles.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permisos para usar este comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Argumentos faltantes. Revisa la sintaxis del comando.")
    else:
        await ctx.send("❌ Ha ocurrido un error inesperado.")
        print(error)

# Comandos del bot
@bot.command(name="ping")
async def ping(ctx):
    """Muestra la latencia del bot."""
    latency = round(bot.latency * 1000)  # Latencia en milisegundos
    await ctx.send(f"{ctx.author.mention} Pong 🏓 Latencia: {latency} ms.")

@bot.command(name="redes")
async def redes(ctx):
    """Muestra las redes sociales oficiales (ejemplo)."""
    embed = discord.Embed(
        title="¡Conoce mis redes sociales!",
        description="Aquí puedes encontrar todas mis redes sociales oficiales:",
        color=discord.Color.orange()
    )
    embed.add_field(name="Instagram", value="[@Ejemplo_Instagram](https://www.instagram.com/ejemplo/)", inline=False)
    embed.add_field(name="YouTube", value="[@Ejemplo_YouTube](https://www.youtube.com/channel/ejemplo)", inline=False)
    embed.add_field(name="X (antes Twitter)", value="[@Ejemplo_Twitter](https://x.com/ejemplo)", inline=False)
    embed.add_field(name="Twitch", value="[@Ejemplo_Twitch](https://www.twitch.tv/ejemplo)", inline=False)
    embed.set_footer(text=f"¡Gracias por tu apoyo, {ctx.author.name}!")
    embed.set_thumbnail(url="https://example.com/logo.jpg")  # Logo de ejemplo
    embed.set_image(url="https://example.com/banner.jpg")  # Banner de ejemplo
    await ctx.send(embed=embed)

@bot.command(name="info")
async def info(ctx):
    """Muestra información sobre el bot."""
    embed = discord.Embed(
        title="Información sobre el bot",
        description="Soy el bot oficial de la comunidad de ejemplo. 😄",
        color=discord.Color.orange()
    )
    embed.add_field(name="Creador", value="EjemploDev", inline=False)
    embed.add_field(name="Versión", value="1.0.0", inline=False)
    embed.add_field(name="Fecha de creación", value="Enero 2023", inline=False)
    embed.set_footer(text="¡Gracias por ser parte de nuestra comunidad! 🌟")
    await ctx.send(embed=embed)

# Lista de comandos por categoría
comandos = {
    "General": [
        ("!redes", "Muestra las redes sociales oficiales de ejemplo."),
        ("!ping", "Muestra el ping con el servidor."),
        ("!info", "Muestra información del bot."),
        ("!sugerencia", "Añade una sugerencia en el canal de sugerencias.")
    ],
    "Diversión": [
        ("!moneda", "Tira una moneda (cara o cruz)."),
        ("!suerte", "Haz una pregunta y obtén una respuesta al estilo de la bola mágica."),
        ("!memide", "El bot te dice cuánto te mide, aleatoriamente."),
        ("!rps", "Juega piedra, papel o tijera contra el bot."),
    ],
    "Administración": [
        ("!say", "El bot repite el mensaje (solo administradores pueden usarlo)."),
        ("!clear", "Borra un número de mensajes en el canal (solo administradores pueden usarlo)."),
        ("!warn", "Añade un warn al usuario y notifica por privado.")
    ],
}

@bot.command(name="ayuda")
async def help_command(ctx):
    """Muestra la lista de comandos disponibles con submenús usando botones."""
    embed = discord.Embed(
        title="Comandos Disponibles",
        description="Aquí está la lista de comandos que puedes usar:",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url="https://example.com/logo.jpg")  # Logo de ejemplo

    # Agregar la primera página (General)
    embed.add_field(name="Categoría: General", value="\n".join([f"**{cmd}**: {desc}" for cmd, desc in comandos["General"]]), inline=False)
    embed.set_footer(text="Página 1/3 - Usa los botones para navegar.")

    # Crear los botones con emojis y colores
    boton_general = Button(
        style=discord.ButtonStyle.primary,
        label="General",
        custom_id="general",
        emoji="📋"
    )
    boton_diversion = Button(
        style=discord.ButtonStyle.success,
        label="Diversión",
        custom_id="diversion",
        emoji="🎮"
    )
    boton_administracion = Button(
        style=discord.ButtonStyle.danger,
        label="Administración",
        custom_id="administracion",
        emoji="🛠️"
    )

    # Crear la vista y agregar los botones
    view = View()
    view.add_item(boton_general)
    view.add_item(boton_diversion)
    view.add_item(boton_administracion)

    # Enviar el mensaje con los botones
    mensaje = await ctx.send(embed=embed, view=view)

    # Función para manejar las interacciones de los botones
    async def button_callback(interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("No puedes interactuar con este menú.", ephemeral=True)
            return

        categoria = interaction.data["custom_id"]

        if categoria == "general":
            embed.clear_fields()
            embed.add_field(name="Categoría: General", value="\n".join([f"**{cmd}**: {desc}" for cmd, desc in comandos["General"]]), inline=False)
            embed.set_footer(text="Página 1/3 - Usa los botones para navegar.")
        elif categoria == "diversion":
            embed.clear_fields()
            embed.add_field(name="Categoría: Diversión", value="\n".join([f"**{cmd}**: {desc}" for cmd, desc in comandos["Diversión"]]), inline=False)
            embed.set_footer(text="Página 2/3 - Usa los botones para navegar.")
        elif categoria == "administracion":
            embed.clear_fields()
            embed.add_field(name="Categoría: Administración", value="\n".join([f"**{cmd}**: {desc}" for cmd, desc in comandos["Administración"]]), inline=False)
            embed.set_footer(text="Página 3/3 - Usa los botones para navegar.")

        await interaction.response.edit_message(embed=embed, view=view)

    # Asignar la función de callback a cada botón
    boton_general.callback = button_callback
    boton_diversion.callback = button_callback
    boton_administracion.callback = button_callback

@bot.command(name="moneda")
async def flip_coin(ctx):
    """Tira una moneda (cara o cruz)."""
    resultado = random.choice(["Cara", "Cruz"])
    await ctx.send(f"{ctx.author.mention} La moneda ha salido: {resultado}")

@bot.command(name="suerte")
async def eight_ball(ctx):
    """Responde al estilo de la bola mágica."""
    respuestas = [
        "El bot dice que: Bien.", "El bot dice que: Mal.", "El bot dice que: Tal vez.",
        "El bot dice que: Definitivamente sí.", "El bot dice que: No cuentes con ello.",
        "El bot dice que: Claro que sí.", "El bot dice que: Parece que sí.",
        "El bot dice que: Mejor no te digo nada.", "El bot dice que: No estoy seguro, vuelve a intentarlo."
    ]
    respuesta = random.choice(respuestas)
    await ctx.send(f"{ctx.author.mention} {respuesta}")

@bot.command(name="memide")
async def me_mide(ctx):
    tamaños = ["2 cm 😳", "5 cm 😢", "10 cm 🫠", "15 cm 😏", "20 cm 😎", "30 cm 🔥"]
    medida = random.choice(tamaños)
    await ctx.send(f"{ctx.author.mention} El bot dice que te mide {medida} ")

@bot.command(name="rps")
async def piedra_papel_tijeras(ctx, eleccion: str):
    opciones = ["piedra", "papel", "tijeras"]
    eleccion = eleccion.lower()

    if eleccion not in opciones:
        await ctx.send("✋ Opciones válidas: piedra, papel o tijeras.")
        return

    bot_choice = random.choice(opciones)
    resultado = ""

    if eleccion == bot_choice:
        resultado = "🤝 Empate."
    elif (eleccion == "piedra" and bot_choice == "tijeras") or \
         (eleccion == "papel" and bot_choice == "piedra") or \
         (eleccion == "tijeras" and bot_choice == "papel"):
        resultado = "🎉 ¡Ganaste!"
    else:
        resultado = "😢 Perdiste."

    await ctx.send(f"🆚 {ctx.author.mention} eligió `{eleccion}`. Yo elegí `{bot_choice}`. {resultado}")

@bot.command(name="say")
@commands.has_permissions(administrator=True)
async def say(ctx, *, message: str):
    """El bot repite el mensaje (solo administradores pueden usarlo)."""
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name="clear")
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    """Borra un número de mensajes en el canal (solo administradores pueden usarlo)."""
    if amount < 1:
        await ctx.send("Por favor, ingresa un número mayor que 0.")
        return

    await ctx.channel.purge(limit=amount + 1)

class TicketView(View):
    """Vista con el botón para abrir un ticket."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Abrir Ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user

        existing_ticket = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
        if existing_ticket:
            await interaction.response.send_message("❌ Ya tienes un ticket abierto.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
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
            description=f"Hola {user.mention}, un moderador te atenderá pronto.\n\n"
                        "**🔸 Regla básica:** Sé claro con tu solicitud y respeta al staff.",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url="https://example.com/ticket-icon.png")  # Icono de ticket de ejemplo
        embed.set_footer(text="🛠️ Usa el botón de abajo para cerrar el ticket.")

        await ticket_channel.send(embed=embed, view=CloseTicketView(ticket_channel))
        await interaction.response.send_message(f"✅ Ticket creado: {ticket_channel.mention}", ephemeral=True)

class CloseTicketView(View):
    """Vista con el botón para cerrar el ticket."""
    def __init__(self, channel=None):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label="🔒 Cerrar Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not self.channel:
            self.channel = interaction.channel
        await interaction.response.send_message("⏳ Cerrando ticket en 5 segundos...", ephemeral=True)
        await asyncio.sleep(5)
        await self.channel.delete()

@bot.command(name="ticket")
@commands.has_permissions(administrator=True)
async def ticket(ctx):
    """Comando para enviar el mensaje con el botón de abrir ticket."""
    embed = discord.Embed(
        title="📌 Sistema de Tickets - Ejemplo",
        description="Si necesitas ayuda, abre un ticket con el botón de abajo.\n\n"
                    "🔸 **Soporte técnico**\n"
                    "🔸 **Reportes y quejas**\n"
                    "🔸 **Consultas generales**",
        color=discord.Color.orange()
    )
    embed.set_image(url="https://example.com/ticket-banner.jpg")  # Banner de ticket de ejemplo
    embed.set_footer(text="📌 Nuestro staff responderá lo antes posible.")

    await ctx.send(embed=embed, view=TicketView())

# Diccionario para llevar el control de votos por mensaje
votos = {}

class Votacion(View):
    def __init__(self, mensaje_id, mensaje_original, mensaje_sugerencia):
        super().__init__()
        self.mensaje_id = mensaje_id
        self.mensaje_original = mensaje_original
        self.mensaje_sugerencia = mensaje_sugerencia  # Guardar la sugerencia como texto
        self.votos_positivos = 0
        self.votos_negativos = 0
        self.usuarios_que_votaron = set()  # Conjunto para almacenar los usuarios que ya votaron

    @discord.ui.button(label="👍 Voto positivo", style=discord.ButtonStyle.green)
    async def voto_positivo(self, interaction: discord.Interaction, button: Button):
        """Gestiona el voto positivo."""
        # Verificar si el usuario ya ha votado
        if interaction.user.id in self.usuarios_que_votaron:
            await interaction.response.send_message("¡Ya has votado! Solo puedes votar una vez.", ephemeral=True)
            return

        # Registrar el voto del usuario
        self.votos_positivos += 1
        self.usuarios_que_votaron.add(interaction.user.id)  # Agregar al conjunto de usuarios que votaron

        await interaction.response.send_message(f"Gracias por tu voto positivo. Votos positivos: {self.votos_positivos}, negativos: {self.votos_negativos}", ephemeral=True)
        await self.actualizar_mensaje(interaction.message)

    @discord.ui.button(label="👎 Voto negativo", style=discord.ButtonStyle.red)
    async def voto_negativo(self, interaction: discord.Interaction, button: Button):
        """Gestiona el voto negativo."""
        # Verificar si el usuario ya ha votado
        if interaction.user.id in self.usuarios_que_votaron:
            await interaction.response.send_message("¡Ya has votado! Solo puedes votar una vez.", ephemeral=True)
            return

        # Registrar el voto del usuario
        self.votos_negativos += 1
        self.usuarios_que_votaron.add(interaction.user.id)  # Agregar al conjunto de usuarios que votaron

        await interaction.response.send_message(f"Gracias por tu voto negativo. Votos positivos: {self.votos_positivos}, negativos: {self.votos_negativos}", ephemeral=True)
        await self.actualizar_mensaje(interaction.message)

    @discord.ui.button(label="✅ Finalizar sugerencia", style=discord.ButtonStyle.blurple)
    async def finalizar_sugerencia(self, interaction: discord.Interaction, button: Button):
        """Gestiona la finalización de la sugerencia solo por administradores."""
        # Verificar si el usuario es administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ No tienes permisos para finalizar la sugerencia.", ephemeral=True)
            return

        # Calcular el resultado
        if self.votos_positivos > self.votos_negativos:
            resultado = "Aprobada"
        else:
            resultado = "No aprobada"

        # Actualizar el embed con el resultado final
        embed = discord.Embed(
            title=f"Sugerencia de {self.mensaje_original.author.name}",
            description=self.mensaje_sugerencia,
            color=discord.Color.blue()
        )
        
        # Comprobamos si el usuario tiene un avatar
        avatar_url = self.mensaje_original.author.avatar.url if self.mensaje_original.author.avatar else "https://example.com/default-avatar.png"
        embed.set_footer(text=f"Enviado por {self.mensaje_original.author.name}")
        embed.set_thumbnail(url=avatar_url)
        
        embed.add_field(name="Votos positivos", value=str(self.votos_positivos), inline=True)
        embed.add_field(name="Votos negativos", value=str(self.votos_negativos), inline=True)
        embed.add_field(name="Estado", value=resultado, inline=False)

        await interaction.message.edit(embed=embed)

        # Desactivar el botón de finalizar sugerencia para evitar presionarlo de nuevo
        button.disabled = True
        await interaction.message.edit(view=self)

    async def actualizar_mensaje(self, mensaje):
        """Actualiza el mensaje con el contador de votos sin cambiar la foto del usuario."""
        embed = discord.Embed(
            title=f"Sugerencia de {self.mensaje_original.author.name}",
            description=self.mensaje_sugerencia,  # Usar el texto original de la sugerencia
            color=discord.Color.blue()
        )
        
        # Comprobamos si el usuario tiene un avatar
        avatar_url = self.mensaje_original.author.avatar.url if self.mensaje_original.author.avatar else "https://example.com/default-avatar.png"
        embed.set_footer(text=f"Enviado por {self.mensaje_original.author.name}")
        embed.set_thumbnail(url=avatar_url)  # Mantener el thumbnail original
        
        embed.add_field(name="Votos positivos", value=str(self.votos_positivos), inline=True)
        embed.add_field(name="Votos negativos", value=str(self.votos_negativos), inline=True)
        await mensaje.edit(embed=embed)

@bot.command(name="sugerencia")
async def sugerencia(ctx, *, mensaje: str):
    """Recibe una sugerencia de un usuario y la publica con botones para votar."""
    
    # Verificar si el comando se ejecutó en el canal correcto
    if ctx.channel.id != CANAL_SUGERENCIAS_ID:
        await ctx.send("❌ Las sugerencias solo pueden enviarse en el canal autorizado.")
        return

    # Crear el embed para la sugerencia
    embed = discord.Embed(
        title=f"Sugerencia de {ctx.author.name}",
        description=mensaje,
        color=discord.Color.orange()
    )
    
    # Comprobamos si el usuario tiene un avatar
    avatar_url = ctx.author.avatar.url if ctx.author.avatar else "https://example.com/default-avatar.png"
    embed.set_footer(text=f"Enviado por {ctx.author.name}")
    embed.set_thumbnail(url=avatar_url)  # Agregar el avatar del usuario como thumbnail

    # Crear la vista de votación
    view = Votacion(mensaje_id=ctx.message.id, mensaje_original=ctx.message, mensaje_sugerencia=mensaje)

    # Crear el botón para los administradores
    admin_button = Button(label="✅ Finalizar sugerencia", style=discord.ButtonStyle.blurple)

    # Añadir el botón solo si el usuario tiene permisos de administrador
    admin_view = View()
    admin_view.add_item(admin_button)

    # Crear el embed con los botones para votar y el botón de administrador
    mensaje_embed = await ctx.send(embed=embed, view=view)

    # Almacenamos el mensaje_id en el diccionario para futuras referencias
    votos[ctx.message.id] = view

    # Eliminar el mensaje original del usuario
    await ctx.message.delete()

# Conectar a la base de datos SQLite
conn = sqlite3.connect("warnings.db")
cursor = conn.cursor()

# Crear tabla si no existe
cursor.execute('''CREATE TABLE IF NOT EXISTS warnings (
                    user_id INTEGER,
                    reason TEXT
                )''')
conn.commit()


def tiene_rol(ctx):
    """Función para verificar si el usuario tiene el rol de moderador."""
    role = discord.utils.get(ctx.author.roles, id=MOD_ROLE_ID)
    return role is not None

@bot.command(name="warn")
async def warn(ctx, member: discord.Member, *, reason: str):
    """Advierte a un usuario y almacena el motivo en la base de datos."""
    if not tiene_rol(ctx):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    cursor.execute("INSERT INTO warnings (user_id, reason) VALUES (?, ?)", (member.id, reason))
    conn.commit()

    embed_dm = discord.Embed(
        title="⚠️ Has sido advertido",
        description=f"Motivo: {reason}\n\nSi crees que esto es un error, contacta con un moderador.",
        color=discord.Color.red()
    )
    embed_dm.set_footer(text=f"Servidor: ")
    embed_dm.set_thumbnail(url="Tu logo")

    try:
        await member.send(embed=embed_dm) 
    except discord.Forbidden:
        await ctx.send("❌ No he podido enviar un mensaje privado a este usuario.")

    # Embed para el canal de registro
    embed_warn = discord.Embed(
        title="🚨 Advertencia aplicada",
        description=f"{member.mention} ha sido advertido.",
        color=discord.Color.orange()
    )
    embed_warn.add_field(name="👤 Usuario", value=member.mention, inline=True)
    embed_warn.add_field(name="👮 Moderador", value=ctx.author.mention, inline=True)
    embed_warn.add_field(name="📌 Motivo", value=reason, inline=False)

    warn_channel = ctx.guild.get_channel(WARN_CHANNEL_ID)
    if warn_channel:
        await warn_channel.send(embed=embed_warn) 
    else:
        await ctx.send("❌ No se encontró el canal de advertencias.")

@bot.command(name="historial")
async def historial(ctx, member: discord.Member):
    """Muestra el historial de advertencias de un usuario."""
    if not tiene_rol(ctx):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    cursor.execute("SELECT reason FROM warnings WHERE user_id = ?", (member.id,))
    user_warnings = cursor.fetchall()

    if not user_warnings:
        await ctx.send(f"{member.mention} no tiene advertencias previas.")
    else:
        embed = discord.Embed(title=f"Historial de advertencias de {member.name}", color=discord.Color.red())
        for idx, warn in enumerate(user_warnings, start=1):
            embed.add_field(name=f"Advertencia {idx}", value=warn[0], inline=False)
        await ctx.send(embed=embed)



@bot.command(name="stats")
async def stats(ctx):
    """Muestra estadísticas del servidor."""
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 Estadísticas del Servidor: {guild.name}", color=discord.Color.blue())
    embed.add_field(name="👥 Miembros", value=str(guild.member_count), inline=False)
    embed.add_field(name="💬 Canales de Texto", value=str(len(guild.text_channels)), inline=False)
    embed.add_field(name="🔊 Canales de Voz", value=str(len(guild.voice_channels)), inline=False)
    await ctx.send(embed=embed)

bot.run("Tu token aqui")