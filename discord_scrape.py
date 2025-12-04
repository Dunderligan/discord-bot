import discord
import os
import json
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
        "rank": "",
        "tier": -1,
        "sr": -1,
        "role": "",
        "is_captain": False,
    }

    STEPS: list = ["RANK", "ROLE", "BATTLETAG", "CAPTAIN"]
    teams: dict = SEASON.copy()

    for channel in category.text_channels:
        if "spelartrupper" in channel.name:
            channel_info = channel.name.split("-")

            season: int = int(channel_info[3][1])
            if teams.get("season") == 0:
                teams["season"] = season

            division: int = int(channel_info[2])
            if not teams.get("divisions").get(division):
                teams["divisions"][division] = DIVISION.copy()

            async for message in channel.history(limit=1):
                content = message.content
                roster = [row for row in content.split("\n")]

                team_name = " ".join(
                    [
                        a.capitalize()
                        for a in roster[0]
                        .replace("*", "")
                        .split("AVG")[0]
                        .rstrip()
                        .split()
                    ]
                )
                if "division" in team_name.lower():
                    team_name = team_name[
                        : team_name.lower().index("division") - 2
                    ].rstrip()
                if not teams.get("divisions").get(division).get(team_name):
                    teams["divisions"][division][team_name] = TEAM.copy()

                for player in roster[1:]:
                    player_copy = list(
                        filter(lambda p: p != "-" and p != ",", player.split())
                    )
                    member = PLAYER.copy()
                    current_step = 0

                    while player_copy:
                        if not is_valid(player_copy[0]):
                            player_copy = player_copy[1:]

                        elif STEPS[current_step] == "RANK":
                            if len(player) >= 5:
                                rank = get_rank(player[0:2])
                            else:
                                rank = get_rank(player[0:1])

                            if rank[0]:
                                member["sr"] = rank[1][0]
                                player_copy = player_copy[1:]
                            else:
                                member["rank"] = rank[1][0]
                                member["tier"] = rank[1][1]
                                player_copy = player_copy[2:]
                            current_step += 1

                        elif STEPS[current_step] == "ROLE":
                            member["role"] = player[0].lower().replace("dps", "damage")
                            player_copy = player_copy[1:]
                            current_step += 1

                        elif STEPS[current_step] == "BATTLETAG":
                            member["battletag"] = player[0]
                            player_copy = player_copy[1:]
                            current_step += 1

                        elif STEPS[current_step] == "CAPTAIN":
                            if player:
                                if "c" in player[0].lower():
                                    member["is_captain"] = True
                            break
                    
                    teams["divisions"][division][team_name]["players"].append(member)

            await interaction.channel.send(f"rosters: {teams}")

            """
                    if player[2].lower() in RANKS:
                        member["battletag"] = player[6]
                        member["rank"] = player[2].lower()
                        member["tier"] = int(player[3])
                        member["role"] = player[4].lower().replace("dps", "damage")
                        if len(player) >= 8:
                            member["is_captain"] = "c" in player[7].lower()
                        else:
                            member["is_captain"] = False
                    else:
                        member["battletag"] = player[3]
                        member["sr"] = int(float(player[1].replace("k", "").strip(" .,-")) * 1000)
                        member["role"] = player[2].lower().replace("dps", "damage")
                        if len(player) >= 5:
                            member["is_captain"] = "c" in player[4].lower()
                        else:
                            member["is_captain"] = False

                    await interaction.channel.send(f"member: {member}")
                    """

            await interaction.channel.send(
                f"Got rosters from season {season}, division {division}"
            )

            """
            **Chef's Kiss**  *AVG: <:silver:631440339051479040> Silver 3*
            - <:bronze:631440315164917760> Bronze 5, Tank - RANDOM501st#2386 **C** ✅ 
            - <:plat:631440410874740746> Platinum 4, Tank - ŜŊǕŜMǕMȐƗƘƐŊ ✅ 
            - <:bronze:631440315164917760> Bronze 4, DPS - Zamzamzoot ✅ 
            - <:silver:631440339051479040> Silver 1, DPS - Getsaken ✅ 
            - <:silver:631440339051479040> Silver 3, Support - Vasterasgurkan ✅ 
            - <:silver:631440339051479040> Silver 2, Support - Finsklax#2472 **C** ✅ 

            - 🧠 Coach - Starkeadrian
            - 🧠 Coach - Koloma
            """


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

    if len(parts) == 1:
        try:
            sr = int(float(str(parts[0]).strip("k .,-").replace(",", ".")) * 1000)
        except ValueError:
            sr = 0
        return (True, [sr])
    elif len(parts) == 2:
        try:
            rank = str(parts[0]).lower()
            if rank not in RANKS:
                if rank in RANK_ALIASES:
                    rank = RANK_ALIASES[rank]
                else:
                    raise ValueError
            tier = int(strip_punc(parts[1]))
        except ValueError:
            rank = None
            tier = None
        return (False, [rank, tier])
    return (False, [None, None])


def strip_punc(text: str) -> str:
    return text.strip(" ,.-()")


def is_valid(text: str) -> bool:
    return (len(text) > 1 or text not in ":(),.-") and not (text.startswith(":") and text.endswith(":"))


client.run(token)
