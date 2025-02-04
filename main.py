import discord
from discord.ext import commands
import random
import asyncio
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import re
import string
import math

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

AUTHORIZED_USERS = ["1027407264191107112", "679943533460717588","834288163940728851"] # for this just change to your Discord ID and add any admin's ids.

# Initialize the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="j!", intents=intents)
bot.remove_command("help")

# Tracks users who are in the middle an interaction.
ongoing_interactions = {}

@bot.event
async def on_command(ctx):
    # Notify users who attempt to use other commands while in an interaction
    if ctx.author.id in ongoing_interactions:
        channel_id = ongoing_interactions[ctx.author.id]
        await ctx.reply(
            f"You have an ongoing action that requires your confirmation inside of <#{channel_id}>. "
            "Please complete or cancel it before using other commands."
        )
        return

# Load or create the user database
data_file = "users.json"
if not os.path.exists(data_file):
    with open(data_file, "w") as f:
        json.dump({}, f)

with open(data_file, "r") as f:
    users = json.load(f)

# Helper functions
def save_users():
    with open(data_file, "w") as f:
        json.dump(users, f, indent=4)

def get_user(user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {
            "balance": 40,
            "job_level": 0,
            "inventory": {}
        }
        # Add exclusive items to the dev user's inventory
        if str(user_id) == "1027407264191107112":
            users[str(user_id)]["inventory"]["10"] = 1  # Unicorn
            users[str(user_id)]["inventory"]["18"] = 1  # Poseidon
        save_users()
    return users[str(user_id)]

def add_item(user_id, item_id, amount):
    user = get_user(user_id)
    if item_id in user["inventory"]:
        user["inventory"][item_id] += amount
    else:
        user["inventory"][item_id] = amount
    save_users()

def remove_item(user_id, item_id, amount):
    user = get_user(user_id)
    if item_id in user["inventory"] and user["inventory"][item_id] >= amount:
        user["inventory"][item_id] -= amount
        if user["inventory"][item_id] == 0:
            del user["inventory"][item_id]
        save_users()
        return True
    return False

# Hunting and fishing probabilities and items
hunting_animals = {
    "3": {"name": "Deer", "probability": 0.5, "price":"Not for sale", "sell_price": 4, "usable":"no"},
    "4": {"name": "Wild Boar", "probability": 0.25, "price":"Not for sale", "sell_price": 8, "usable":"no"},
    "5": {"name": "Elk", "probability": 0.0625, "price":"Not for sale", "sell_price": 16, "usable":"no"},
    "6": {"name": "Mountain Lion", "probability": 0.01, "price":"Not for sale", "sell_price": 50, "usable":"no"},
    "7": {"name": "Eagle", "probability": 0.002, "price":"Not for sale", "sell_price": 10000, "usable":"no"},
    "8": {"name": "Snow Leopard", "probability": 0.001, "price":"Not for sale", "sell_price": 15000, "usable":"no"},
    "9": {"name": "The Dragon", "probability": 0.00001, "price":"Not for sale", "sell_price": 100000, "usable":"no"},
    "10": {"name": "Unicorn", "probability": 0.0, "price":"Not for sale", "sell_price": 9e+19489293432984329342, "usable":"no"},
}

fishing_fish = {
    "11": {"name": "Bluegill Fish", "probability": 0.5, "price":"Not for sale", "sell_price": 4, "usable":"no"},
    "12": {"name": "Salmon", "probability": 0.25, "price":"Not for sale", "sell_price": 8, "usable":"no"},
    "13": {"name": "Tuna", "probability": 0.0625, "price":"Not for sale", "sell_price": 16, "usable":"no"},
    "14": {"name": "Shark", "probability": 0.01, "price":"Not for sale", "sell_price": 50, "usable":"no"},
    "15": {"name": "Whales", "probability": 0.002, "price":"Not for sale", "sell_price": 10000, "usable":"no"},
    "16": {"name": "Orca", "probability": 0.001, "price":"Not for sale", "sell_price": 15000, "usable":"no"},
    "17": {"name": "The Leviathan", "probability": 0.00001, "price":"Not for sale", "sell_price": 100000, "usable":"no"},
    "18": {"name": "Poseidon", "probability": 0.0, "price":"Not for sale", "sell_price": 9e+19489293432984329342, "usable":"no"},
}

market_items = {
    "1": {"name": "Fishing Rod", "price": 150, "sell_price": 20, "usable":"no"},
    "2": {"name": "Hunting Rifle", "price": 150, "sell_price": 20, "usable":"no"},
    "23": {"name": "Dragon's Lure", "price": 10000000, "sell_price": 30000, "usable":"yes"},
    "24": {"name": "Leviathan's Charm", "price": 10000000, "sell_price": 30000, "usable":"yes"},
    "25": {"name": "Life-saver", "price": 320, "sell_price": 1, "usable":"no"},
    "26": {"name": "Pad lock", "price": 120, "sell_price": 1, "usable":"no"}
}

Admin_excl = {
    "0": {"name": "xVapure", "probability": 0.0, "sell_price": -1, "usable":"no"},
    "i": {"name": "Kamui", "probability": 0.0, "sell_price": -1, "usable":"no"},
    "-1": {"name": "Test_placeholder", "probability": 0.0, "sell_price": -1, "usable":"no"},
    "-2": {"name": "NotVentea", "probability": 0.0, "sell_price": -1, "usable":"no"}
    
}

Other_items = {
    "19": {"name": "Leviathan Segment", "probability": 0.0, "sell_price": 70000, "usable":"no"},
    "20": {"name": "Dragon's Body", "probability": 0.0, "sell_price": 70000, "usable":"no"},
    "21": {"name": "Dragon's Tail", "probability": 0.0, "sell_price": 30000, "usable":"no"},
    "22": {"name": "Leviathan's Tail", "probability": 0.0, "sell_price": 30000, "usable":"no"},
}

Mutations = {
    "3.5": {"name": "Deer [MUTATED]", "probability": 0.0, "sell_price": 4, "usable":"no"},
    "4.5": {"name": "Wild Boar [MUTATED]", "probability": 0.0, "sell_price": 8, "usable":"no"},
    "5.5": {"name": "Elk [MUTATED]", "probability": 0.0, "sell_price": 16, "usable":"no"},
    "6.5": {"name": "Mountain Lion [MUTATED]", "probability": 0.0, "sell_price": 50, "usable":"no"},
    "7.5": {"name": "Eagle [MUTATED]", "probability": 0.0, "sell_price": 10000, "usable":"no"},
    "8.5": {"name": "Snow Leopard [MUTATED]", "probability": 0.0, "sell_price": 15000, "usable":"no"},
    "9.5": {"name": "The Dragon [MUTATED]", "probability": 0.0, "sell_price": 100000, "usable":"no"},
    "10.5": {"name": "Unicorn [MUTATED]", "probability": 0.0, "sell_price": 9e+19489293432984329342, "usable":"no"},
    "11.5": {"name": "Bluegill Fish [MUTATED]", "probability": 0.0, "sell_price": 4, "usable":"no"},
    "12.5": {"name": "Salmon [MUTATED]", "probability": 0.0, "sell_price": 8, "usable":"no"},
    "13.5": {"name": "Tuna [MUTATED]", "probability": 0.0, "sell_price": 16, "usable":"no"},
    "14.5": {"name": "Shark [MUTATED]", "probability": 0.0, "sell_price": 50, "usable":"no"},
    "15.5": {"name": "Whales [MUTATED]", "probability": 0.0, "sell_price": 10000, "usable":"no"},
    "16.5": {"name": "Orca [MUTATED]", "probability": 0.0, "sell_price": 15000, "usable":"no"},
    "17.5": {"name": "The Leviathan [MUTATED]", "probability": 0.00001, "sell_price": 100000, "usable":"no"},
    "18.5": {"name": "Poseidon [MUTATED]", "probability": 0.0, "sell_price": 9e+19489293432984329342, "usable":"no"},
}

#Newest item is 26

# Combine all items for easier inventory and sell logic
all_items = {**market_items, **hunting_animals, **fishing_fish, **Admin_excl, **Other_items, **Mutations}

# Bot events
@bot.event
async def on_ready():
    print("TOKEN/password is correct, logging into {0.user}!".format(bot))
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing,name="j!help"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("It looks like you're missing some required arguments for this command. Use `j!help` to learn more.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"This command is on cooldown. Please try again in {round(error.retry_after, 2)} seconds.")
    elif isinstance(error, commands.BadArgument):
        await ctx.reply("Invalid argument provided. Please check your input and try again. Use `j!help` to learn more.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.reply("We have recently migrated to slash commands, type `/` and find Jerry to start using your favourite commands!")
    else:
        await ctx.reply("An unexpected error occurred. Please try again later.")

# Commands
@bot.slash_command(name="register", description="Register to start using the bot")
async def register(ctx: discord.ApplicationContext):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve", ephemeral=True)
        return
    if str(ctx.author.id) in users:
        await ctx.respond("You are already registered!", ephemeral=True)
        return

    user = get_user(ctx.author.id)
    await ctx.respond(f"Welcome, <@{ctx.author.id}>! You have been registered with $40.")

@bot.slash_command(name="help", description="Shows a list of commands and their usage.")
async def help(ctx: discord.ApplicationContext, page: int = 1):
    commands_list = [
        "- `/register` → Register to start using the bot.",
        "- `/balance [@user]` → Check your or another user's balance.",
        "- `/inventory [@user] [page]` → View your or another user's inventory.",
        "- `/market list [page]` → View available items in the market.",
        "- `/market buy <item_id> <amount>` → Buy an item from the market.",
        "- `/market sell <item_id> <amount>` → Sell an item from your inventory.",
        "- `/daily` → Claim your daily reward.",
        "- `/gamble <amount> <multiplier>` → Gamble an amount with a chance to multiply it.",
        "- `/duel <@user> <amount>` → Challenge a user to a duel for money.",
        "- `/hunt` → Hunt animals for profit (requires a hunting rifle).",
        "- `/fish` → Fish for profit (requires a fishing rod).",
        "- `/passive <on/off>` → Enable or disable passive mode (prevents robbery/trades/duels).",
        "- `/trade <@user> <your_item> <their_item>` → Trade items with another user.",
        "- `/gift <@user> <item_id/money> <amount>` → Gift an item or money to another user.",
        "- `/auction help` → View auction-related commands.",
        "- `/work do` → Work to earn money.",
        "- `/work upgrade` → Upgrade your job for better earnings.",
        "- `/itemlist [page]` → View all available items.",
        "- `/iteminfo <item_id>` → Get details about a specific item.",
    ]

    items_per_page = 10
    total_pages = -(-len(commands_list) // items_per_page)  # Ceiling division

    if page < 1 or page > total_pages:
        await ctx.respond(f"Invalid page number. Please choose a page between 1 and {total_pages}.", ephemeral=True)
        return

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_commands = commands_list[start_idx:end_idx]

    help_text = (
        f"**Jerry Bot Help**\n"
        f"Commands (Page {page}/{total_pages}):\n"
        + "\n".join(page_commands)
    )

    if page < total_pages:
        help_text += f"\n\nUse `/help {page + 1}` to view the next page."

    await ctx.respond(help_text, ephemeral=True)

@bot.slash_command(name="balance", description="Check your or another user's balance")
async def balance(ctx: discord.ApplicationContext, user: discord.User = None):
    if ctx.author.id in ongoing_interactions or user and user.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve", ephemeral=True)
        return
    
    user = user or ctx.author  # Default to the command user if no target user is specified
    
    # Fetch the user's data
    user_data = get_user(user.id)
    
    # Respond with the user's balance
    await ctx.respond(f"`{user.name}'s` current balance is ${user_data['balance']}")

work_group = bot.create_group("work", "Earn money or upgrade your job.")

@work_group.command(name="do", description="Work to earn money")
@commands.cooldown(1, 20, commands.BucketType.user)
async def work(ctx: discord.ApplicationContext):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("You have a pending action that needs to be resolved.", ephemeral=True)
        return

    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)  # Reset cooldown for admins

    user = get_user(ctx.author.id)

    job_tiers = [
        {"name": "Newly Employed", "min": 1, "max": 5, "cost": 0},
        {"name": "Employee", "min": 1, "max": 10, "cost": 70},
        {"name": "Manager", "min": 3, "max": 20, "cost": 140},
        {"name": "Boss", "min": 10, "max": 50, "cost": 280},
        {"name": "C.E.O", "min": 70, "max": 400, "cost": 1000},
    ]

    tier = job_tiers[user["job_level"]]
    earnings = random.randint(tier["min"], tier["max"])
    user["balance"] += earnings
    save_users()
    await ctx.respond(f"You worked as a {tier['name']} and earned ${earnings}!", ephemeral=False)

@work_group.command(name="upgrade", description="Upgrade your job tier")
async def work_upgrade(ctx: discord.ApplicationContext):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("You have a pending action that needs to be resolved.", ephemeral=True)
        return

    user = get_user(ctx.author.id)

    job_tiers = [
        {"name": "Newly Employed", "min": 1, "max": 5, "cost": 0},
        {"name": "Employee", "min": 1, "max": 10, "cost": 70},
        {"name": "Manager", "min": 3, "max": 20, "cost": 140},
        {"name": "Boss", "min": 10, "max": 50, "cost": 280},
        {"name": "C.E.O", "min": 70, "max": 400, "cost": 1000},
    ]

    if user["job_level"] >= len(job_tiers) - 1:
        await ctx.respond("You are already at the highest job tier.", ephemeral=True)
        return

    next_tier = job_tiers[user["job_level"] + 1]
    if user["balance"] < next_tier["cost"]:
        await ctx.respond("You don't have enough money to upgrade.", ephemeral=True)
        return

    user["balance"] -= next_tier["cost"]
    user["job_level"] += 1
    save_users()
    await ctx.respond(f"You have upgraded to {next_tier['name']}!", ephemeral=False)

# Handle cooldown messages
@work.error
async def work_cooldown(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"This command is on cooldown. Try again in {round(error.retry_after, 2)} seconds.", ephemeral=True)

@bot.slash_command(name="beg", description="Beg for money (50% chance to succeed)")
@commands.cooldown(1, 60, commands.BucketType.user)
async def beg(ctx: discord.ApplicationContext):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return
    
    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)  # Reset cooldown for admins

    user = get_user(ctx.author.id)
    if random.random() < 0.5:
        amount = random.randint(1, 5)
        user["balance"] += amount
        save_users()
        await ctx.respond(f"Someone took pity on you and gave you ${amount}!", ephemeral=False)
    else:
        await ctx.respond("No one gave you any money. Try again later.", ephemeral=False)

# Handle cooldown messages
@beg.error
async def beg_cooldown(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"This command is on cooldown. Try again in {round(error.retry_after, 2)} seconds.", ephemeral=True)

pending_confirmations = {}

market_group = bot.create_group("market", "View, buy, or sell items in the market.")

@market_group.command(name="list", description="View items available in the market")
async def market_list(ctx: discord.ApplicationContext, page: int = 1):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("You have a pending action that needs to be resolved.", ephemeral=True)
        return

    items_per_page = 5
    total_pages = -(-len(market_items) // items_per_page)  # Calculate total pages

    if page < 1 or page > total_pages:
        await ctx.respond(f"Invalid page number. Please choose a page between 1 and {total_pages}.", ephemeral=True)
        return

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    items_on_page = list(market_items.items())[start_idx:end_idx]

    market_list = "\n".join([
        f"ID: `{item_id}` - {item['name']} (${item['price']})"
        for item_id, item in items_on_page
    ])
    await ctx.respond(f"**Market Items (Page {page}/{total_pages}):**\n{market_list}", ephemeral=False)


@market_group.command(name="buy", description="Buy an item from the market")
async def market_buy(ctx: discord.ApplicationContext, item_id: str, amount: int):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("You have a pending action that needs to be resolved.", ephemeral=True)
        return

    user = get_user(ctx.author.id)

    if item_id not in market_items or amount <= 0:
        await ctx.respond("Invalid item ID or amount. Please check the market list and try again.", ephemeral=True)
        return

    item = market_items[item_id]
    total_price = item["price"] * amount

    if user["balance"] < total_price:
        await ctx.respond("You don't have enough money to buy this quantity of the item.", ephemeral=True)
        return

    ongoing_interactions[ctx.author.id] = ctx.channel.id
    pending_confirmations[ctx.author.id] = ("buy", item_id, amount, ctx.channel.id)
    
    await ctx.respond(
        f"Confirm buying {amount}x {item['name']} for ${total_price}.\n"
        "Type `buy confirm` to confirm or `buy cancel` to cancel.",
        ephemeral=False
    )


@market_group.command(name="sell", description="Sell an item from your inventory")
async def market_sell(ctx: discord.ApplicationContext, item_id: str, amount: str):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("You have a pending action that needs to be resolved.", ephemeral=True)
        return

    user = get_user(ctx.author.id)

    if item_id not in user["inventory"]:
        await ctx.respond("You don't have this item in your inventory.", ephemeral=True)
        return

    if amount.lower() == "all":
        amount = user["inventory"][item_id]
    elif amount.isdigit():
        amount = int(amount)
    else:
        await ctx.respond("Invalid amount. Use a number or `all`.", ephemeral=True)
        return

    if amount <= 0 or user["inventory"].get(item_id, 0) < amount:
        await ctx.respond("Invalid input or insufficient inventory.", ephemeral=True)
        return

    item = all_items[item_id]
    total_price = item["sell_price"] * amount

    ongoing_interactions[ctx.author.id] = ctx.channel.id
    pending_confirmations[ctx.author.id] = ("sell", item_id, amount, ctx.channel.id)

    await ctx.respond(
        f"Confirm selling {amount}x {item['name']} for ${total_price}.\n"
        "Type `sell confirm` to confirm or `sell cancel` to cancel.",
        ephemeral=False
    )

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() in {"buy confirm", "buy cancel", "sell confirm", "sell cancel"}:
        if message.author.id not in pending_confirmations:
            await message.channel.send("You have no pending actions to confirm or cancel.")
            return

        action, item_id, amount, channel_id = pending_confirmations[message.author.id]

        if message.channel.id != channel_id:
            await message.channel.send("Confirm or cancel in the channel where the action was initiated.")
            return

        if message.content.lower().endswith("cancel"):
            del pending_confirmations[message.author.id]
            del ongoing_interactions[message.author.id]
            await message.channel.send("Action canceled.")
            return

        user = get_user(message.author.id)

        if action == "buy" and message.content.lower() == "buy confirm":
            item = market_items[item_id]
            total_price = item["price"] * amount
            user["balance"] -= total_price
            add_item(message.author.id, item_id, amount)
            await message.channel.send(f"You bought {amount}x {item['name']} for ${total_price}.")

        elif action == "sell" and message.content.lower() == "sell confirm":
            item = all_items[item_id]
            total_price = item["sell_price"] * amount
            remove_item(message.author.id, item_id, amount)
            user["balance"] += total_price
            save_users()
            await message.channel.send(f"You sold {amount}x {item['name']} for ${total_price}.")

        del pending_confirmations[message.author.id]
        del ongoing_interactions[message.author.id]
        return

    await bot.process_commands(message)

@bot.slash_command(name="use", description="Use a special item")
async def use(ctx: discord.ApplicationContext, item_id: str, amount: int):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return

    if amount <= 0:
        await ctx.respond("Invalid amount. Please enter a positive integer.", ephemeral=True)
        return

    user = get_user(ctx.author.id)

    # Validate the item and amount
    if item_id not in ["23", "24"]:
        await ctx.respond("This item cannot be used.", ephemeral=True)
        return

    if item_id not in user["inventory"] or user["inventory"][item_id] < amount:
        await ctx.respond("You don't have enough of this item to use.", ephemeral=True)
        return

    # Consume the item
    if not remove_item(ctx.author.id, item_id, amount):
        await ctx.respond("Failed to use the item.", ephemeral=True)
        return

    # Set the flags based on the item used
    if item_id == "23":
        user["next_hunt_dragon"] = user.get("next_hunt_dragon", 0) + amount
        await ctx.respond(f"You used {amount} Dragon's Lure(s)! The next {user['next_hunt_dragon']} hunt(s) will guarantee a Dragon spawn.")
    elif item_id == "24":
        user["next_fish_leviathan"] = user.get("next_fish_leviathan", 0) + amount
        await ctx.respond(f"You used {amount} Leviathan's Charm(s)! The next {user['next_fish_leviathan']} fish(es) will guarantee a Leviathan spawn.")

    save_users()

@bot.slash_command(name="hunt", description="Hunt animals for profit (requires a hunting rifle).")
@commands.cooldown(1, 35, commands.BucketType.user)
async def hunt(ctx: discord.ApplicationContext):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return

    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)

    user = get_user(ctx.author.id)
    if "2" not in user["inventory"] or user["inventory"]["2"] <= 0:
        await ctx.respond("You need a hunting rifle to hunt.", ephemeral=True)
        return

    # Determine if Dragon is guaranteed to spawn
    guaranteed_dragon = user.get("next_hunt_dragon", 0) > 0
    loot = []
    dragon_spawned = False

    for animal_id, animal in hunting_animals.items():
        if animal_id == "9":  # "The Dragon"
            if guaranteed_dragon:
                dragon_spawned = True
                user["next_hunt_dragon"] -= 1
                save_users()
            elif random.random() < animal["probability"]:
                dragon_spawned = True
        elif random.random() < animal["probability"]:
            loot.append(animal_id)

    if dragon_spawned:
        await ctx.respond("A Dragon has appeared! Type `shoot the dragon` within 10 seconds to try and claim it!", ephemeral=False)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=10)
            if msg.content.lower() == "shoot the dragon":
                if random.random() < 0.1:  # 10% chance to catch
                    dragon_id = "9.5" if random.random() < 0.01 else "9"  # 1% chance to mutate
                    add_item(ctx.author.id, dragon_id, 1)
                    dragon_name = Mutations[dragon_id]["name"] if ".5" in dragon_id else hunting_animals[dragon_id]["name"]
                    await ctx.respond(f"You successfully captured {dragon_name}! It has been added to your inventory.")
                else:
                    item = "20" if random.random() < 0.3 else "21"  # Body (30%) or Tail (70%)
                    add_item(ctx.author.id, item, 1)
                    await ctx.respond(f"The Dragon escaped! You salvaged its {Other_items[item]['name']}.")
            else:
                await ctx.respond("You failed to type the phrase correctly. The Dragon escaped!")
        except asyncio.TimeoutError:
            await ctx.respond("Time's up! The Dragon has flown away.")

    if loot:
        loot_with_mutations = []
        for item in loot:
            mutated = f"{item}.5" if random.random() < 0.01 else item
            add_item(ctx.author.id, mutated, 1)
            loot_with_mutations.append(mutated)

        loot_names = ", ".join([Mutations[item]["name"] if ".5" in item else hunting_animals[item]["name"] for item in loot_with_mutations])
        await ctx.respond(f"You went hunting and caught: {loot_names}!")
    else:
        await ctx.respond("You went hunting but found nothing.")

@hunt.error
async def rob_cooldown(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"This command is on cooldown. Try again in {round(error.retry_after, 2)} seconds.", ephemeral=True)

@bot.slash_command(name="fish", description="Fish for profit (requires a fishing rod).")
@commands.cooldown(1, 35, commands.BucketType.user)
async def fish(ctx: discord.ApplicationContext):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return

    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)

    user = get_user(ctx.author.id)
    if "1" not in user["inventory"] or user["inventory"]["1"] <= 0:
        await ctx.respond("You need a fishing rod to fish.", ephemeral=True)
        return

    # Determine if Leviathan is guaranteed to spawn
    guaranteed_leviathan = user.get("next_fish_leviathan", 0) > 0
    loot = []
    leviathan_spawned = False

    for fish_id, fish in fishing_fish.items():
        if fish_id == "17":  # "The Leviathan"
            if guaranteed_leviathan:
                leviathan_spawned = True
                user["next_fish_leviathan"] -= 1
                save_users()
            elif random.random() < fish["probability"]:
                leviathan_spawned = True
        elif random.random() < fish["probability"]:
            loot.append(fish_id)

    if leviathan_spawned:
        await ctx.respond("A Leviathan has appeared! Type `shoot the leviathan` within 10 seconds to try and claim it!", ephemeral=False)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=10)
            if msg.content.lower() == "shoot the leviathan":
                if random.random() < 0.1:  # 10% chance to catch
                    leviathan_id = "17.5" if random.random() < 0.01 else "17"  # 1% chance to mutate
                    add_item(ctx.author.id, leviathan_id, 1)
                    leviathan_name = Mutations[leviathan_id]["name"] if ".5" in leviathan_id else fishing_fish[leviathan_id]["name"]
                    await ctx.respond(f"You successfully captured {leviathan_name}! It has been added to your inventory.")
                else:
                    item = "19" if random.random() < 0.3 else "22"  # Segment (30%) or Tail (70%)
                    add_item(ctx.author.id, item, 1)
                    await ctx.respond(f"The Leviathan escaped! You salvaged its {Other_items[item]['name']}.")
            else:
                await ctx.respond("You failed to type the phrase correctly. The Leviathan escaped!")
        except asyncio.TimeoutError:
            await ctx.respond("Time's up! The Leviathan has swum away.")

    if loot:
        loot_with_mutations = []
        for item in loot:
            mutated = f"{item}.5" if random.random() < 0.01 else item
            add_item(ctx.author.id, mutated, 1)
            loot_with_mutations.append(mutated)

        loot_names = ", ".join([Mutations[item]["name"] if ".5" in item else fishing_fish[item]["name"] for item in loot_with_mutations])
        await ctx.respond(f"You went fishing and caught: {loot_names}!")
    else:
        await ctx.respond("You went fishing but caught nothing.")

@fish.error
async def rob_cooldown(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"This command is on cooldown. Try again in {round(error.retry_after, 2)} seconds.", ephemeral=True)

@bot.slash_command(name="inventory", description="View your or another user's inventory.")
async def inventory(ctx: discord.ApplicationContext, user: discord.User = None, page: int = 1):
    user = user or ctx.author  # Default to the command user if no target user is specified
    
    user_data = get_user(user.id)
    inventory = user_data.get("inventory", {})

    if not inventory:
        await ctx.respond(f"`{user.name}'s` inventory is empty.", ephemeral=True)
        return

    items_per_page = 10
    total_items = len(inventory)
    total_pages = math.ceil(total_items / items_per_page)

    if page < 1 or page > total_pages:
        await ctx.respond(f"Invalid page number. Please choose between 1 and {total_pages}.", ephemeral=True)
        return

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page

    inventory_slice = list(inventory.items())[start_idx:end_idx]
    items = "\n".join(
        [
            f"ID: `{item}` - {all_items.get(item, { 'name': 'Unknown' })['name']} (x{count})"
            for item, count in inventory_slice
        ]
    )

    await ctx.respond(f"**`{user.name}'s` Inventory (Page {page} of {total_pages}):**\n{items}")

@bot.command()
async def grant(ctx, target: discord.User, item_id: str, amount: int = 1):
    # Check if the command issuer is an authorized user
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("We have recently migrated to slash commands, type `/` and find Jerry to start using your favourite commands!")
        return

    if item_id.lower() == "all":
        # Grant all items with the specified quantity
        for item_key, item in all_items.items():
            add_item(target.id, item_key, amount)
        await ctx.reply(f"Granted {amount} of every item to `{target.name}`.")
        return

    # Validate the specific item ID
    if item_id not in all_items:
        await ctx.reply("Invalid item ID.")
        return

    # Add the item to the target user's inventory
    add_item(target.id, item_id, amount)
    item_name = all_items[item_id]["name"]
    await ctx.reply(f"Granted {amount}x {item_name} to `{target.name}`.")

@bot.slash_command(name="gift", description="Inside 'gift_type' put either the item id to gift an item or type 'money' and then 'amount'.")
async def gift(
    ctx: discord.ApplicationContext,
    target: discord.User,
    gift_type: str,
    amount: int
):
    if ctx.author.id in ongoing_interactions or target.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return

    # Ensure the user is not gifting to themselves
    if target.id == ctx.author.id:
        await ctx.respond("You cannot gift to yourself.", ephemeral=True)
        return

    # Fetch the giver's and recipient's data
    giver = get_user(ctx.author.id)
    recipient = get_user(target.id)

    if gift_type.lower() == "money":
        # Validate the giver's balance
        if giver["balance"] < amount:
            await ctx.respond("You don't have enough money to gift.", ephemeral=True)
            return
        
        # Transfer money
        giver["balance"] -= amount
        recipient["balance"] += amount
        save_users()
        await ctx.respond(f"You gifted **${amount}** to `{target.name}`!")

    elif gift_type.lower() in all_items:
        item_id = gift_type.lower()

        # Validate the giver's inventory
        if item_id not in giver["inventory"] or giver["inventory"][item_id] < amount:
            await ctx.respond("You don't have enough of that item to gift.", ephemeral=True)
            return

        # Transfer items
        remove_item(ctx.author.id, item_id, amount)
        add_item(target.id, item_id, amount)
        item_name = all_items[item_id]["name"]
        await ctx.respond(f"You gifted **{amount}x {item_name}** to `{target.name}`!")

    else:
        await ctx.respond("Invalid gift type. Use `money` or a valid item ID.", ephemeral=True)

@bot.command(aliases = ["resetdata"])
async def reset(ctx, target: discord.User):
    # Ensure the command issuer is the authorized admin
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("We have recently migrated to slash commands, type `/` and find Jerry to start using your favourite commands!")
        return

    # Reset the target user's data
    user_id = str(target.id)
    users[user_id] = {
        "balance": 40,
        "job_level": 0,
        "inventory": {}
    }
    save_users()
    await ctx.reply(f"`{target.name}'s` data has been reset.")

@bot.command(aliases = ["setbal"])
async def setbalance(ctx, target: discord.User, amount: int):
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("We have recently migrated to slash commands, type `/` and find Jerry to start using your favourite commands!")
        return

    # Set the target user's balance
    user = get_user(target.id)
    user["balance"] = amount
    save_users()
    await ctx.reply(f"`{target.name}'s` balance has been set to ${amount}.")

@bot.command()
async def stats(ctx, target: discord.User):
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("We have recently migrated to slash commands, type `/` and find Jerry to start using your favourite commands!")
        return

    user_data = get_user(target.id)
    inventory = "\n".join([f"{all_items[item]['name']}: {count}" for item, count in user_data["inventory"].items()]) or "Empty"
    await ctx.reply(
        f"**{target.name}'s Stats:**\n"
        f"- Balance: ${user_data['balance']}\n"
        f"- Job Level: {user_data['job_level']}\n"
        f"- Inventory:\n{inventory}"
    )

@bot.slash_command(name="itemlist", description="View available items in the game.")
async def itemlist(ctx: discord.ApplicationContext, page: int = 1):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return

    # Exclude admin-exclusive items
    user_items = {key: value for key, value in all_items.items() if key not in Admin_excl}
    
    items_per_page = 5
    total_items = len(user_items)
    total_pages = -(-total_items // items_per_page)  # Ceiling division
    
    if page < 1 or page > total_pages:
        await ctx.respond(f"Invalid page number. Please choose a page between 1 and {total_pages}.", ephemeral=True)
        return

    # Get the items for the current page
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    items_on_page = list(user_items.items())[start_idx:end_idx]
    
    # Format the item list for display
    item_list = "\n".join([
        f"ID: `{item_id}` - {item['name']} (${item.get('sell_price', 0)})"
        for item_id, item in items_on_page
    ])
    
    if item_list:
        await ctx.respond(f"**Item List (Page {page}/{total_pages}):**\n{item_list}\n\n- Use `/itemlist page:<number>` to navigate pages.")
    else:
        await ctx.respond("No items available.")


@bot.slash_command(name="daily", description="Claim your daily reward.")
async def daily(ctx: discord.ApplicationContext):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return

    user = get_user(ctx.author.id)
    last_claimed_key = "last_daily"
    now = datetime.utcnow()

    # Check if the user has already claimed their daily reward
    if last_claimed_key in user:
        last_claimed = datetime.fromisoformat(user[last_claimed_key])
        if now - last_claimed < timedelta(days=1):
            remaining_time = timedelta(days=1) - (now - last_claimed)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.respond(f"You've already claimed your daily reward. Try again in {hours}h {minutes}m {seconds}s.", ephemeral=True)
            return

    # Grant the reward and update the timestamp
    reward = random.randint(5, 10)
    user["balance"] += reward
    user[last_claimed_key] = now.isoformat()
    save_users()

    await ctx.respond(f"You've claimed your daily reward of ${reward}!")

@bot.slash_command(name="iteminfo", description="Get details about a specific item.")
async def iteminfo(ctx: discord.ApplicationContext, item_id: str):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return

    # Validate item ID
    if item_id not in all_items:
        await ctx.respond("Invalid item ID. Please check the item list and try again.", ephemeral=True)
        return

    # Fetch item details
    item = all_items[item_id]
    name = item["name"]
    sell_price = item.get("price", "Not for sale")
    resell_price = item.get("sell_price", "N/A")
    probability = item.get("probability", "Cannot be dropped")
    usable = item.get("usable", "no")

    # Get user inventory to display the number of copies owned
    user_data = get_user(ctx.author.id)
    owned = user_data["inventory"].get(item_id, 0)

    # Define item descriptions
    descriptions = {
        "1": "A basic fishing rod for catching fish. Not usable directly.",
        "2": "A hunting rifle used for hunting animals. Not usable directly.",
        "3": "A deer that you hunted. No specific use.",
        "4": "A wild boar that you hunted. No specific use.",
        "5": "An elk that you hunted. No specific use.",
        "6": "A mountain lion that you hunted. No specific use.",
        "7": "An eagle that you hunted. No specific use.",
        "8": "A rare snow leopard. No specific use.",
        "9": "The legendary Dragon. No specific use.",
        "10": "A mystical Unicorn. No specific use.",
        "11": "A common bluegill fish. No specific use.",
        "12": "A fresh salmon. No specific use.",
        "13": "A large tuna. No specific use.",
        "14": "A dangerous shark. No specific use.",
        "15": "A massive whale. No specific use.",
        "16": "An intelligent orca. No specific use.",
        "17": "The mythical Leviathan. No specific use.",
        "18": "Poseidon, god of the seas. No specific use.",
        "19": "A segment of the Leviathan. No specific use.",
        "20": "The body of a Dragon. No specific use.",
        "21": "The tail of a Dragon. No specific use.",
        "22": "The tail of a Leviathan. No specific use.",
        "23": "A lure that guarantees a Dragon spawn in your next hunt. Usable, consumes on usage.",
        "24": "A charm that guarantees a Leviathan spawn in your next fishing attempt. Usable, consumes on usage.",
        "25": "An item that saves you when you die if you have one inside your inventory. Not usable directly, consumes per failed death.",
        "26": "An item that saves you from being robbed once. Not usable directly, consumes per failed robbery.",
        "-1": "An item used for testing purposes."
    }

    # Include mutation descriptions
    for key, value in Mutations.items():
        descriptions[key] = f"A mutated version of {value['name']}. No specific use."

    description = descriptions.get(item_id, "No description available.")

    # Send item information as a response
    await ctx.respond(
        f"**Item Information**\n"
        f"- **Name**: {name}\n"
        f"- **Sell Price**: ${sell_price}\n"
        f"- **Resell Price**: ${resell_price}\n"
        f"- **Usable?**: {usable}\n"
        f"- **Owned**: {owned} copies\n"
        f"- **Description**: {description}\n"
    )

@bot.slash_command(name="gamble", description="Bet an amount with a specified multiplier. Higher risk, higher reward!")
@commands.cooldown(1, 30, commands.BucketType.user)
async def gamble(ctx: discord.ApplicationContext, 
                 amount: discord.Option(int, "The amount of money to bet"), 
                 multiplier: discord.Option(int, "The multiplier for your bet (must be greater than 1)")):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("You have an ongoing action that must be resolved first.", ephemeral=True)
        return

    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)

    user = get_user(ctx.author.id)

    # Validate inputs
    if amount <= 0:
        await ctx.respond("The bet amount must be greater than 0.", ephemeral=True)
        return

    if multiplier <= 1:
        await ctx.respond("The multiplier must be greater than 1.", ephemeral=True)
        return

    if user["balance"] < amount:
        await ctx.respond("You don't have enough money to place this bet.", ephemeral=True)
        return

    # Calculate winning probability
    winning_probability = 1 / multiplier

    # Determine outcome
    if random.random() < winning_probability:
        # User wins
        winnings = int(amount * multiplier)
        user["balance"] += winnings
        save_users()
        await ctx.respond(f"🎉 **You won ${winnings}!** Your new balance is **${user['balance']}**.")
    else:
        # User loses
        user["balance"] -= amount
        save_users()
        await ctx.respond(f"💸 **You lost ${amount}.** Your new balance is **${user['balance']}**.")

@gamble.error
async def work_cooldown(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"This command is on cooldown. Try again in {round(error.retry_after, 2)} seconds.", ephemeral=True)

@bot.slash_command(name="duel", description="Challenge another user to a duel for money!")
async def duel(ctx: discord.ApplicationContext, 
               target: discord.Option(discord.User, "The user you want to duel"), 
               amount: discord.Option(int, "The amount of money to wager")):
    
    # Prevent dueling yourself
    if ctx.author == target:
        await ctx.respond("You cannot duel yourself!", ephemeral=True)
        return

    # Check if either user has an ongoing action
    if ctx.author.id in ongoing_interactions or target.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that must be resolved first.", ephemeral=True)
        return

    challenger = get_user(ctx.author.id)
    opponent = get_user(target.id)

    # Prevent dueling in passive mode
    if challenger.get("passive_mode", False):
        await ctx.respond("You cannot start a duel while in passive mode.", ephemeral=True)
        return

    if opponent.get("passive_mode", False):
        await ctx.respond(f"`{target.name}` is in passive mode and cannot accept a duel.", ephemeral=True)
        return

    # Validate amount
    if amount <= 0:
        await ctx.respond("The wager amount must be greater than 0.", ephemeral=True)
        return

    if challenger["balance"] < amount:
        await ctx.respond("You don't have enough money for this duel.", ephemeral=True)
        return

    if opponent["balance"] < amount:
        await ctx.respond(f"`{target.name}` does not have enough money for this duel.", ephemeral=True)
        return

    # Track ongoing duel
    ongoing_interactions[ctx.author.id] = ctx.channel.id
    ongoing_interactions[target.id] = ctx.channel.id

    # Notify about the duel request
    await ctx.respond(
        f"⚔️ **Duel Challenge!** <@{ctx.author.id}> has challenged <@{target.id}> to a duel for **${amount}**!\n"
        "Both participants must confirm with **`duel accept`** or cancel with **`duel cancel`**."
    )

    confirmations = set()

    def check(m):
        return (
            m.channel == ctx.channel and  # Same channel
            m.author in {ctx.author, target} and  # One of the duelers
            m.content.lower() in {"duel accept", "duel cancel"}  # Only valid responses
        )

    try:
        while len(confirmations) < 2:
            msg = await bot.wait_for("message", check=check, timeout=60)
            if msg.content.lower() == "duel cancel":
                await ctx.respond(f"❌ The duel was canceled by <@{msg.author.id}>.")
                ongoing_interactions.pop(ctx.author.id, None)
                ongoing_interactions.pop(target.id, None)
                return
            confirmations.add(msg.author.id)
    except asyncio.TimeoutError:
        await ctx.respond("⏳ **Duel timed out.** Both participants did not confirm in time.")
        ongoing_interactions.pop(ctx.author.id, None)
        ongoing_interactions.pop(target.id, None)
        return

    # Determine the winner
    winner, loser = (ctx.author, target) if random.random() < 0.5 else (target, ctx.author)
    winner_data = get_user(winner.id)
    loser_data = get_user(loser.id)

    # Update balances
    winner_data["balance"] += amount
    loser_data["balance"] -= amount
    save_users()

    # Remove users from ongoing interactions
    ongoing_interactions.pop(ctx.author.id, None)
    ongoing_interactions.pop(target.id, None)

    # Announce the duel result
    await ctx.respond(
        f"🏆 **The duel is over!** <@{winner.id}> **wins ${amount}** from <@{loser.id}>!\n"
        f"**New balances:**\n"
        f"- `{winner.name}`: **${winner_data['balance']}**\n"
        f"- `{loser.name}`: **${loser_data['balance']}**"
    )

@bot.slash_command(name="trade", description="Trade an item with another user.")
async def trade(ctx: discord.ApplicationContext, 
                target: discord.Option(discord.User, "The user you want to trade with"), 
                your_item_id: discord.Option(str, "Your item ID to trade"), 
                their_item_id: discord.Option(str, "The item ID you want in exchange")):
    
    # Prevent self-trading
    if ctx.author == target:
        await ctx.respond("You cannot trade with yourself!", ephemeral=True)
        return

    # Check if either user has an ongoing action
    if ctx.author.id in ongoing_interactions or target.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that must be resolved first.", ephemeral=True)
        return
    
    trader = get_user(ctx.author.id)
    target_user = get_user(target.id)

    # Check if either user has passive mode enabled
    if trader.get("passive_mode", False):
        await ctx.respond("You cannot initiate a trade while in passive mode.", ephemeral=True)
        return

    if target_user.get("passive_mode", False):
        await ctx.respond(f"`{target.name}` is in passive mode and cannot be invited to trade.", ephemeral=True)
        return

    # Validate user inventory
    if your_item_id not in trader["inventory"] or trader["inventory"][your_item_id] <= 0:
        await ctx.respond("You don't have that item to trade.", ephemeral=True)
        return

    if their_item_id not in target_user["inventory"] or target_user["inventory"][their_item_id] <= 0:
        await ctx.respond(f"`{target.name}` does not have that item to trade.", ephemeral=True)
        return

    # Add users to ongoing interactions (store channel ID)
    ongoing_interactions[ctx.author.id] = ctx.channel.id
    ongoing_interactions[target.id] = ctx.channel.id

    # Notify both users of the trade request
    await ctx.respond(
        f"🔄 **Trade Request!** <@{ctx.author.id}> wants to trade `{your_item_id}` for `{their_item_id}` with <@{target.id}>.\n"
        "Both participants must confirm with **`trade confirm`** or cancel with **`trade cancel`**."
    )

    # Function to validate confirmations
    def check(m):
        return (
            m.channel == ctx.channel and  # Must be in the same channel
            m.author in {ctx.author, target} and  # Must be one of the participants
            m.content.lower() in {"trade confirm", "trade cancel"}  # Must type 'trade confirm' or 'trade cancel'
        )

    confirmations = set()
    try:
        while len(confirmations) < 2:
            msg = await bot.wait_for("message", check=check, timeout=60)
            if msg.content.lower() == "trade cancel":
                await ctx.respond(f"❌ The trade was canceled by <@{msg.author.id}>.")
                ongoing_interactions.pop(ctx.author.id, None)
                ongoing_interactions.pop(target.id, None)
                return
            confirmations.add(msg.author.id)
    except asyncio.TimeoutError:
        await ctx.respond("⏳ **Trade timed out.** Both participants did not confirm in time.")
        ongoing_interactions.pop(ctx.author.id, None)
        ongoing_interactions.pop(target.id, None)
        return

    # Perform the trade if both users confirm
    remove_item(ctx.author.id, your_item_id, 1)
    add_item(ctx.author.id, their_item_id, 1)
    remove_item(target.id, their_item_id, 1)
    add_item(target.id, your_item_id, 1)

    # Remove users from ongoing interactions
    ongoing_interactions.pop(ctx.author.id, None)
    ongoing_interactions.pop(target.id, None)

    # Notify success
    await ctx.respond(f"✅ **Trade successful!** <@{ctx.author.id}> traded `{your_item_id}` for `{their_item_id}` with <@{target.id}>.")

@bot.command()
async def spawn(ctx, item_id: str):
    # Check if the user is authorized
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("We have recently migrated to slash commands, type `/` and find Jerry to start using your favourite commands!")
        return

    # Validate the item ID
    if item_id not in all_items:
        await ctx.reply("Invalid item ID. Please check the item list and try again.")
        return

    item_name = all_items[item_id]["name"]

    # Special handling for Dragon and Leviathan
    if item_id == "9":
        await ctx.reply("A Dragon has appeared! Type `shoot the dragon` within 10 seconds to try and claim it!")

        def check(m):
            return (
                m.channel == ctx.channel and
                m.content.lower() == "shoot the dragon"
            )

        try:
            msg = await bot.wait_for("message", check=check, timeout=10)
            add_item(msg.author.id, item_id, 1)
            await ctx.reply(f"<@{msg.author.id}> has successfully captured the Dragon! It has been added to their inventory.")
        except asyncio.TimeoutError:
            await ctx.reply("Time's up! The Dragon has flown away.")
        return

    elif item_id == "17":
        await ctx.reply("A Leviathan has appeared! Type `shoot the leviathan` within 10 seconds to try and claim it!")

        def check(m):
            return (
                m.channel == ctx.channel and
                m.content.lower() == "shoot the leviathan"
            )

        try:
            msg = await bot.wait_for("message", check=check, timeout=10)
            add_item(msg.author.id, item_id, 1)
            await ctx.reply(f"<@{msg.author.id}> has successfully captured the Leviathan! It has been added to their inventory.")
        except asyncio.TimeoutError:
            await ctx.reply("Time's up! The Leviathan has swum away.")
        return
    # Generic item spawn
    await ctx.reply(f"{item_name} (ID: `{item_id}`) has been summoned from the divine heavens! Type `i wanna claim {item_id}` to claim the item.")

    def check(m):
        return (
            m.channel == ctx.channel and
            m.content.lower() == f"i wanna claim {item_id}" and
            m.author.id != ctx.author.id  # Ensure the summoner cannot claim their own item
        )

    try:
        msg = await bot.wait_for("message", check=check, timeout=10)
        add_item(msg.author.id, item_id, 1)
        await ctx.reply(f"<@{msg.author.id}> has claimed the item {item_name}! It has been added to their inventory.")
    except asyncio.TimeoutError:
        await ctx.reply(f"Time's up! The item {item_name} has disappeared back into the divine heavens.")

@bot.command()
async def whitelist(ctx, user: discord.User):
    # Check if the user is authorized
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("We have recently migrated to slash commands, type `/` and find Jerry to start using your favourite commands!")
        return

    # Add the user to the authorized list
    user_id = str(user.id)
    if user_id in AUTHORIZED_USERS:
        await ctx.reply(f"<@{user.id}> is already an authorized user.")
        return

    AUTHORIZED_USERS.append(user_id)
    await ctx.reply(f"<@{user.id}> has been added to the list of authorized temporarily.")

auction_file = "auction_list.json"
if not os.path.exists(auction_file):
    with open(auction_file, "w") as f:
        json.dump([], f)

def load_auctions():
    with open(auction_file, "r") as f:
        return json.load(f)

def save_auctions(auctions):
    with open(auction_file, "w") as f:
        json.dump(auctions, f, indent=4)

def generate_market_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

auctions = load_auctions()

auction_group = bot.create_group("auction", "Auction commands.")

@auction_group.command(name="help", description="Show auction command list.")
async def auction_help(ctx: discord.ApplicationContext):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve", ephemeral=True)
        return
    await ctx.respond("Available commands: \n"
                      "- `/auction help`: Show this help menu.\n"
                      "- `/auction show <page>`: View auction listings.\n"
                      "- `/auction sell <item_id> <price>`: Start an auction.\n"
                      "- `/auction buy <market_code>`: Buy an item.\n"
                      "- `/auction pending <page>`: View your auctions.\n"
                      "- `/auction takedown <market_code>`: Remove your auction.\n"
                      "- `/auction view <item_id> <page>`: View listings for an item.")

@auction_group.command(name="sell", description="Sell an item in the auction.")
async def auction_sell(ctx: discord.ApplicationContext,
                       item_id: discord.Option(str, "The item ID you want to sell"),
                       price: discord.Option(int, "The price for the item")):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return

    user_id = str(ctx.author.id)
    user_data = get_user(user_id)

    if item_id not in user_data["inventory"] or user_data["inventory"][item_id] <= 0:
        await ctx.respond("You don't have this item in your inventory.", ephemeral=True)
        return

    market_code = generate_market_code()
    ongoing_interactions[ctx.author.id] = ctx.channel.id

    await ctx.respond(f"Confirm selling item `{item_id}` for ${price} as auction `{market_code}`.\n"
                      "Type `auction confirm` to proceed or `auction cancel` to cancel.", ephemeral=False)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        if msg.content.lower() == "auction confirm":
            auctions.append({
                "seller_id": user_id,
                "item_id": item_id,
                "price": price,
                "market_code": market_code,
                "buyer_id": None
            })
            save_auctions(auctions)
            remove_item(user_id, item_id, 1)
            await ctx.respond(f"Item `{item_id}` is now on auction with code `{market_code}`.", ephemeral=False)
        else:
            await ctx.respond("Auction canceled.", ephemeral=True)
    except asyncio.TimeoutError:
        await ctx.respond("Auction timed out. Please try again.", ephemeral=True)
    finally:
        ongoing_interactions.pop(ctx.author.id, None)

@auction_group.command(name="buy", description="Buy an item from the auction.")
async def auction_buy(ctx: discord.ApplicationContext,
                      market_code: discord.Option(str, "The auction market code")):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve", ephemeral=True)
        return
    user_id = str(ctx.author.id)
    auction = next((a for a in auctions if a["market_code"] == market_code), None)

    if not auction:
        await ctx.respond("Invalid market code.", ephemeral=True)
        return

    if auction["seller_id"] == user_id:
        await ctx.respond("You cannot buy your own auction.", ephemeral=True)
        return

    user_data = get_user(user_id)

    if user_data["balance"] < auction["price"]:
        await ctx.respond("You don't have enough money to buy this item.", ephemeral=True)
        return

    auction["buyer_id"] = user_id
    save_auctions(auctions)

    seller_data = get_user(auction["seller_id"])
    seller_data["balance"] += auction["price"]
    user_data["balance"] -= auction["price"]
    add_item(user_id, auction["item_id"], 1)

    await ctx.respond(f"You bought `{auction['item_id']}` for ${auction['price']}.", ephemeral=False)
    seller_user = await bot.fetch_user(int(auction["seller_id"]))
    await seller_user.send(f"Your auction `{market_code}` has been sold to <@{user_id}>.", allowed_mentions=discord.AllowedMentions(users=True))

@auction_group.command(name="show", description="Show all auctions.")
async def auction_show(ctx: discord.ApplicationContext,
                       page: discord.Option(int, "The page number", default=1)):
    items_per_page = 5
    total_pages = (len(auctions) + items_per_page - 1) // items_per_page
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve", ephemeral=True)
        return
    if page < 1 or page > total_pages:
        await ctx.respond(f"There are no auctioned items.", ephemeral=True)
        return

    start = (page - 1) * items_per_page
    end = start + items_per_page
    listings = auctions[start:end]

    auction_list = "\n".join([
        f"Market Code: `{a['market_code']}`, Item: `{a['item_id']}`, Price: ${a['price']}, Seller: <@{a['seller_id']}>"
        for a in listings if a["buyer_id"] is None
    ])
    await ctx.respond(f"**Auction Listings (Page {page}/{total_pages}):**\n{auction_list}", ephemeral=False,allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

@auction_group.command(name="pending", description="View your pending auctions.")
async def auction_pending(ctx: discord.ApplicationContext,
                          page: discord.Option(int, "The page number", default=1)):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve", ephemeral=True)
        return
    user_id = str(ctx.author.id)
    user_auctions = [a for a in auctions if a["seller_id"] == user_id and a["buyer_id"] is None]
    items_per_page = 5
    total_pages = (len(user_auctions) + items_per_page - 1) // items_per_page

    if page < 1 or page > total_pages:
        await ctx.respond(f"Invalid page. Choose a page between 1 and {total_pages}.", ephemeral=True)
        return

    start = (page - 1) * items_per_page
    end = start + items_per_page
    listings = user_auctions[start:end]

    auction_list = "\n".join([
        f"Market Code: `{a['market_code']}`, Item: `{a['item_id']}`, Price: ${a['price']}"
        for a in listings
    ])
    await ctx.respond(f"**Your Pending Auctions (Page {page}/{total_pages}):**\n{auction_list}", ephemeral=False)

@auction_group.command(name="takedown", description="Remove your auction.")
async def auction_takedown(ctx: discord.ApplicationContext,
                           market_code: discord.Option(str, "The auction market code")):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve", ephemeral=True)
        return
    user_id = str(ctx.author.id)
    auction = next((a for a in auctions if a["market_code"] == market_code), None)

    if not auction:
        await ctx.respond("Invalid market code.", ephemeral=True)
        return

    if auction["seller_id"] != user_id:
        await ctx.respond("You can only take down your own auctions.", ephemeral=True)
        return

    if auction["buyer_id"] is not None:
        await ctx.respond("This auction has already been sold and cannot be taken down.", ephemeral=True)
        return

    auctions.remove(auction)
    save_auctions(auctions)
    add_item(user_id, auction["item_id"], 1)
    await ctx.respond(f"Auction `{market_code}` has been taken down and item returned to your inventory.", ephemeral=False)
@auction_group.command(name="view", description="View auctions for a specific item.")
async def auction_view(ctx: discord.ApplicationContext,
                       item_id: discord.Option(str, "The item ID to search for"),
                       page: discord.Option(int, "The page number", default=1)):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve", ephemeral=True)
        return
    item_auctions = [a for a in auctions if a["item_id"] == item_id and a["buyer_id"] is None]
    items_per_page = 5
    total_pages = (len(item_auctions) + items_per_page - 1) // items_per_page

    if page < 1 or page > total_pages:
        await ctx.respond(f"Invalid page. Choose a page between 1 and {total_pages}.", ephemeral=True)
        return

    start = (page - 1) * items_per_page
    end = start + items_per_page
    listings = item_auctions[start:end]

    if not listings:
        await ctx.respond("No listings available for this item on this page.", ephemeral=True)
        return

    auction_list = "\n".join([
        f"Market Code: `{a['market_code']}`, Price: ${a['price']}, Seller: <@{a['seller_id']}>"
        for a in listings
    ])
    await ctx.respond(f"**Listings for Item `{item_id}` (Page {page}/{total_pages}):**\n{auction_list}", ephemeral=False)

@bot.slash_command(name="passive", description="Toggle passive mode (prevents duels, trades, and robbery).")
async def passivemode(ctx: discord.ApplicationContext,
                      mode: discord.Option(str, "Enable or disable passive mode", choices=["on", "off"])):
    if ctx.author.id in ongoing_interactions:
        await ctx.respond("You have a pending action to resolve.", ephemeral=True)
        return

    user = get_user(ctx.author.id)
    now = datetime.utcnow()

    # Check if cooldown applies
    last_used = datetime.fromisoformat(user.get("last_passive_use", "1970-01-01T00:00:00"))
    cooldown = timedelta(hours=10)

    if now - last_used < cooldown:
        remaining_time = cooldown - (now - last_used)
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        await ctx.respond(f"Passive mode can only be toggled every 10 hours. Try again in {hours}h {minutes}m.", ephemeral=True)
        return

    # Update passive mode state and save last usage time
    user["passive_mode"] = mode == "on"
    user["last_passive_use"] = now.isoformat()
    save_users()

    state = "enabled" if user["passive_mode"] else "disabled"
    await ctx.respond(f"Passive mode has been {state}. You will {'not ' if user['passive_mode'] else ''}be invited to duels or trades. You also {'cannot' if user['passive_mode'] else 'can'} be robbed.", ephemeral=False)

# Add the crime command
@bot.slash_command(name="crime", description="Commit a crime and earn money (or face consequences).")
@commands.cooldown(1, 30, commands.BucketType.user)
async def crime(ctx: discord.ApplicationContext):
    user = get_user(ctx.author.id)

    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)  # Reset cooldown for authorized users

    if ctx.author.id in ongoing_interactions:
        await ctx.respond("You already have a pending interaction. Complete or cancel it first.", ephemeral=True)
        return

    # Add user to ongoing interactions
    ongoing_interactions[ctx.author.id] = ctx.channel.id

    # Define crime options
    crimes = [
        {"name": "Arson", "reward": (20, 30), "death_chance": 0.01, "success_chance": 0.50,
         "messages": {"success": "You set a building on fire. You earned ${earnings}.",
                      "fail": "The wind blows out the flames before it even started.",
                      "death": "You ended up burning yourself. You are dead."}},
        
        {"name": "Shop-lifting", "reward": (10, 20), "death_chance": 0.007, "success_chance": 0.50,
         "messages": {"success": "You stole a piece of grocery and earned ${earnings}.",
                      "fail": "You got caught, RUN.",
                      "death": "Security caught and beat you to death."}},

        {"name": "Robbing", "reward": (25, 40), "death_chance": 0.014, "success_chance": 0.45,
         "messages": {"success": "You stole ${earnings} from an old grandma. Proud?",
                      "fail": "You got caught but managed to escape.",
                      "death": "You got caught and beaten up to death."}},

        {"name": "Cyberbullying", "reward": (5, 15), "death_chance": 0.005, "success_chance": 0.55,
         "messages": {"success": "The kid sent you ${earnings} to stop bullying.",
                      "fail": "Discord mods banned you, time for a new account.",
                      "death": "You laughed so hard that you choked to death."}},

        {"name": "Hacking", "reward": (20, 30), "death_chance": 0.01, "success_chance": 0.50,
         "messages": {"success": "You hacked into Jerry's system and stole ${earnings}.",
                      "fail": "The firewall was too strong this time.",
                      "death": "The FBI noticed your actions, and you were executed for a billion-dollar data breach."}},

        {"name": "Vandalism", "reward": (5, 15), "death_chance": 0.005, "success_chance": 0.55,
         "messages": {"success": "You wrote 'Jerry' on a wall, and xVapure sent you ${earnings} for free promotion.",
                      "fail": "You ran out of spray paint.",
                      "death": "You fell from a 10-story building while painting and died."}}
    ]

    # Select 3 random crimes
    selected_crimes = random.sample(crimes, 3)

    # Add a "Cancel" option
    selected_crimes.append({"name": "No more crimes.", "reward": (0, 0), "death_chance": 0, "success_chance": 0,
                            "messages": {"success": "You decided not to commit a crime.", "fail": "", "death": ""}})

    # Create dropdown selection for crimes
    class CrimeDropdown(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label=crime["name"], value=crime["name"])
                for crime in selected_crimes
            ]
            super().__init__(placeholder="Select a crime to commit...", options=options)

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id in ongoing_interactions:
                crime_selected = next(c for c in selected_crimes if c["name"] == self.values[0])

                if crime_selected["name"] == "No more crimes.":
                    # If the user cancels, just remove them from ongoing interactions
                    ongoing_interactions.pop(ctx.author.id, None)
                    await interaction.response.send_message("You decided not to commit any crime. Good idea!", ephemeral=False)
                    return

                outcome = random.random()

                if outcome < crime_selected["death_chance"]:
                    # Death outcome
                    if "25" in user["inventory"] and user["inventory"]["25"] > 0:
                        remove_item(ctx.author.id, "25", 1)
                        await interaction.response.send_message("You nearly died, but a life-saver saved you!", ephemeral=False)
                    else:
                        user["balance"] = int(user["balance"] * 0.8)
                        if user["inventory"]:
                            random_item = random.choice(list(user["inventory"].keys()))
                            remove_item(ctx.author.id, random_item, 1)
                        save_users()
                        await interaction.response.send_message(crime_selected["messages"]["death"], ephemeral=False)
                elif outcome < crime_selected["death_chance"] + crime_selected["success_chance"]:
                    # Successful crime
                    earnings = random.randint(*crime_selected["reward"])
                    user["balance"] += earnings
                    save_users()
                    await interaction.response.send_message(crime_selected["messages"]["success"].replace("{earnings}", f"{earnings}"), ephemeral=False)
                else:
                    # Failed crime
                    await interaction.response.send_message(crime_selected["messages"]["fail"], ephemeral=False)

                # Remove user from ongoing interactions once they have completed the interaction
                ongoing_interactions.pop(ctx.author.id, None)

    # Send message with dropdown
    view = discord.ui.View()
    view.add_item(CrimeDropdown())
    await ctx.respond("Select a crime to commit:", view=view, ephemeral=False)

@crime.error
async def rob_cooldown(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"This command is on cooldown. Try again in {round(error.retry_after, 2)} seconds.", ephemeral=True)

@bot.slash_command(name="rob", description="Attempt to rob another user (50% success rate).")
@commands.cooldown(1, 300, commands.BucketType.user)  # 5-minute cooldown
async def rob(ctx: discord.ApplicationContext, target: discord.User):
    if ctx.author == target:
        await ctx.respond("You cannot rob yourself!", ephemeral=True)
        return

    if ctx.author.id in ongoing_interactions or target.id in ongoing_interactions:
        await ctx.respond("One of the participants has a pending action that they need to resolve.", ephemeral=True)
        return

    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)  # Reset cooldown for admins

    # Get user and victim data
    robber = get_user(ctx.author.id)
    victim = get_user(target.id)

    # Check if users are in passive mode
    if robber.get("passive_mode", False):
        await ctx.respond("You cannot rob while in passive mode.", ephemeral=True)
        return

    if victim.get("passive_mode", False):
        await ctx.respond(f"`{target.name}` is in passive mode and cannot be robbed.", ephemeral=True)
        return

    # Check if the victim has been robbed recently
    if "last_robbed" in victim:
        last_robbed = datetime.fromisoformat(victim["last_robbed"])
        if datetime.utcnow() - last_robbed < timedelta(minutes=10):
            await ctx.respond(f"`{target.name}` was recently robbed. Please wait before trying again.", ephemeral=True)
            return

    # Check if both robber and victim have sufficient balance
    if robber["balance"] < 100:
        await ctx.respond("You need at least $100 to attempt a robbery.", ephemeral=True)
        return

    if victim["balance"] < 100:
        await ctx.respond(f"`{target.name}` does not have enough money to be robbed.", ephemeral=True)
        return

    # Check for pad lock protection
    if victim["inventory"].get("26", 0) > 0:  # Pad lock ID: 26
        victim["inventory"]["26"] -= 1  # Consume one pad lock
        if victim["inventory"]["26"] == 0:
            del victim["inventory"]["26"]

        fine = int(robber["balance"] * 0.1)
        robber["balance"] -= fine
        save_users()

        await ctx.respond(
            f"`{target.name}` had a pad lock! The robbery failed, and you lost ${fine}. One pad lock was consumed from their inventory.",
            ephemeral=False
        )
        return

    # Robbery attempt (50% success rate)
    if random.random() < 0.5:
        # Successful robbery
        amount_stolen = random.randint(
            int(victim["balance"] * 0.2), int(victim["balance"] * 0.5)
        )
        victim["balance"] -= amount_stolen
        robber["balance"] += amount_stolen
        victim["last_robbed"] = datetime.utcnow().isoformat()
        save_users()

        # Notify the victim in DMs
        try:
            await target.send(
                f"You have been robbed by `{ctx.author.name}` and lost ${amount_stolen}."
            )
        except discord.Forbidden:
            await ctx.respond(
                f"Robbery successful, but I couldn't notify `{target.name}` in DMs."
            )

        await ctx.respond(
            f"You successfully robbed `{target.name}` and stole ${amount_stolen}!"
        )
    else:
        # Failed robbery
        fine = int(robber["balance"] * 0.1)
        robber["balance"] -= fine
        save_users()

        await ctx.respond(
            f"The robbery failed! You were caught and had to pay a fine of ${fine}."
        )

@rob.error
async def rob_cooldown(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"This command is on cooldown. Try again in {round(error.retry_after, 2)} seconds.", ephemeral=True)


@rob.error
async def rob_cooldown(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"This command is on cooldown. Try again in {round(error.retry_after, 2)} seconds.", ephemeral=True)


@bot.slash_command(name="ping", description="Check bot latency")
async def ping(ctx: discord.ApplicationContext):
    latency = bot.latency * 1000  # Convert to milliseconds
    await ctx.respond(f"Pong! 🏓 `{latency:.2f}ms`")

@bot.command(aliases=["speak"])
async def say(ctx, *, msg=None):
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("We have recently migrated to slash commands, type `/` and find Jerry to start using your favourite commands!")
        return
    
    if msg is None:
        await ctx.reply("ㅤ")  # Sends an invisible space character
    else:
        try:
            await ctx.message.delete()  # Delete the command message
        except discord.Forbidden:
            await ctx.reply("I don't have permission to delete messages.")
            return

        await ctx.send(msg)  # Send the user's message

@bot.command(aliases=["dm"])
async def directmessage(ctx, target: str, *, message: str):
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("We have recently migrated to slash commands, type `/` and find Jerry to start using your favourite commands!")
        return

    if target.lower() == "all":
        # Sending a message to all registered users
        failed = 0
        success = 0

        for user_id in users.keys():
            try:
                user = await bot.fetch_user(int(user_id))
                await user.send(message)
                success += 1
            except discord.Forbidden:
                failed += 1
            except discord.HTTPException:
                failed += 1

        await ctx.reply(f"✅ Successfully sent DMs to {success} users.\n❌ Failed to DM {failed} users (they might have DMs disabled).")
    
    else:
        # Sending a message to a specific user
        try:
            user = await commands.UserConverter().convert(ctx, target)
            await user.send(message)
            await ctx.reply(f"✅ Successfully sent a DM to {user.name}.")
        except commands.BadArgument:
            await ctx.reply("❌ Invalid user. Please mention a valid user.")
        except discord.Forbidden:
            await ctx.reply("❌ I cannot send a DM to this user. They might have DMs disabled.")
        except discord.HTTPException:
            await ctx.reply("❌ Failed to send the message due to a network error.")

bot.run(DISCORD_BOT_TOKEN)
