import discord
import os
import json
import copy
from dotenv import load_dotenv
from discord import app_commands

load_dotenv()
token = os.getenv("TOKEN")
server_id: int = int(os.getenv("SERVER_ID"))
admin_role_id: int = int(os.getenv("ADMIN_ID"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await tree.sync(guild=discord.Object(id=server_id))


@tree.command(
    name="scrape_teams",
    description="Reads through roster messages and saves teams.",
    guild=discord.Object(id=server_id),
)
@app_commands.checks.has_role(admin_role_id)
@app_commands.describe(category="Category to check")
async def scrape_teams(
    interaction: discord.Interaction, category: discord.CategoryChannel
) -> str:
    """teams: dict = {
        "season": 0,
        "divisions": {
            "1": {
                "T": {
                    "players": [
                        {
                            "battletag": "B",
                            "rank": 0,
                            "tier": 0,
                            "sr": 0000,
                            "role": "dps",
                            "is_captain": False,
                        }
                    ],
                }
            },
            "2": {},
        },
    }"""

    await interaction.response.send_message("Scraping teams...")

    SEASON: dict = {"season": 0, "divisions": {}}
    DIVISION: dict = {}
    TEAM: dict = {"players": []}
    PLAYER: dict = {
        "battletag": "",
        "rank": None,
        "tier": None,
        "sr": None,
        "role": "",
        "is_captain": False,
    }

    ROLES: list = ["tank", "damage", "support", "flex", "coach"]

    STEPS: list = ["RANK", "ROLE", "BATTLETAG", "CAPTAIN"]
    teams: dict = copy.deepcopy(SEASON)

    for channel in category.text_channels:
        if "spelartrupper" in channel.name:
            channel_info = channel.name.split("-")

            season: int = int(channel_info[3][1])
            if teams.get("season") == 0:
                teams["season"] = season

            division: int = int(channel_info[2])
            if not teams.get("divisions").get(division):
                teams["divisions"][division] = copy.deepcopy(DIVISION)

            async for message in channel.history(limit=4):
                content = message.content
                roster = [row for row in content.split("\n")]

                if roster[0].startswith("-"):
                    team_name = "UNKNOWN"  # todo ASK FOR INPUT FROM USER
                else:
                    team_name = " ".join(
                        [
                            a.capitalize()
                            for a in roster[0]
                            .replace("*", "")
                            .lower()
                            .split("avg")[0]
                            .strip()
                            .split()
                        ]
                    )
                    
                    if "division" in team_name.lower():
                        team_name = team_name[
                            : team_name.lower().index("division") - 2
                        ].rstrip()
                    roster = roster[1:]

                if not teams.get("divisions").get(division).get(team_name):
                    teams["divisions"][division][team_name] = copy.deepcopy(TEAM)

                for roster_player in roster:
                    player = list(
                        filter(lambda p: p != "-" and p != ",", strip_emojis(roster_player).split())
                    )
                    member = copy.deepcopy(PLAYER)
                    current_step = 0

                    while True:
                        if not player:
                            break
                        print(player)

                        if not is_valid(player[0]):
                            print("invalid start")
                            player = player[1:]

                        elif STEPS[current_step] == "RANK":
                            rank = get_rank(player)

                            if rank[0]:
                                member["sr"] = rank[1][0]
                            else:
                                if len(rank[1]) == 2:
                                    member["rank"] = rank[1][0]
                                    member["tier"] = rank[1][1]
                            player = player[len(rank[1]) :]
                            current_step += 1

                        elif STEPS[current_step] == "ROLE":
                            role = player[0].lower().replace("dps", "damage")
                            if role in ROLES:
                                member["role"] = role
                            else:
                                member["role"] = "flex"
                            player = player[1:]
                            current_step += 1

                        elif STEPS[current_step] == "BATTLETAG":
                            member["battletag"] = player[0]
                            player = player[1:]
                            current_step += 1

                        elif STEPS[current_step] == "CAPTAIN":
                            if player:
                                if "c" in player[0].lower():
                                    member["is_captain"] = True
                            break

                    teams["divisions"][division][team_name]["players"].append(member)

            with open("output.json", "w") as file:
                json.dump(teams, file)
            # await interaction.channel.send(f"rosters: {teams}")

            await interaction.channel.send(
                f"Got rosters from season {season}, division {division}"
            )


def get_rank(parts: list) -> tuple[bool, list]:
    """
    Takes a list of 1 or 2 indices.
    Extracts (rank, tier) or (sr) and returns a tuple
    with a bool for if it is legacy rank (sr) or not,
    and a list with either 1 or 2 parts of a rank.
    """
    RANKS: list = [
        "bronze",
        "silver",
        "gold",
        "platinum",
        "diamond",
        "master",
        "grandmaster",
        "champion",
    ]
    RANK_ALIASES: dict = {"guld": "gold", "gm": "grandmaster", "brons": "bronze"}

    rank = strip_punc(str(parts[0]).lower())
    if "." in rank or "k" in rank:
        try:
            sr = int(float(rank.strip("k ,-").replace(",", ".")) * 1000)
        except ValueError:
            sr = None
        return (True, [sr])
    elif rank in RANKS or rank in RANK_ALIASES:
        if rank not in RANKS:
            rank = RANK_ALIASES
        try:
            tier = int(strip_punc(parts[1]))
        except ValueError:
            rank = None
            tier = None
        return (False, [rank, tier])
    else:
        return (False, [None])


def strip_punc(text: str) -> str:
    return text.strip(" ,.-()")


def strip_emojis(text: str) -> str:
    mod_text = text
    if text.startswith(":"):
        mod_text = mod_text[mod_text.index(":", 1)+1:]
    if text.endswith(":"):
        mod_text = mod_text[:mod_text.index(":")]
    print(f"Removed emojis. Old: {text}, New: {mod_text}")
    return mod_text


def is_valid(text: str) -> bool:
    return (len(text) > 1 or text in "12345") and not (
        text.startswith(":") and text.endswith(":")
    )


client.run(token)
