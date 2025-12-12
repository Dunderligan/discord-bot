import discord
import os
import json
import datetime
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
    name="parse_teams",
    description="Reads through roster messages and parses teams into a json-file.",
    guild=discord.Object(id=server_id),
)
@app_commands.checks.has_role(admin_role_id)
@app_commands.describe(category="Category to check")
async def parse_teams(
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

            season: int = int(channel_info[-1][1])

            if teams.get("season") == 0:
                teams["season"] = season

            division = "Division " + channel_info[2]
            if not teams.get("divisions").get(division):
                teams["divisions"][division] = copy.deepcopy(DIVISION)

            async for message in channel.history(limit=16):
                content = message.content
                roster = [row for row in content.split("\n")]

                if roster[0].startswith("-"):
                    print(f"SKIPPED TEAM: {roster}\nManually input team on website")
                    continue
                else:
                    team_name = strip_emojis(
                        " ".join(
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
                        filter(
                            lambda p: p != "-" and p != ",",
                            strip_emojis(roster_player).split(),
                        )
                    )
                    member = copy.deepcopy(PLAYER)
                    current_step = 0

                    while True:
                        if not player:
                            break

                        if not is_valid(player[0]):
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
                            member["battletag"] = strip_punc(player[0])
                            player = player[1:]
                            current_step += 1

                        elif STEPS[current_step] == "CAPTAIN":
                            if player:
                                if "c" in player[0].lower():
                                    member["is_captain"] = True
                            break

                    teams["divisions"][division][team_name]["players"].append(member)

    with open(f"parsed_data/season_{season}.json", "w") as file:
        json.dump(teams, file, indent=1)

    await interaction.channel.send(
        f"Got rosters from season {season}:",
        file=discord.File(f"parsed_data/season_{season}.json"),
    )


@tree.command(
    name="parse_groups",
    description="Reads through schedule to find groups and matches, outputting into a json-file.",
    guild=discord.Object(id=server_id),
)
@app_commands.checks.has_role(admin_role_id)
@app_commands.describe(category="Category to check")
async def parse_groups(
    interaction: discord.Interaction, category: discord.CategoryChannel
) -> str:
    """
    "season": 0,
    "start_date": ?,
    "divisions": {
        "1": {
            "groups": {
                "Grupp A": {
                    "teams": [],
                    "matches": [
                        {
                        "date": None
                        "rosterA": "Missarna",
                        "rosterB": "Kaninerna",
                        "teamAScore": 3,
                        "teamBScore": 0,
                        "draws": 0
                        }
                    ]
                }
            }
        }
    }
    """

    # GROUP NAMES GO FROM A -> B -> C -> ...
    # MULTIPLE MESSAGES IN A CHANNEL MEANS ONE GROUP PER MESSAGE
    # SPLIT ON "OMGÅNG", CAN GET DATE FROM THERE

    await interaction.response.send_message("Parsing groups...")

    SEASON: dict = {"season": 0, "start_date": None, "divisions": {}}
    DIVISION: dict = {"groups": {}}
    GROUP: dict = {"teams": [], "matches": []}
    MATCH: dict = {
        "date": None,
        "rosterA": "",
        "rosterB": "",
        "teamAScore": 0,
        "teamBScore": 0,
        "draws": 0,
    }

    groups: dict = copy.deepcopy(SEASON)
    start_date = None
    for channel in category.text_channels:
        if "spelschema" in channel.name:
            channel_info = channel.name.split("-")

            season: int = int(channel_info[-1][1])
            division: str = ("Division " + channel_info[1][3])

            if groups.get("season") == 0:
                groups["season"] = season

            if not groups.get("divisions").get(division):
                groups["divisions"][division] = copy.deepcopy(DIVISION)

            
            async for message in channel.history(limit=4):
                if groups.get("start_date") is None:
                    start_date = message.created_at.replace(hour=20, minute=0, second=0, microsecond=0)
                    groups["start_date"] = start_date.isoformat()

                content = message.content
                rows = [row for row in content.split("\n")]

                group = copy.deepcopy(GROUP)

                rounds = []
                current_round = 0
                for row in rows:
                    line = strip_punc(row)
                    if line.lower().startswith("omgång"):
                        rounds.append([])
                        current_round += 1

                    elif line != "" and not line.lower().startswith("senast"):
                        line = line.split("vs.")

                        rosterA: str = strip_punc(line[0])
                        rosterB: str = strip_punc(line[1])
                        teamAScore: int = 0
                        teamBScore: int = 0
                        draws: int = 0

                        if "..." in line[1]:
                            rest = line[1].split("...")
                            rosterB = strip_punc(rest[0])

                            score = list(map(strip_punc, rest[1].split("-")))
                            teamAScore = int(score[0][0])
                            teamBScore = int(score[1][0])
                            draws = 3 - (teamAScore + teamBScore)

                        if rosterA not in group["teams"]:
                            group["teams"].append(rosterA)
                        if rosterB not in group["teams"]:
                            group["teams"].append(rosterB)

                        match = copy.deepcopy(MATCH)

                        if start_date:
                            match["date"] = (start_date + datetime.timedelta(days=7*(current_round - 1))).isoformat()
                        match["rosterA"] = rosterA
                        match["rosterB"] = rosterB
                        match["teamAScore"] = teamAScore
                        match["teamBScore"] = teamBScore
                        match["draws"] = draws

                        group["matches"].append(match)

                groups["divisions"][division]["groups"]["Grupp A"] = group

    with open(f"parsed_data/season_{season}_groups.json", "w") as file:
        json.dump(groups, file, indent=1)

    await interaction.channel.send(
        f"Got groups from season {season}:",
        file=discord.File(f"parsed_data/season_{season}_groups.json"),
    )


def get_rank(parts: list) -> tuple[bool, list]:
    """
    Takes a list and tries to find a rank in either format
    sr "X.Xk" or with tier "Rank X", returns rank and a bool
    set to whether it uses sr or not.
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
            sr = int(float(rank.strip("k ,-?").replace(",", ".")) * 1000)
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
    """
    Strips punctuation from text.
    """
    return text.strip(" ,.-()*")


def strip_emojis(text: str) -> str:
    """
    Strips emojis on format ":name:" from front
    and end of string.
    """
    mod_text = text
    if text.startswith(":"):
        mod_text = mod_text[mod_text.index(":", 1) + 1 :].lstrip()
    if text.endswith(":"):
        mod_text = mod_text[: mod_text.index(":")].rstrip()
    return mod_text


def is_valid(text: str) -> bool:
    """
    Returns whether text contains valid information, or
    is just wrongly placed punctuation.
    """
    return (
        (len(text) > 1 or text in "12345")
        and not (text.startswith(":") and text.endswith(":"))
        and text != "N/A"
    )


client.run(token)
