import os
import datetime
from zoneinfo import ZoneInfo
import discord
from discord.ext import tasks, commands

# --------- CONFIG TO EDIT (except TOKEN) ---------
GUILD_ID = 1445750975796215882       # your server ID
CHANNEL_ID = 1445794710026190901     # channel ID for reminders
ROLE_NAME = "reminder"               # exact role name
LAST_REMINDER_HOUR = 21              # last reminder hour (UK time)
# -----------------------------------------------

# TOKEN from environment variable (Railway)
TOKEN = os.environ.get("TOKEN")
if TOKEN is None:
    raise RuntimeError("TOKEN environment variable not set.")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

last_med_day = None
med_taken_today = False


def now_uk():
    """Returns current UK time."""
    return datetime.datetime.now(tz=ZoneInfo("Europe/London"))


class MedButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="I took my medication",
        style=discord.ButtonStyle.success,
        custom_id="med_taken_button"
    )
    async def med_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global med_taken_today, last_med_day

        today = now_uk().date()

        if last_med_day != today:
            last_med_day = today

        med_taken_today = True

        await interaction.response.send_message(
            "✅ Thank you! I'm glad you took your medication.",
            ephemeral=True
        )

        try:
            await interaction.message.edit(
                content=interaction.message.content + "\n\n✅ Medication confirmed for today.",
                view=None
            )
        except Exception:
            pass


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    send_medication_reminders.start()
    print("Reminder task started.")


@tasks.loop(minutes=1)
async def send_medication_reminders():
    global last_med_day, med_taken_today

    now = now_uk()
    today = now.date()
    hour = now.hour
    minute = now.minute

    if last_med_day != today:
        last_med_day = today
        med_taken_today = False

    if minute != 0:
        return

    if med_taken_today:
        return

    if hour < 17:
        return

    if hour > LAST_REMINDER_HOUR:
        return

    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print("⚠️ Invalid GUILD_ID or bot not on this server.")
        return

    channel = guild.get_channel(CHANNEL_ID)
    if channel is None:
        print("⚠️ Invalid CHANNEL_ID or channel not found.")
        return

    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role is None:
        print("⚠️ Role not found, check ROLE_NAME.")
        return

    if hour == 17:
        title = "🕔 It's time to take your medication! (UK time)"
    else:
        title = f"⏰ Medication reminder (it's {hour}:00 UK time)"

    view = MedButtonView()

    await channel.send(
        content=f"{role.mention}\n{title}\nPlease click the button below once you've taken it. 💊",
        view=view
    )


@bot.command(name="testmed")
async def test_med(ctx: commands.Context):
    global last_med_day, med_taken_today
    last_med_day = now_uk().date()
    med_taken_today = False

    role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
    view = MedButtonView()

    await ctx.send(
        content=f"{role.mention}\n🔔 Medication reminder test.\nClick the button once you've taken it.",
        view=view
    )


bot.run(TOKEN)
