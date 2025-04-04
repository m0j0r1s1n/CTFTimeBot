import discord
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the base URLs for the CTFTime API
team_base_url = 'https://ctftime.org/api/v1/teams/'
top_teams_by_country_url = 'https://ctftime.org/api/v1/top-by-country/'
events_url = 'https://ctftime.org/api/v1/events/'
top_teams = 'https://ctftime.org/api/v1/top/'
top_teams_by_year = 'https://ctftime.org/api/v1/top/{year}/'
specific_event ='https://ctftime.org/api/v1/events/{event_id}/'

# Set the headers to accept JSON responses and include a User-Agent
headers = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Define the bot
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
client = discord.Client(intents=intents)

# Dictionary to store custom CTF events and their challenges
custom_ctfs = {}

# File to store custom CTFs
CUSTOM_CTFS_FILE = 'custom_ctfs.json'

def save_custom_ctfs():
    with open(CUSTOM_CTFS_FILE, 'w') as f:
        json.dump(custom_ctfs, f)

def load_custom_ctfs():
    global custom_ctfs
    if os.path.exists(CUSTOM_CTFS_FILE):
        with open(CUSTOM_CTFS_FILE, 'r') as f:
            custom_ctfs = json.load(f)
    else:
        custom_ctfs = {}

def fetch_team_details(team_id):
    url = f'{team_base_url}{team_id}/'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_events(limit, start, finish):
    url = f'{events_url}?limit={limit}&start={start}&finish={finish}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_upcoming_events(limit=5):
    url = f'{events_url}?limit={limit}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_top_teams():
    url = f'{top_teams}?limit=10'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_top_teams_by_year(year):
    url = top_teams_by_year.format(year=year)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_specific_event(event_id):
    url = specific_event.format(event_id=event_id)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_top_teams_by_country(country_code):
    url = f'{top_teams_by_country_url}{country_code}/'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    load_custom_ctfs()

async def create_ctf_role(guild, ctf_name):
    # Check if the role already exists
    role_name = f"CTF: {ctf_name}"
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        # Create the role if it doesn't exist
        role = await guild.create_role(name=role_name, mentionable=True)
        print(f"Created role: {role_name}")
    return role

async def assign_ctf_role(member, role):
    # Assign the role to the user
    if role not in member.roles:
        await member.add_roles(role)
        print(f"Assigned role {role.name} to {member.name}")
    else:
        print(f"{member.name} already has the role {role.name}")

async def remove_ctf_role(member, role):
    # Remove the role from the user
    if role in member.roles:
        await member.remove_roles(role)
        print(f"Removed role {role.name} from {member.name}")
    else:
        print(f"{member.name} does not have the role {role.name}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f"Received message: {message.content}")

    if message.content.startswith('!help_ctftime'): 
        embed = discord.Embed(title="CTFTime Bot Help", description="Available commands:", color=0x00ff00)
        embed.add_field(name="!create_ctf <name>", value="Create a new custom CTF event with the given name.", inline=False)
        embed.add_field(name="!delete_ctf <ctf_name>", value="Delete a custom CTF event by name.", inline=False)
        embed.add_field(name="!join_ctf <ctf_name>", value="Join a custom CTF event and get the associated role.", inline=False)
        embed.add_field(name="!leave_ctf <ctf_name>", value="Leave a CTF and remove the associated role.", inline=False)
        embed.add_field(name="!add_challenge <ctf_name> <challenge_name>", value="Add a new challenge to a specific CTF.", inline=False)
        embed.add_field(name="!delete_challenge <ctf_name> <challenge_name>", value="Delete a challenge from a specific CTF.", inline=False)
        embed.add_field(name="!allocate_challenge <ctf_name> <challenge_name>", value="Allocate a challenge to yourself in a specific CTF.", inline=False)
        embed.add_field(name="!solve_challenge <ctf_name> <challenge_name>", value="Mark a challenge as solved in a specific CTF.", inline=False)
        embed.add_field(name="!list_challenges <ctf_name>", value="List all challenges for a specific CTF.", inline=False)
        embed.add_field(name="!show_ctf <ctf_name>", value="Show details of a specific CTF, including solved and unsolved challenges.", inline=False)
        embed.add_field(name="!list_ctfs", value="List upcoming CTF events with their IDs.", inline=False)
        embed.add_field(name="!time_until_start <event_id>", value="Get the time remaining until a specific CTF event starts.", inline=False)
        embed.add_field(name="!time_left <event_id>", value="Get the remaining time for a specific CTF event.", inline=False)
        embed.add_field(name="!upcoming <limit>", value="Fetch a specified number of upcoming events (default is 5).", inline=False)
        await message.channel.send(embed=embed)

    elif message.content.startswith('!create_ctf'):
        try:
            ctf_name = ' '.join(message.content.split()[1:])
            if not ctf_name:
                await message.channel.send("Usage: !create_ctf <name>")
                return

            if ctf_name in custom_ctfs:
                await message.channel.send(f"A CTF with the name '{ctf_name}' already exists.")
            else:
                custom_ctfs[ctf_name] = {
                    'name': ctf_name,
                    'challenges': {}
                }
                save_custom_ctfs()

                # Create a role for the CTF
                guild = message.guild
                role = await create_ctf_role(guild, ctf_name)
                await message.channel.send(f"The Epic CTF '{ctf_name}' has been created. Role '{role.name}' has been created.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!delete_ctf'):
        try:
            ctf_name = ' '.join(message.content.split()[1:])
            if not ctf_name:
                await message.channel.send("Usage: !delete_ctf <ctf_name>")
                return

            if ctf_name not in custom_ctfs:
                await message.channel.send(f"CTF '{ctf_name}' does not exist.")
            else:
                # Delete the CTF from the custom_ctfs dictionary
                del custom_ctfs[ctf_name]
                save_custom_ctfs()

                # Optionally, delete the associated role
                guild = message.guild
                role = discord.utils.get(guild.roles, name=f"CTF: {ctf_name}")
                if role:
                    await role.delete()
                    await message.channel.send(f"CTF '{ctf_name}' and its associated role have been deleted.")
                else:
                    await message.channel.send(f"CTF '{ctf_name}' has been deleted, but no associated role was found.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!time_until_start'):
        try:
            event_id = int(message.content.split()[1])
            data = fetch_specific_event(event_id)
            if not data:
                await message.channel.send("No data received for the specified event.")
            else:
                start_time = datetime.strptime(data['start'], '%Y-%m-%dT%H:%M:%S%z')
                current_time = datetime.now(start_time.tzinfo)
                time_until_start = start_time - current_time

                if time_until_start.total_seconds() > 0:
                    # Convert to Unix epoch time
                    epoch_time = int(start_time.timestamp())

                    # Convert to human-readable format
                    days = time_until_start.days
                    hours, remainder = divmod(time_until_start.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)

                    # Send the response
                    await message.channel.send(
                        f"Time until the event '{data['title']}' starts:\n"
                        f"- Epoch Time: {epoch_time}\n"
                        f"- Human-Readable: {days} days, {hours} hours, {minutes} minutes"
                    )
                else:
                    await message.channel.send(f"The event '{data['title']}' has already started.")
        except Exception as e:
            await message.channel.send(f"Please provide a valid event ID. An error occurred")


    elif message.content.startswith('!join_ctf'):
        try:
            ctf_name = ' '.join(message.content.split()[1:])
            if not ctf_name:
                await message.channel.send("Usage: !join_ctf <ctf_name>")
                return

            if ctf_name not in custom_ctfs:
                await message.channel.send(f"CTF '{ctf_name}' does not exist.")
            else:
                # Assign the CTF role to the user
                guild = message.guild
                role = discord.utils.get(guild.roles, name=f"CTF: {ctf_name}")
                if role:
                    await assign_ctf_role(message.author, role)
                    await message.channel.send(f"You have joined CTF '{ctf_name}'. Role '{role.name}' has been assigned.")
                else:
                    await message.channel.send(f"Role for CTF '{ctf_name}' not found.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!upcoming'):
        try:
            limit = int(message.content.split()[1]) if len(message.content.split()) > 1 else 5
            data = fetch_upcoming_events(limit)
            if not data:
                await message.channel.send("No upcoming events received from CTFTime")
            else:
                embed = discord.Embed(title="Upcoming CTF Events", color=0x00ff00)
                for event in data:
                    start_time = datetime.strptime(event['start'], '%Y-%m-%dT%H:%M:%S%z')
                    finish_time = datetime.strptime(event['finish'], '%Y-%m-%dT%H:%M:%S%z')
                    embed.add_field(
                        name=event['title'],
                        value=f"ID: {event['id']}\nStart: {start_time}\nFinish: {finish_time}\nURL: {event['url']}",
                        inline=False
                    )
                await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!add_challenge'):
        try:
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                await message.channel.send("Usage: !add_challenge <ctf_name> <challenge_name>")
                return

            ctf_name = parts[1]
            challenge_name = parts[2]

            if ctf_name not in custom_ctfs:
                await message.channel.send(f"CTF '{ctf_name}' does not exist.")
            else:
                if challenge_name in custom_ctfs[ctf_name]['challenges']:
                    await message.channel.send(f"The challenge '{challenge_name}' already exists in CTF '{ctf_name}'.")
                else:
                    custom_ctfs[ctf_name]['challenges'][challenge_name] = {
                        'user': None,
                        'solved': False,
                        'working_on': False
                    }
                    save_custom_ctfs()
                    await message.channel.send(f"The challenge '{challenge_name}' has been added to CTF '{ctf_name}'.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!allocate_challenge'):
        try:
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                await message.channel.send("Usage: !allocate_challenge <ctf_name> <challenge_name>")
                return

            ctf_name = parts[1]
            challenge_name = parts[2]

            if ctf_name not in custom_ctfs:
                await message.channel.send(f"CTF '{ctf_name}' does not exist.")
            else:
                # If the challenge doesn't exist, add it to the CTF
                if challenge_name not in custom_ctfs[ctf_name]['challenges']:
                    custom_ctfs[ctf_name]['challenges'][challenge_name] = {
                        'user': None,
                        'solved': False,
                        'working_on': False
                    }
                    save_custom_ctfs()
                    await message.channel.send(f"The challenge '{challenge_name}' has been added to CTF '{ctf_name}'.")

                # Allocate the challenge to the user
                challenge = custom_ctfs[ctf_name]['challenges'][challenge_name]
                if challenge['user']:
                    await message.channel.send(f"The challenge '{challenge_name}' is already allocated to {challenge['user']}.")
                else:
                    challenge['user'] = message.author.name
                    challenge['working_on'] = True
                    save_custom_ctfs()

                    # Assign the CTF role to the user
                    guild = message.guild
                    role = discord.utils.get(guild.roles, name=f"CTF: {ctf_name}")
                    if role:
                        await assign_ctf_role(message.author, role)
                    else:
                        await message.channel.send(f"Role for CTF '{ctf_name}' not found.")

                    await message.channel.send(f"The challenge '{challenge_name}' in CTF '{ctf_name}' has been allocated to {message.author.name}.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!solve_challenge'):
        try:
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                await message.channel.send("Usage: !solve_challenge <ctf_name> <challenge_name>")
                return

            ctf_name = parts[1]
            challenge_name = parts[2]

            if ctf_name not in custom_ctfs:
                await message.channel.send(f"CTF '{ctf_name}' does not exist.")
            else:
                if challenge_name not in custom_ctfs[ctf_name]['challenges']:
                    await message.channel.send(f"The challenge '{challenge_name}' does not exist in CTF '{ctf_name}'.")
                else:
                    challenge = custom_ctfs[ctf_name]['challenges'][challenge_name]
                    if challenge['user'] == message.author.name:
                        challenge['solved'] = True
                        challenge['working_on'] = False
                        save_custom_ctfs()
                        await message.channel.send(f"The challenge '{challenge_name}' in CTF '{ctf_name}' has been marked as solved by {message.author.name}.")
                    else:
                        await message.channel.send(f"The challenge '{challenge_name}' is allocated to {challenge['user']}, not you.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!list_challenges'):
        try:
            ctf_name = ' '.join(message.content.split()[1:])
            if not ctf_name:
                await message.channel.send("Usage: !list_challenges <ctf_name>")
                return

            if ctf_name not in custom_ctfs:
                await message.channel.send(f"CTF '{ctf_name}' does not exist.")
            else:
                challenges = custom_ctfs[ctf_name]['challenges']
                if not challenges:
                    await message.channel.send(f"No challenges have been added to CTF '{ctf_name}' yet.")
                else:
                    # Split challenges into pages (25 challenges per page)
                    challenges_list = list(challenges.items())
                    pages = [challenges_list[i:i + 25] for i in range(0, len(challenges_list), 25)]

                    for page_num, page in enumerate(pages, start=1):
                        embed = discord.Embed(title=f"Challenges for CTF '{ctf_name}' (Page {page_num}/{len(pages)})", color=0x00ff00)
                        for challenge_name, details in page:
                            status = "Solved" if details['solved'] else "Unsolved"
                            working_on = f"Working on it: {details['user']}" if details['working_on'] else "Not being worked on"
                            solved_by = f"Solved by: {details['user']}" if details['solved'] else "Not solved yet"
                            embed.add_field(
                                name=challenge_name,
                                value=f"Status: {status}\n{working_on}\n{solved_by}",
                                inline=False
                            )
                        await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!show_ctf'):
        try:
            ctf_name = ' '.join(message.content.split()[1:])
            if not ctf_name:
                await message.channel.send("Usage: !show_ctf <ctf_name>")
                return

            if ctf_name not in custom_ctfs:
                await message.channel.send(f"CTF '{ctf_name}' does not exist.")
            else:
                ctf = custom_ctfs[ctf_name]
                challenges = ctf['challenges']

                # Create an embed to display CTF details
                embed = discord.Embed(title=f"CTF: {ctf_name}", color=0x00ff00)

                # Add challenges and their solve status
                if not challenges:
                    embed.add_field(name="Challenges", value="No challenges have been added to this CTF yet.", inline=False)
                else:
                    solved_challenges = []
                    unsolved_challenges = []

                    for challenge_name, details in challenges.items():
                        status = "Solved" if details['solved'] else "Unsolved"
                        working_on = f"Working on it: {details['user']}" if details['working_on'] else "Not being worked on"
                        solved_by = f"Solved by: {details['user']}" if details['solved'] else "Not solved yet"
                        challenge_info = f"Status: {status}\n{working_on}\n{solved_by}"

                        if details['solved']:
                            solved_challenges.append(f"**{challenge_name}**\n{challenge_info}")
                        else:
                            unsolved_challenges.append(f"**{challenge_name}**\n{challenge_info}")

                    if solved_challenges:
                        embed.add_field(name="Solved Challenges", value="\n\n".join(solved_challenges), inline=False)
                    if unsolved_challenges:
                        embed.add_field(name="Unsolved Challenges", value="\n\n".join(unsolved_challenges), inline=False)

                await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!delete_challenge'):
        try:
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                await message.channel.send("Usage: !delete_challenge <ctf_name> <challenge_name>")
                return

            ctf_name = parts[1]
            challenge_name = parts[2]

            if ctf_name not in custom_ctfs:
                await message.channel.send(f"CTF '{ctf_name}' does not exist.")
            else:
                if challenge_name not in custom_ctfs[ctf_name]['challenges']:
                    await message.channel.send(f"The challenge '{challenge_name}' does not exist in CTF '{ctf_name}'.")
                else:
                    challenge = custom_ctfs[ctf_name]['challenges'][challenge_name]
                    # Check if the user is the one who allocated the challenge
                    if challenge['user'] == message.author.name:
                        del custom_ctfs[ctf_name]['challenges'][challenge_name]
                        save_custom_ctfs()
                        await message.channel.send(f"The challenge '{challenge_name}' has been deleted from CTF '{ctf_name}'.")
                    else:
                        await message.channel.send(f"You cannot delete the challenge '{challenge_name}' because it is allocated to {challenge['user']}.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!time_left'):
        try:
            event_id = int(message.content.split()[1])
            data = fetch_specific_event(event_id)
            if not data:
                await message.channel.send("No data received from CTFTime")
            else:
                finish_time = datetime.strptime(data['finish'], '%Y-%m-%dT%H:%M:%S%z')
                current_time = datetime.now(finish_time.tzinfo)
                time_left = finish_time - current_time
                if time_left.total_seconds() > 0:
                    await message.channel.send(f"Time left for the event '{data['title']}': {time_left}")
                else:
                    await message.channel.send(f"The event '{data['title']}' has already ended.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!list_ctfs'):
        try:
            limit = int(message.content.split()[1]) if len(message.content.split()) > 1 else 5
            data = fetch_upcoming_events(limit)
            if not data:
                await message.channel.send("No upcoming events received from CTFTime")
            else:
                embeds = []
                embed = discord.Embed(title="Upcoming CTF Events", color=0x00ff00)
                for i, event in enumerate(data):
                    if i > 0 and i % 25 == 0:
                        embeds.append(embed)
                        embed = discord.Embed(title="Upcoming CTF Events (cont.)", color=0x00ff00)
                    embed.add_field(name=event['title'], value=f"ID: {event['id']}\nStart: {event['start']}\nFinish: {event['finish']}\nURL: {event['url']}", inline=False)
                embeds.append(embed)
                for embed in embeds:
                    await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!current_ctfs'):
        try:
            limit = int(message.content.split()[1]) if len(message.content.split()) > 1 else 5
            data = fetch_upcoming_events(limit)
            if not data:
                await message.channel.send("No upcoming events received from CTFTime")
            else:
                current_time = datetime.now()
                embeds = []
                embed = discord.Embed(title="Currently Ongoing CTF Events", color=0x00ff00)
                ongoing_events = [event for event in data if datetime.strptime(event['start'], '%Y-%m-%dT%H:%M:%S%z') <= current_time <= datetime.strptime(event['finish'], '%Y-%m-%dT%H:%M:%S%z')]
                if ongoing_events:
                    for i, event in enumerate(ongoing_events):
                        if i > 0 and i % 25 == 0:
                            embeds.append(embed)
                            embed = discord.Embed(title="Currently Ongoing CTF Events (cont.)", color=0x00ff00)
                        embed.add_field(name=event['title'], value=f"ID: {event['id']}\nStart: {event['start']}\nFinish: {event['finish']}\nURL: {event['url']}", inline=False)
                else:
                    embed.add_field(name="No ongoing events", value="There are no CTF events currently ongoing.", inline=False)
                embeds.append(embed)
                for embed in embeds:
                    await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    elif message.content.startswith('!leave_ctf'):
        try:
            ctf_name = ' '.join(message.content.split()[1:])
            if not ctf_name:
                await message.channel.send("Usage: !leave_ctf <ctf_name>")
                return

            if ctf_name not in custom_ctfs:
                await message.channel.send(f"CTF '{ctf_name}' does not exist.")
            else:
                # Remove the CTF role from the user
                guild = message.guild
                role = discord.utils.get(guild.roles, name=f"CTF: {ctf_name}")
                if role:
                    await remove_ctf_role(message.author, role)
                    await message.channel.send(f"You have left CTF '{ctf_name}'. Role '{role.name}' has been removed.")
                else:
                    await message.channel.send(f"Role for CTF '{ctf_name}' not found.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

# Run the bot the safe way
client.run(os.getenv('DISCORD_BOT_TOKEN'))
