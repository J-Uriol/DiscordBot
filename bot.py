import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import random
import asyncio
import sqlite3
import time
from datetime import datetime, timedelta
import os  

# Configuracion del bot
WELCOME_CHANNEL_ID = 1334545817054347264
TICKET_CATEGORY_ID = 1085501163081830410
MOD_ROLE_ID = 1314314275929591888
CANAL_SUGERENCIAS_ID = 1334647354682511423
WARN_CHANNEL_ID = 1335264623422865409
ROLES_IDS = [949439013817835531, 949040738899988520, 1335559691916279910]
USER_ID_NO_MENCIONAR = 454306880387547166
ROL_GANADOR_ID = 1404422238312075286
CANAL_ANUNCIOS_ID = 871470222886973543
URL_ANUNCIO = "https:\\pruebaxd"

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True  
steal_cooldowns = {}

bot = commands.Bot(command_prefix='!', intents=intents) #Prefijo

# Configuración de la economía
ECO_DB_NAME = "economy.db"
DAILY_AMOUNT = 200
WORK_MIN = 100
WORK_MAX = 500

# Conexión a base de datos de economía
eco_conn = sqlite3.connect(ECO_DB_NAME)
eco_cursor = eco_conn.cursor()

# Crear tablas si no existen
eco_cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    last_daily TEXT,
                    last_work TEXT
                )''')

eco_cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price INTEGER,
                    description TEXT
                )''')

eco_cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    PRIMARY KEY (user_id, item_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (item_id) REFERENCES items(item_id)
                )''')

eco_cursor.execute('''CREATE TABLE IF NOT EXISTS hall_of_fame (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month INTEGER,
    year INTEGER,
    user_id INTEGER,
    balance INTEGER
)''')

eco_cursor.execute('''CREATE TABLE IF NOT EXISTS task_state (
    key TEXT PRIMARY KEY,
    last_processed TEXT
)''')
eco_conn.commit()

# Base de datos para advertencias
def get_warn_db():
    conn = sqlite3.connect("warnings.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS warnings (
                    user_id INTEGER,
                    reason TEXT
                )''')
    return conn, cursor

@bot.event
async def on_ready():
    bot.add_view(TicketView())  
    bot.add_view(CloseTicketView(None))  
    print(f'{bot.user.name} ha iniciado sesión.')
    await bot.change_presence(activity=discord.Streaming(name="AkantorPlay13", url="https://www.twitch.tv/akantorplay13"))
    check_monthly_winner.start()

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

@tasks.loop(hours=24)
async def check_monthly_winner():
    now = datetime.now()
    if now.day != 1:
        return
    # Verificar si ya se procesó este mes
    eco_cursor.execute("SELECT last_processed FROM task_state WHERE key='monthly_winner'")
    last_processed = eco_cursor.fetchone()
    current_month = f"{now.year}-{now.month}"
    
    if last_processed and last_processed[0] == current_month:
        return

    guild = discord.utils.get(bot.guilds)
    if not guild:
        return

    # Sacar top 1
    eco_cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 1")
    result = eco_cursor.fetchone()
    if not result:
        return

    user_id, balance = result
    member = guild.get_member(user_id)
    if not member:
        return

    # Guardar en Hall of Fame
    eco_cursor.execute("INSERT INTO hall_of_fame (month, year, user_id, balance) VALUES (?, ?, ?, ?)",
                       (now.month - 1 or 12, now.year if now.month != 1 else now.year - 1, user_id, balance))
    
    # Actualizar estado de procesamiento
    eco_cursor.execute("REPLACE INTO task_state (key, last_processed) VALUES (?, ?)",
                       ('monthly_winner', current_month))
    eco_conn.commit()

    # Asignar rol
    role = guild.get_role(ROL_GANADOR_ID)
    if role:
        await member.add_roles(role)

    # Anunciar
    canal = guild.get_channel(CANAL_ANUNCIOS_ID)
    if canal:
        await canal.send(f"🏆 **Ganador del mes anterior:** {member.mention} con {balance:,} monedas.\n¡Felicidades! 🎉")

    # Reiniciar balances
    eco_cursor.execute("UPDATE users SET balance = 0")
    eco_conn.commit()

@check_monthly_winner.before_loop
async def before_check_monthly_winner():
    await bot.wait_until_ready()

@bot.event
async def on_member_join(member):
    try:
        # Obtener los roles válidos
        roles = [role for role_id in ROLES_IDS 
                 if (role := member.guild.get_role(role_id)) is not None]

        # Asignar roles
        if roles:
            await member.add_roles(*roles)
            print(f"Se han añadido los roles a {member.name}")

        # Obtener el canal de bienvenida
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            await channel.send(f"**¿Qué te trae por aquí {member.mention}?**")

            # Crear y enviar el embed de bienvenida
            embed = discord.Embed(
                title="¡Bienvenido a la Comunidad de PRUEBA!",
                description=f"¡Nos alegra tenerte con nosotros, {member.name}!\n\n"
                            "- No olvides leer las reglas y pasar por los canales de presentación para conocerte mejor con los demás.",
                color=discord.Color.orange()
            )
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)
            embed.set_image(url=URL_ANUNCIO)

            await channel.send(embed=embed)
    except Exception as e:
        print(f"Error al procesar la bienvenida de {member.name}: {e}")

class UserEconomy:
    @staticmethod
    def get_user(user_id):
        eco_cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return eco_cursor.fetchone()

    @staticmethod
    def create_user(user_id):
        eco_cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
        eco_conn.commit()

    @staticmethod
    def update_balance(user_id, amount):
        if not UserEconomy.get_user(user_id):
            UserEconomy.create_user(user_id)
        
        eco_cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        eco_conn.commit()

    @staticmethod
    def get_balance(user_id):
        user = UserEconomy.get_user(user_id)
        if not user:
            UserEconomy.create_user(user_id)
            return 0
        return user[1]

    @staticmethod
    def set_last_daily(user_id):
        now = datetime.now().isoformat()
        eco_cursor.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (now, user_id))
        eco_conn.commit()

    @staticmethod
    def can_claim_daily(user_id):
        user = UserEconomy.get_user(user_id)
        if not user or not user[2]:
            return True
        
        last_daily = datetime.fromisoformat(user[2])
        return datetime.now() - last_daily >= timedelta(hours=24)

    @staticmethod
    def set_last_work(user_id):
        now = datetime.now().isoformat()
        eco_cursor.execute("UPDATE users SET last_work = ? WHERE user_id = ?", (now, user_id))
        eco_conn.commit()

    @staticmethod
    def can_work(user_id):
        user = UserEconomy.get_user(user_id)
        if not user or not user[3]:
            return True
        
        last_work = datetime.fromisoformat(user[3])
        return datetime.now() - last_work >= timedelta(hours=1)

# Comandos del bot
@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"{ctx.author.mention} Pong 🏓 Latencia: {latency} ms.")

@bot.command(name="redes")
async def redes(ctx):
    embed = discord.Embed(
        title="¡Conoce mis redes sociales!",
        description="Aquí puedes encontrar todas mis redes sociales oficiales:",
        color=discord.Color.orange()
    )
    embed.add_field(name="Instagram", value="[@prueba](https://www.instagram.com/prueba/)", inline=False)
    embed.add_field(name="YouTube", value="[@prueba](https://www.youtube.com/channel/prueba)", inline=False)
    embed.add_field(name="X (antes Twitter)", value="[@prueba](https://x.com/prueba)", inline=False)
    embed.add_field(name="Twitch", value="[@Akantorplay](https://www.twitch.tv/prueba)", inline=False)
    embed.set_footer(text=f"¡Gracias por tu apoyo, {ctx.author.name}!")
    embed.set_thumbnail(url="")
    embed.set_image(url="")
    await ctx.send(embed=embed)

@bot.command(name="info")
async def info(ctx):
    embed = discord.Embed(
        title="Información sobre el bot",
        description="Soy el bot oficial de la comunidad PRUEBA. 😄",
        color=discord.Color.orange()
    )
    embed.add_field(name="Creador", value="jav1ermzn", inline=False)
    embed.add_field(name="Versión", value="2.0.0", inline=False)
    embed.add_field(name="Fecha de creación", value="Enero 2025", inline=False)
    embed.set_footer(text="¡Gracias por ser parte de nuestra comunidad! 🌟")
    await ctx.send(embed=embed)

@bot.command(name="pc")
async def pc(ctx):
    embed = discord.Embed(
        title="Información del PC de PRUEBA",
        description="Componentes del ordenador de PRUEBA",
        color=discord.Color.orange()
    )
    embed.add_field(name="Procesador", value="Intel Core i7-14700KF", inline=False)
    embed.add_field(name="Tarjeta gráfica", value="NVIDIA GeForce RTX 4070 Ti Super", inline=False)
    embed.add_field(name="Memoria RAM", value="32 GB (16 GB x 2) DDR5", inline=False)
    embed.set_thumbnail(url="https://i.ibb.co/PZStwmWm/Nuevo-logo-1-2.jpg")
    await ctx.send(embed=embed)

# Lista de comandos por categoría
comandos = {
    "General": [
        ("!redes", "Muestra las redes sociales oficiales de Akantor."),
        ("!ping", "Muestra el ping con el servidor."),
        ("!info", "Muestra información del bot."),
        ("!sugerencia", "Añade una sugerencia en el canal de sugerencias."),
        ("!pc", "Muestra las especificaciones del ordenador de Akantor"),
        ("!stats", "Muestra las estadisticas del servidor"),
    ],
    "Diversión": [
        ("!moneda", "Tira una moneda (cara o cruz)."),
        ("!suerte", "Haz una pregunta y obtén una respuesta al estilo de la bola mágica."),
        ("!memide", "Aka te dice cuánto te mide, aleatoriamente."),
        ("!rps", "Juegas un piedra papel tijera contra Aka (piedra , papel , tijera)"),
    ],
    "Administración": [
        ("!say", "El bot repite el mensaje (solo administradores pueden usarlo)."),
        ("!clear", "Borra un número de mensajes en el canal (solo administradores pueden usarlo)."),
        ("!warn", "Añade un warn al usuario y notifica por privado"),
    ],
    "Economía": [
        ("!balance [usuario]", "Muestra el balance de un usuario."),
        ("!daily", "Reclama tu recompensa diaria de monedas."),
        ("!work", "Trabaja para ganar monedas."),
        ("!transfer @usuario cantidad", "Transfiere monedas a otro usuario."),
        ("!leaderboard", "Muestra los usuarios con más monedas."),
        ("!halloffame", "Muestra los usuarios ganadores de cada mes."),
        ("!steal @usuario", "Intenta robar monedas a otro usuario."),
        ("!coinflip cantidad", "Apuesta en cara o cruz."),
        ("!slots cantidad", "Juega a las tragamonedas."),
        ("!roulette cantidad color", "Apuesta a rojo o negro en la ruleta."),
    ],
}

@bot.command(name="ayuda")
async def help_command(ctx):
    embed = discord.Embed(
        title="Comandos Disponibles",
        description="Aquí está la lista de comandos que puedes usar:",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url="")
    embed.add_field(name="Categoría: General", value="\n".join([f"**{cmd}**: {desc}" for cmd, desc in comandos["General"]]), inline=False)
    embed.set_footer(text="Página 1/4 - Usa los botones para navegar.")

    boton_general = Button(style=discord.ButtonStyle.primary, label="General", custom_id="general", emoji="📋")
    boton_diversion = Button(style=discord.ButtonStyle.success, label="Diversión", custom_id="diversion", emoji="🎮")
    boton_administracion = Button(style=discord.ButtonStyle.danger, label="Administración", custom_id="administracion", emoji="🛠️")
    boton_economia = Button(style=discord.ButtonStyle.secondary, label="Economía", custom_id="economia", emoji="💰")

    view = View()
    view.add_item(boton_general)
    view.add_item(boton_diversion)
    view.add_item(boton_administracion)
    view.add_item(boton_economia)

    mensaje = await ctx.send(embed=embed, view=view)

    async def button_callback(interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("No puedes interactuar con este menú.", ephemeral=True)
            return

        categoria = interaction.data["custom_id"]
        embed.clear_fields()
        
        if categoria == "general":
            embed.add_field(name="Categoría: General", value="\n".join([f"**{cmd}**: {desc}" for cmd, desc in comandos["General"]]), inline=False)
            embed.set_footer(text="Página 1/4 - Usa los botones para navegar.")
        elif categoria == "diversion":
            embed.add_field(name="Categoría: Diversión", value="\n".join([f"**{cmd}**: {desc}" for cmd, desc in comandos["Diversión"]]), inline=False)
            embed.set_footer(text="Página 2/4 - Usa los botones para navegar.")
        elif categoria == "administracion":
            embed.add_field(name="Categoría: Administración", value="\n".join([f"**{cmd}**: {desc}" for cmd, desc in comandos["Administración"]]), inline=False)
            embed.set_footer(text="Página 3/4 - Usa los botones para navegar.")
        elif categoria == "economia":
            embed.add_field(name="Categoría: Economía", value="\n".join([f"**{cmd}**: {desc}" for cmd, desc in comandos["Economía"]]), inline=False)
            embed.set_footer(text="Página 4/4 - Usa los botones para navegar.")

        await interaction.response.edit_message(embed=embed, view=view)

    boton_general.callback = button_callback
    boton_diversion.callback = button_callback
    boton_administracion.callback = button_callback
    boton_economia.callback = button_callback

# Comandos de economía
@bot.command(name="balance", aliases=["bal"])
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    # Asegurar que el usuario exista en la DB
    if not UserEconomy.get_user(member.id):
        UserEconomy.create_user(member.id)
    
    balance = UserEconomy.get_balance(member.id)
    
    embed = discord.Embed(
        title=f"💰 Balance de {member.display_name}",
        description=f"**Dinero disponible:** {balance} monedas",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="daily")
async def daily(ctx):
    if not UserEconomy.can_claim_daily(ctx.author.id):
        await ctx.send("❌ Ya has reclamado tu recompensa diaria hoy. Vuelve mañana.")
        return
    
    UserEconomy.update_balance(ctx.author.id, DAILY_AMOUNT)
    UserEconomy.set_last_daily(ctx.author.id)
    
    embed = discord.Embed(
        title="🎉 Recompensa Diaria",
        description=f"Has recibido {DAILY_AMOUNT} monedas. ¡Vuelve mañana por más!",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Balance actual: {UserEconomy.get_balance(ctx.author.id)} monedas")
    await ctx.send(embed=embed)

@bot.command(name="work")
async def work(ctx):
    if not UserEconomy.can_work(ctx.author.id):
        await ctx.send("❌ Necesitas descansar. Puedes trabajar de nuevo en 1 hora.")
        return
    
    earnings = random.randint(WORK_MIN, WORK_MAX)
    UserEconomy.update_balance(ctx.author.id, earnings)
    UserEconomy.set_last_work(ctx.author.id)
    
    jobs = [
        "fue camarero en un bar",
        "programó un bot de Discord",
        "vendió limonada en la calle",
        "hizo streaming en Twitch",
        "dio clases particulares",
        "vendió artículos usados",
        "participó en un estudio de mercado",
        "hizo de repartidor"
    ]
    
    embed = discord.Embed(
        title="💼 Trabajo Completado",
        description=f"{ctx.author.mention} {random.choice(jobs)} y ganó {earnings} monedas.",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Balance actual: {UserEconomy.get_balance(ctx.author.id)} monedas")
    await ctx.send(embed=embed)

@bot.command(name="transfer", aliases=["pay"])
async def transfer(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ La cantidad debe ser mayor que 0.")
        return
    
    # Crear usuarios si no existen
    if not UserEconomy.get_user(ctx.author.id):
        UserEconomy.create_user(ctx.author.id)
    if not UserEconomy.get_user(member.id):
        UserEconomy.create_user(member.id)
    
    sender_balance = UserEconomy.get_balance(ctx.author.id)
    if sender_balance < amount:
        await ctx.send("❌ No tienes suficientes monedas para realizar esta transferencia.")
        return
    
    # Realizar la transferencia
    UserEconomy.update_balance(ctx.author.id, -amount)
    UserEconomy.update_balance(member.id, amount)
    
    embed = discord.Embed(
        title="✅ Transferencia Exitosa",
        description=f"{ctx.author.mention} ha transferido {amount} monedas a {member.mention}.",
        color=discord.Color.green()
    )
    embed.add_field(name=f"Nuevo balance de {ctx.author.display_name}", 
                   value=f"{UserEconomy.get_balance(ctx.author.id)} monedas", inline=False)
    embed.add_field(name=f"Nuevo balance de {member.display_name}", 
                   value=f"{UserEconomy.get_balance(member.id)} monedas", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="shop")
async def shop(ctx):
    eco_cursor.execute("SELECT * FROM items")
    items = eco_cursor.fetchall()
    
    if not items:
        await ctx.send("ℹ️ La tienda está vacía por ahora.")
        return
    
    embed = discord.Embed(
        title="🛒 Tienda de la Comunidad",
        description="Compra artículos con !buy <ID>",
        color=discord.Color.purple()
    )
    
    for item in items:
        embed.add_field(
            name=f"🆔 {item[0]} - {item[1]} (💵 {item[2]})",
            value=item[3],
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name="buy")
async def buy(ctx, item_id: int, quantity: int = 1):
    if quantity <= 0:
        await ctx.send("❌ La cantidad debe ser mayor que 0.")
        return
    
    eco_cursor.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
    item = eco_cursor.fetchone()
    
    if not item:
        await ctx.send("❌ Artículo no encontrado.")
        return
    
    total_price = item[2] * quantity
    user_balance = UserEconomy.get_balance(ctx.author.id)
    
    if user_balance < total_price:
        await ctx.send(f"❌ No tienes suficientes monedas. Necesitas {total_price} monedas.")
        return
    
    # Realizar la compra
    UserEconomy.update_balance(ctx.author.id, -total_price)
    
    # Añadir al inventario
    eco_cursor.execute('''INSERT OR IGNORE INTO inventory (user_id, item_id) VALUES (?, ?)
                       ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + ?''',
                       (ctx.author.id, item_id, quantity))
    eco_conn.commit()
    
    embed = discord.Embed(
        title="✅ Compra Exitosa",
        description=f"Has comprado {quantity} {item[1]} por {total_price} monedas.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Nuevo balance: {UserEconomy.get_balance(ctx.author.id)} monedas")
    await ctx.send(embed=embed)

@bot.command(name="inventory", aliases=["inv"])
async def inventory(ctx, member: discord.Member = None):
    member = member or ctx.author
    
    eco_cursor.execute('''SELECT items.item_id, items.name, items.description, inventory.quantity 
                       FROM inventory JOIN items ON inventory.item_id = items.item_id
                       WHERE inventory.user_id = ?''', (member.id,))
    items = eco_cursor.fetchall()
    
    if not items:
        await ctx.send(f"ℹ️ {member.display_name} no tiene ningún artículo en su inventario.")
        return
    
    embed = discord.Embed(
        title=f"🎒 Inventario de {member.display_name}",
        color=discord.Color.light_grey()
    )
    
    for item in items:
        embed.add_field(
            name=f"{item[1]} (x{item[3]})",
            value=item[2],
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx):
    eco_cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
    top_users = eco_cursor.fetchall()

    if not top_users:
        embed = discord.Embed(
            title="🏆 Tabla de Clasificación",
            description="ℹ️ No hay usuarios ricos todavía. ¡Empieza a ganar monedas!",
            color=discord.Color.dark_gold()
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title="🏆 Los Más Ricos del Servidor",
        description="¡Aquí están los 10 usuarios con más monedas! 💰",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://i.ibb.co/8P8KxK8/gold-trophy.png")
    embed.set_footer(text=f"Solicitado por {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    for idx, (user_id, balance) in enumerate(top_users, 1):
        user = bot.get_user(user_id)
        user_name = user.display_name if user else f"Usuario desconocido ({user_id})"
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🏅"
        embed.add_field(
            name=f"{medal} {idx}. {user_name}",
            value=f"💵 {balance:,} monedas",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command(name="steal")
@commands.cooldown(1, 1800, commands.BucketType.user)
async def steal(ctx, member: discord.Member):
    try:
        if member == ctx.author:
            embed = discord.Embed(
                title="🚫 Error",
                description="No puedes robarte a ti mismo, ¡eso sería demasiado fácil!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Asegurar que ambos usuarios existen en la DB
        if not UserEconomy.get_user(ctx.author.id):
            UserEconomy.create_user(ctx.author.id)
        if not UserEconomy.get_user(member.id):
            UserEconomy.create_user(member.id)
            
        target_balance = UserEconomy.get_balance(member.id)
        if target_balance < 300:
            embed = discord.Embed(
                title="🚫 Pobreza Detectada",
                description=f"{member.mention} no tiene suficientes monedas para ser robado (mínimo 300 monedas).",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        thief_balance = UserEconomy.get_balance(ctx.author.id)
        if thief_balance < 500:
            embed = discord.Embed(
                title="🚫 Sin Fondos para Multas",
                description="Necesitas al menos 500 monedas para intentar un robo (por si te atrapan).",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        SUCCESS_CHANCE = 0.05
        MAX_STEAL_PERCENT = 0.2
        MIN_FINE = 500
        MAX_FINE = 1500

        steal_amount = random.randint(50, int(target_balance * MAX_STEAL_PERCENT))
        
        if random.random() < SUCCESS_CHANCE:
            UserEconomy.update_balance(ctx.author.id, steal_amount)
            UserEconomy.update_balance(member.id, -steal_amount)
            
            embed = discord.Embed(
                title="💰 ¡Robo Milagroso!",
                description=f"{ctx.author.mention} ha realizado un robo imposible (5% de éxito) y ha robado **{steal_amount:,} monedas** a {member.mention}!",
                color=discord.Color.green()
            )
            embed.add_field(name="💰 Dinero robado", value=f"{steal_amount:,} monedas", inline=False)
            embed.add_field(name="💵 Tu nuevo balance", value=f"{UserEconomy.get_balance(ctx.author.id):,} monedas", inline=False)
            embed.set_footer(text="¡Probabilidad de éxito: 5%! | Cooldown: 30 minutos")
            embed.set_thumbnail(url="https://i.ibb.co/5W5ZxZ5/thief.png")
        else:
            fine = random.randint(MIN_FINE, MAX_FINE)
            actual_fine = min(fine, thief_balance)
            UserEconomy.update_balance(ctx.author.id, -actual_fine)
            
            embed = discord.Embed(
                title="🚨 ¡Atrapado y Multado!",
                description=f"{ctx.author.mention} intentó robar a {member.mention} pero fue capturado y multado con **{actual_fine:,} monedas**.",
                color=discord.Color.red()
            )
            embed.add_field(name="💸 Multa aplicada", value=f"{actual_fine:,} monedas", inline=False)
            embed.add_field(name="💵 Tu nuevo balance", value=f"{UserEconomy.get_balance(ctx.author.id):,} monedas", inline=False)
            embed.set_footer(text="Probabilidad de éxito: 0.5% | Cooldown: 30 minutos")
            embed.set_thumbnail(url="https://i.ibb.co/7J7Q7Q7/police.png")

        try:
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("¡Operación de robo completada! (No se pudo mostrar el embed)")

    except Exception as e:
        print(f"Error en comando steal: {e}")
        await ctx.send("❌ Ocurrió un error al procesar el robo. Inténtalo de nuevo más tarde.")

@steal.error
async def steal_error(ctx, error):
    try:
        if isinstance(error, commands.CommandOnCooldown):
            remaining = str(timedelta(seconds=int(error.retry_after)))
            embed = discord.Embed(
                title="⏳ Enfriamiento",
                description=f"Debes esperar {remaining} antes de intentar otro robo.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="🚫 Error",
                description="Debes mencionar a un usuario para robar. Ejemplo: `!steal @usuario`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="🚫 Usuario no encontrado",
                description="No pude encontrar al usuario mencionado. Asegúrate de que esté en el servidor.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            print(f"Error no manejado en comando steal: {error}")
            embed = discord.Embed(
                title="❌ Error inesperado",
                description="Ocurrió un error al procesar el comando.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    except Exception as e:
        print(f"Error al manejar el error del comando steal: {e}")

@bot.command(name="gift")
async def gift(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        embed = discord.Embed(
            title="🚫 Error",
            description="La cantidad debe ser mayor que 0. ¡No seas tacaño!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    if member == ctx.author:
        embed = discord.Embed(
            title="🚫 Error",
            description="¡No puedes regalarte monedas a ti mismo!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Asegurar que ambos usuarios existen en la DB
    if not UserEconomy.get_user(ctx.author.id):
        UserEconomy.create_user(ctx.author.id)
    if not UserEconomy.get_user(member.id):
        UserEconomy.create_user(member.id)
        
    sender_balance = UserEconomy.get_balance(ctx.author.id)
    if sender_balance < amount:
        embed = discord.Embed(
            title="🚫 Saldo Insuficiente",
            description="No tienes suficientes monedas para ser tan generoso.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    UserEconomy.update_balance(ctx.author.id, -amount)
    UserEconomy.update_balance(member.id, amount)

    embed = discord.Embed(
        title="🎁 ¡Regalo Enviado!",
        description=f"{ctx.author.mention} ha regalado **{amount:,} monedas** a {member.mention}. ¡Qué generoso!",
        color=discord.Color.green()
    )
    embed.add_field(name=f"Balance de {ctx.author.display_name}", value=f"💵 {UserEconomy.get_balance(ctx.author.id):,} monedas", inline=True)
    embed.add_field(name=f"Balance de {member.display_name}", value=f"💵 {UserEconomy.get_balance(member.id):,} monedas", inline=True)
    embed.set_thumbnail(url="https://i.ibb.co/3r3r3r3/gift.png")
    await ctx.send(embed=embed)

# Comandos de casino
@bot.command(name="coinflip")
async def coinflip(ctx, amount: int):
    if amount <= 0:
        embed = discord.Embed(
            title="🚫 Error",
            description="La apuesta debe ser mayor que 0. ¡Arriesga algo!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Asegurar que el usuario exista en la DB
    if not UserEconomy.get_user(ctx.author.id):
        UserEconomy.create_user(ctx.author.id)
        
    user_balance = UserEconomy.get_balance(ctx.author.id)
    if user_balance < amount:
        embed = discord.Embed(
            title="🚫 Saldo Insuficiente",
            description="No tienes suficientes monedas para esta apuesta.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    result = random.choice(["Cara", "Cruz"])
    embed = discord.Embed(
        title="🎲 Lanzando la Moneda...",
        description=f"{ctx.author.mention} apostó **{amount:,} monedas**.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://i.ibb.co/8P8KxK8/coin.png")
    message = await ctx.send(embed=embed)
    await asyncio.sleep(2)

    if random.random() < 0.5:
        UserEconomy.update_balance(ctx.author.id, amount)
        embed.title = "🎉 ¡Ganaste!"
        embed.description = f"Salió **{result}**. ¡Ganaste **{amount:,} monedas**!"
        embed.color = discord.Color.green()
    else:
        UserEconomy.update_balance(ctx.author.id, -amount)
        embed.title = "😢 Perdiste"
        embed.description = f"Salió **{result}**. Perdiste **{amount:,} monedas**."
        embed.color = discord.Color.red()

    embed.add_field(name="Tu nuevo balance", value=f"💵 {UserEconomy.get_balance(ctx.author.id):,} monedas", inline=False)
    await message.edit(embed=embed)

@bot.command(name="slots")
async def slots(ctx, amount: int):
    if amount <= 0:
        embed = discord.Embed(
            title="🚫 Error",
            description="La apuesta debe ser mayor que 0. ¡Juega en grande!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Asegurar que el usuario exista en la DB
    if not UserEconomy.get_user(ctx.author.id):
        UserEconomy.create_user(ctx.author.id)
        
    user_balance = UserEconomy.get_balance(ctx.author.id)
    if user_balance < amount:
        embed = discord.Embed(
            title="🚫 Saldo Insuficiente",
            description="No tienes suficientes monedas para girar las tragamonedas.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    symbols = ["🍒", "🍋", "🍊", "💎", "🔔", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    embed = discord.Embed(
        title="🎰 Girando las Tragamonedas...",
        description=f"{ctx.author.mention} apostó **{amount:,} monedas**.\n\n| {' | '.join(['❓']*3)} |",
        color=discord.Color.purple()
    )
    message = await ctx.send(embed=embed)
    await asyncio.sleep(2)

    winnings = 0
    if result[0] == result[1] == result[2]:
        winnings = amount * 5
        UserEconomy.update_balance(ctx.author.id, winnings - amount)
        embed.title = "🎰 ¡Jackpot!"
        embed.color = discord.Color.green()
        embed.description = f"| {' | '.join(result)} |\n¡Ganaste **{winnings:,} monedas** (x5)!"
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        winnings = amount * 2
        UserEconomy.update_balance(ctx.author.id, winnings - amount)
        embed.title = "🎰 ¡Ganaste!"
        embed.color = discord.Color.green()
        embed.description = f"| {' | '.join(result)} |\n¡Ganaste **{winnings:,} monedas** (x2)!"
    else:
        UserEconomy.update_balance(ctx.author.id, -amount)
        embed.title = "🎰 Perdiste"
        embed.color = discord.Color.red()
        embed.description = f"| {' | '.join(result)} |\nPerdiste **{amount:,} monedas**."

    embed.add_field(name="Tu nuevo balance", value=f"💵 {UserEconomy.get_balance(ctx.author.id):,} monedas", inline=False)
    await message.edit(embed=embed)

@bot.command(name="roulette")
async def roulette(ctx, amount: int, color: str):
    if amount <= 0:
        embed = discord.Embed(
            title="🚫 Error",
            description="La apuesta debe ser mayor que 0. ¡Arriesga algo!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Asegurar que el usuario exista en la DB
    if not UserEconomy.get_user(ctx.author.id):
        UserEconomy.create_user(ctx.author.id)
        
    user_balance = UserEconomy.get_balance(ctx.author.id)
    if user_balance < amount:
        embed = discord.Embed(
            title="🚫 Saldo Insuficiente",
            description="No tienes suficientes monedas para esta apuesta.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    color = color.lower()
    if color not in ["rojo", "negro"]:
        embed = discord.Embed(
            title="🚫 Error",
            description="Debes elegir 'rojo' o 'negro'. ¡Intenta de nuevo!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
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
        UserEconomy.update_balance(ctx.author.id, amount)
        embed.title = "🎉 ¡Ganaste!"
        embed.description = f"La ruleta cayó en **{result}**. ¡Ganaste **{amount:,} monedas**!"
        embed.color = discord.Color.green()
    else:
        UserEconomy.update_balance(ctx.author.id, -amount)
        embed.title = "😢 Perdiste"
        embed.description = f"La ruleta cayó en **{result}**. Perdiste **{amount:,} monedas**."
        embed.color = discord.Color.red()

    embed.add_field(name="Tu nuevo balance", value=f"💵 {UserEconomy.get_balance(ctx.author.id):,} monedas", inline=False)
    await message.edit(embed=embed)

# Comandos de administración para la economía
@bot.command(name="addmoney")
@commands.has_permissions(administrator=True)
async def add_money(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ La cantidad debe ser mayor que 0.")
        return
    
    # Asegurar que el usuario exista en la DB
    if not UserEconomy.get_user(member.id):
        UserEconomy.create_user(member.id)
    
    UserEconomy.update_balance(member.id, amount)
    
    embed = discord.Embed(
        title="✅ Monedas Añadidas",
        description=f"Se han añadido {amount} monedas a {member.mention}.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Nuevo balance: {UserEconomy.get_balance(member.id)} monedas")
    await ctx.send(embed=embed)

@bot.command(name="removemoney")
@commands.has_permissions(administrator=True)
async def remove_money(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ La cantidad debe ser mayor que 0.")
        return
    
    # Asegurar que el usuario exista en la DB
    if not UserEconomy.get_user(member.id):
        UserEconomy.create_user(member.id)
        
    user_balance = UserEconomy.get_balance(member.id)
    if user_balance < amount:
        amount = user_balance
    
    UserEconomy.update_balance(member.id, -amount)
    
    embed = discord.Embed(
        title="✅ Monedas Eliminadas",
        description=f"Se han eliminado {amount} monedas de {member.mention}.",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Nuevo balance: {UserEconomy.get_balance(member.id)} monedas")
    await ctx.send(embed=embed)

@bot.command(name="additem")
@commands.has_permissions(administrator=True)
async def add_item(ctx, name: str, price: int, *, description: str):
    eco_cursor.execute("INSERT INTO items (name, price, description) VALUES (?, ?, ?)",
                      (name, price, description))
    eco_conn.commit()
    
    embed = discord.Embed(
        title="✅ Artículo Añadido",
        description=f"Se ha añadido '{name}' a la tienda por {price} monedas.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name="removeitem")
@commands.has_permissions(administrator=True)
async def remove_item(ctx, item_id: int):
    eco_cursor.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
    eco_conn.commit()
    
    if eco_cursor.rowcount == 0:
        await ctx.send("❌ No se encontró ningún artículo con ese ID.")
        return
    
    await ctx.send("✅ Artículo eliminado correctamente.")

@bot.command(name="halloffame", aliases=["hof"])
async def halloffame(ctx):
    eco_cursor.execute('''SELECT month, year, user_id, balance
                          FROM hall_of_fame
                          ORDER BY year DESC, month DESC''')
    rows = eco_cursor.fetchall()

    if not rows:
        await ctx.send("📜 No hay ganadores registrados aún.")
        return

    embed = discord.Embed(
        title="🏆 Hall of Fame - Ganadores Mensuales",
        color=discord.Color.gold()
    )

    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    for month, year, user_id, balance in rows:
        user = bot.get_user(user_id)
        nombre = user.name if user else f"Usuario {user_id}"
        embed.add_field(
            name=f"{meses[month-1]} {year}",
            value=f"{nombre} - 💵 {balance:,} monedas",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command(name="moneda")
async def flip_coin(ctx):
    resultado = random.choice(["Cara", "Cruz"])
    await ctx.send(f"{ctx.author.mention} La moneda ha salido: {resultado}")

@bot.command(name="suerte")
async def eight_ball(ctx):
    respuestas = [
        "Aka dice que: Bien.", "Aka dice que: Mal.", "Aka dice que: Tal vez.",
        "Aka dice que: Definitivamente sí.", "Aka dice que: No cuentes con ello.",
        "Aka dice que: Claro que sí.", "Aka dice que: Parece que sí.",
        "Aka dice que: Mejor no te digo nada.", "Aka dice que: No estoy seguro, vuelve a intentarlo.",
        "Aka dice que: Es probable.", "Aka dice que: Lo dudo.", "Aka dice que: ¡Claro que no!",
        "Aka dice que: La respuesta es incierta.", "Aka dice que: La suerte está de tu lado.",
        "Aka dice que: La fortuna te sonríe.", "Aka dice que: Todo depende de ti.",
        "Aka dice que: No es un buen momento para eso.", "Aka dice que: ¡Sí, sin duda!",
        "Aka dice que: No te preocupes, todo saldrá bien.", "Aka dice que: ¡Lo conseguirás!",
        "Aka dice que: Los astros están alineados a tu favor.", "Aka dice que: Mejor espera un poco.",
        "Aka dice que: El futuro es incierto, pero tal vez.", "Aka dice que: Confía en tu instinto."
    ]
    respuesta = random.choice(respuestas)
    await ctx.send(f"{ctx.author.mention} {respuesta}")

@bot.command(name="memide")
async def me_mide(ctx):
    tamaños = ["2 cm 😳", "5 cm 😢", "10 cm 🫠", "15 cm 😏", "20 cm 😎", "30 cm 🔥"]
    medida = random.choice(tamaños)
    await ctx.send(f"{ctx.author.mention} Aka dice que te mide {medida} ")

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
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name="clear")
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    if amount < 1:
        await ctx.send("Por favor, ingresa un número mayor que 0.")
        return

    await ctx.channel.purge(limit=amount+1)

class CloseTicketView(View):
    """Vista con el botón para cerrar el ticket."""
    def __init__(self, channel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label="🔒 Cerrar Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not self.channel:
            self.channel = interaction.channel
        
        await interaction.response.send_message("⏳ Cerrando ticket...", ephemeral=True)
        await self.channel.delete()

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
        embed.set_thumbnail(url="https://i.ibb.co/rscspsR/Reportes-aka.png")
        embed.set_footer(text="🛠️ Usa el botón de abajo para cerrar el ticket.")

        await ticket_channel.send(embed=embed, view=CloseTicketView(ticket_channel))
        await interaction.response.send_message(f"✅ Ticket creado: {ticket_channel.mention}", ephemeral=True)

@bot.command(name="ticket")
@commands.has_permissions(administrator=True)
async def ticket(ctx):
    embed = discord.Embed(
        title="📌 Sistema de Tickets - PRUEBA",
        description="Si necesitas ayuda, abre un ticket con el botón de abajo.\n\n"
                    "🔸 **Soporte técnico**\n"
                    "🔸 **Reportes y quejas**\n"
                    "🔸 **Consultas generales**",
        color=discord.Color.orange()
    )
    embed.set_image(url="PRUEBA")
    embed.set_footer(text="📌 Nuestro staff responderá lo antes posible.")

    await ctx.send(embed=embed, view=TicketView())

# Diccionario para llevar el control de votos por mensaje
votos = {}

class Votacion(View):
    def __init__(self, mensaje_id, mensaje_original, mensaje_sugerencia):
        super().__init__()
        self.mensaje_id = mensaje_id
        self.mensaje_original = mensaje_original
        self.mensaje_sugerencia = mensaje_sugerencia
        self.votos_positivos = 0
        self.votos_negativos = 0
        self.usuarios_que_votaron = set()
        
        # Ocultar botón de finalización para no admins
        if not mensaje_original.author.guild_permissions.administrator:
            self.finalizar_sugerencia.disabled = True

    @discord.ui.button(label="👍 Voto positivo", style=discord.ButtonStyle.green)
    async def voto_positivo(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in self.usuarios_que_votaron:
            await interaction.response.send_message("¡Ya has votado! Solo puedes votar una vez.", ephemeral=True)
            return

        self.votos_positivos += 1
        self.usuarios_que_votaron.add(interaction.user.id)
        await interaction.response.send_message(f"Gracias por tu voto positivo. Votos positivos: {self.votos_positivos}, negativos: {self.votos_negativos}", ephemeral=True)
        await self.actualizar_mensaje(interaction.message)

    @discord.ui.button(label="👎 Voto negativo", style=discord.ButtonStyle.red)
    async def voto_negativo(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in self.usuarios_que_votaron:
            await interaction.response.send_message("¡Ya has votado! Solo puedes votar una vez.", ephemeral=True)
            return

        self.votos_negativos += 1
        self.usuarios_que_votaron.add(interaction.user.id)
        await interaction.response.send_message(f"Gracias por tu voto negativo. Votos positivos: {self.votos_positivos}, negativos: {self.votos_negativos}", ephemeral=True)
        await self.actualizar_mensaje(interaction.message)

    @discord.ui.button(label="✅ Finalizar sugerencia", style=discord.ButtonStyle.blurple)
    async def finalizar_sugerencia(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ No tienes permisos para finalizar la sugerencia.", ephemeral=True)
            return

        if self.votos_positivos > self.votos_negativos:
            resultado = "Aprobada"
        else:
            resultado = "No aprobada"

        embed = discord.Embed(
            title=f"Sugerencia de {self.mensaje_original.author.name}",
            description=self.mensaje_sugerencia,
            color=discord.Color.blue()
        )
        
        avatar_url = self.mensaje_original.author.avatar.url if self.mensaje_original.author.avatar else "https://example.com/default-avatar.png"
        embed.set_footer(text=f"Enviado por {self.mensaje_original.author.name}")
        embed.set_thumbnail(url=avatar_url)
        
        embed.add_field(name="Votos positivos", value=str(self.votos_positivos), inline=True)
        embed.add_field(name="Votos negativos", value=str(self.votos_negativos), inline=True)
        embed.add_field(name="Estado", value=resultado, inline=False)

        await interaction.message.edit(embed=embed)
        button.disabled = True
        await interaction.message.edit(view=self)

    async def actualizar_mensaje(self, mensaje):
        embed = discord.Embed(
            title=f"Sugerencia de {self.mensaje_original.author.name}",
            description=self.mensaje_sugerencia,
            color=discord.Color.blue()
        )
        
        avatar_url = self.mensaje_original.author.avatar.url if self.mensaje_original.author.avatar else "https://example.com/default-avatar.png"
        embed.set_footer(text=f"Enviado por {self.mensaje_original.author.name}")
        embed.set_thumbnail(url=avatar_url)
        
        embed.add_field(name="Votos positivos", value=str(self.votos_positivos), inline=True)
        embed.add_field(name="Votos negativos", value=str(self.votos_negativos), inline=True)
        await mensaje.edit(embed=embed)

@bot.command(name="sugerencia")
async def sugerencia(ctx, *, mensaje: str):
    if ctx.channel.id != CANAL_SUGERENCIAS_ID:
        await ctx.send("❌ Las sugerencias solo pueden enviarse en el canal autorizado.")
        return

    embed = discord.Embed(
        title=f"Sugerencia de {ctx.author.name}",
        description=mensaje,
        color=discord.Color.orange()
    )
    
    avatar_url = ctx.author.avatar.url if ctx.author.avatar else "https://example.com/default-avatar.png"
    embed.set_footer(text=f"Enviado por {ctx.author.name}")
    embed.set_thumbnail(url=avatar_url)

    view = Votacion(mensaje_id=ctx.message.id, mensaje_original=ctx.message, mensaje_sugerencia=mensaje)
    mensaje_embed = await ctx.send(embed=embed, view=view)
    votos[ctx.message.id] = view
    await ctx.message.delete()

@bot.command(name="warn")
async def warn(ctx, member: discord.Member, *, reason: str):
    def tiene_rol(ctx):
        role = discord.utils.get(ctx.author.roles, id=MOD_ROLE_ID)
        return role is not None

    if not tiene_rol(ctx):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    try:
        conn, cursor = get_warn_db()
        cursor.execute("INSERT INTO warnings (user_id, reason) VALUES (?, ?)", (member.id, reason))
        conn.commit()

        embed_dm = discord.Embed(
            title="⚠️ Has sido advertido",
            description=f"Motivo: {reason}\n\nSi crees que esto es un error, contacta con un moderador.",
            color=discord.Color.red()
        )
        embed_dm.set_footer(text=f"Servidor: AKA Server")
        embed_dm.set_thumbnail(url="https://i.ibb.co/PZStwmWm/Nuevo-logo-1-2.jpg")

        try:
            await member.send(embed=embed_dm)
        except discord.Forbidden:
            await ctx.send("❌ No he podido enviar un mensaje privado a este usuario.")

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
    finally:
        conn.close()

@bot.command(name="historial")
async def historial(ctx, member: discord.Member):
    def tiene_rol(ctx):
        role = discord.utils.get(ctx.author.roles, id=MOD_ROLE_ID)
        return role is not None

    if not tiene_rol(ctx):
        await ctx.send("❌ No tienes permiso para usar este comando.")
        return

    try:
        conn, cursor = get_warn_db()
        cursor.execute("SELECT reason FROM warnings WHERE user_id = ?", (member.id,))
        user_warnings = cursor.fetchall()

        if not user_warnings:
            await ctx.send(f"{member.mention} no tiene advertencias previas.")
        else:
            embed = discord.Embed(title=f"Historial de advertencias de {member.name}", color=discord.Color.red())
            for idx, warn in enumerate(user_warnings, start=1):
                embed.add_field(name=f"Advertencia {idx}", value=warn[0], inline=False)
            await ctx.send(embed=embed)
    finally:
        conn.close()

@bot.command(name="stats")
async def stats(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 Estadísticas del Servidor: {guild.name}", color=discord.Color.orange())
    embed.add_field(name="👥 Miembros", value=str(guild.member_count), inline=False)
    embed.add_field(name="💬 Canales de Texto", value=str(len(guild.text_channels)), inline=False)
    embed.add_field(name="🔊 Canales de Voz", value=str(len(guild.voice_channels)), inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def verificar_roles(ctx):
    roles = [role for role_id in ROLES_IDS 
             if (role := ctx.guild.get_role(role_id)) is not None]
    if not roles:
        await ctx.send("Ninguno de los roles especificados existe. Revisa la configuración.")
        return

    count = 0
    for member in ctx.guild.members:
        missing_roles = [role for role in roles if role not in member.roles]
        if missing_roles:
            await member.add_roles(*missing_roles)
            count += 1

    await ctx.send(f"Se ha verificado y corregido el rol en {count} miembros.")

@bot.event
async def on_message(message):
    if str(USER_ID_NO_MENCIONAR) in [str(user.id) for user in message.mentions]:
        mod_role = message.guild.get_role(MOD_ROLE_ID)
        if mod_role and mod_role in message.author.roles:
            await bot.process_commands(message)
            return

        await message.delete()

        embed_mencion = discord.Embed(
            title="⚠️ Mensaje Eliminado",
            description="Motivo: \nNo puedes mencionar a Akantor. \nPor favor, no lo vuelvas a repetir.",
            color=discord.Color.red()
        )
        embed_mencion.set_footer(text="Servidor: AKA Server")
        embed_mencion.set_thumbnail(url="https://i.ibb.co/PZStwmWm/Nuevo-logo-1-2.jpg")

        try:
            await message.author.send(embed=embed_mencion)
        except discord.Forbidden:
            await message.channel.send(
                f"{message.author.mention}, no puedes mencionar a este usuario. Tu mensaje ha sido eliminado.",
                delete_after=10
            )

    await bot.process_commands(message)

# Cerrar conexiones al finalizar
@bot.event
async def on_disconnect():
    print("Bot desconectado de Discord. Esperando reconexión...")

@bot.event
async def on_close():
    eco_conn.close()
    print("Conexiones a bases de datos cerradas.")


# Usar variable de entorno para el token
bot.run("")