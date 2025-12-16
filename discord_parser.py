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


async def parse_teams(season: dict, category: discord.CategoryChannel) -> dict:
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
    season_with_teams = copy.deepcopy(season)

    invalid_count = 0
    for channel in category.text_channels:
        if "spelartrupper" in channel.name:
            channel_info = channel.name.split("-")
            div = channel_info[2]
            if div == "dl":
                division = "Dunderligan"
            else:
                division = "Division " + channel_info[2][0]

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

                groups: dict = season_with_teams["divisions"][division]["groups"]
                teams = []
                done_one_pass = False
                while True:
                    for group_name, value in groups.items():
                        if team_name in value["teams"]:
                            group_name = group_name
                            break
                        elif team_name.lower() in list(
                            map(lambda s: s.lower(), value["teams"].keys())
                        ):
                            for team in value["teams"].keys():
                                if team_name.lower() == team.lower():
                                    team_name = team
                                    break
                            break
                        elif not done_one_pass:
                            teams = teams + list(value["teams"].keys())
                    else:
                        done_one_pass = True
                        print(f"Couldn't find roster '{team_name}' among teams {teams}")
                        team_name = input("Name to instead look for=")
                        continue
                    break

                if not group_name:
                    team = copy.deepcopy(TEAM)
                team = groups[group_name]["teams"][team_name]

                for roster_player in roster:
                    player = list(
                        filter(
                            lambda p: p != "-" and p != "," and p != "",
                            map(
                                strip_emojis,
                                split_on_multiple(roster_player, " ", ",", "-"),
                            ),
                        )
                    )

                    member = copy.deepcopy(PLAYER)
                    current_step = 0

                    while True:
                        if not player:
                            break

                        if not is_valid(player[0]) or (
                            current_step >= 1 and len(player[0]) == 1
                        ):
                            player = player[1:]

                        elif STEPS[current_step] == "RANK":
                            rank = get_rank(player)

                            if rank[0]:
                                member["sr"] = rank[1][0]
                                if member["sr"] is not None:
                                    season_with_teams["legacy_ranks"] = True
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
                            ROLES: list = [
                                "dps",
                                "damage",
                                "support",
                                "coach",
                                "tank",
                                "flex"
                            ]
                            if member["battletag"].lower() in ROLES:
                                member["battletag"] = f"InvalidNumber{invalid_count}#99999999"
                                invalid_count += 1

                            player = player[1:]
                            current_step += 1

                        elif STEPS[current_step] == "CAPTAIN":
                            if player:
                                if "c" in player[0].lower():
                                    member["is_captain"] = True
                            break
                    team["players"].append(member)
    return season_with_teams


async def parse_groups(category: discord.CategoryChannel) -> dict:
    GROUP_NAMES = ["Grupp A", "Grupp B", "Grupp C", "Grupp D"]

    SEASON: dict = {
        "season": 0,
        "start_date": None,
        "legacy_ranks": False,
        "divisions": {},
    }
    DIVISION: dict = {"groups": {}}
    GROUP: dict = {"teams": {}, "matches": []}
    TEAM: dict = {"players": []}
    MATCH: dict = {
        "date": None,
        "rosterA": "",
        "rosterB": "",
        "teamAScore": 0,
        "teamBScore": 0,
        "draws": 0,
    }

    season: dict = copy.deepcopy(SEASON)
    start_date = None
    for channel in category.text_channels:
        if "spelschema" in channel.name:
            channel_info = channel.name.split("-")
            season["season"] = int(channel_info[-1][1])
            div = channel_info[1]
            if div == "dl":
                division: str = "Dunderligan"
            else:
                division: str = "Division " + channel_info[1][3]

            if not season.get("divisions").get(division):
                season["divisions"][division] = copy.deepcopy(DIVISION)

            message_count = 0
            async for message in channel.history(limit=4):
                if season.get("start_date") is None:
                    start_date = message.created_at.replace(
                        hour=19, minute=0, second=0, microsecond=0
                    )
                    season["start_date"] = start_date.isoformat()

                content = message.content
                rows = [row for row in content.split("\n")]

                rounds = []
                current_round = 0
                current_group = 0
                ready = False
                checked_teams = 0
                multiple_groups = False
                for row in rows:
                    line = strip_punc(row)
                    if line.lower().startswith("omgång") or line.lower().startswith(
                        "division"
                    ):
                        rounds.append([])
                        ready = True
                        if not multiple_groups:
                            current_round += 1
                        current_group = 0
                    elif current_round == 0:
                        continue
                    elif ready and (line.isspace() or line == "") and checked_teams >= 0:
                        current_group += 1
                        multiple_groups = True
                    elif line != "" and not line.lower().startswith("senast"):
                        line = split_on_multiple(line, "vs.", " - ", " – ")
                        print(line)

                        rosterA: str = strip_punc(line[0])
                        rosterB: str = strip_punc(line[1])
                        teamAScore: int = 0
                        teamBScore: int = 0
                        draws: int = 0

                        if "..." in line[1] or "…" in line[1]:
                            rest = split_on_multiple(line[1], "...", "…")
                            rosterB = strip_punc(rest[0])
                            score = list(map(strip_punc, rest[1].split("-")))
                            teamAScore = int(score[0][0])
                            teamBScore = int(score[1][0])
                            draws = 3 - (teamAScore + teamBScore)

                        match = copy.deepcopy(MATCH)
                        if start_date:
                            match["date"] = (
                                start_date
                                + datetime.timedelta(days=7 * (current_round - 1))
                            ).isoformat()
                        match["rosterA"] = rosterA
                        match["rosterB"] = rosterB
                        match["teamAScore"] = teamAScore
                        match["teamBScore"] = teamBScore
                        match["draws"] = draws

                        group_number = max(current_group, message_count)
                        if not season["divisions"][division]["groups"].get(
                            GROUP_NAMES[group_number]
                        ):
                            season["divisions"][division]["groups"][
                                GROUP_NAMES[group_number]
                            ] = copy.deepcopy(GROUP)

                        group = season["divisions"][division]["groups"][
                            GROUP_NAMES[group_number]
                        ]
                        group["matches"].append(match)
                        if rosterA not in group["teams"]:
                            group["teams"][rosterA] = copy.deepcopy(TEAM)
                        if rosterB not in group["teams"]:
                            group["teams"][rosterB] = copy.deepcopy(TEAM)

                message_count += 1
    return season


def split_on_multiple(text: str, *separators):
    modified = text
    for s in separators:
        if isinstance(modified, str):
            modified = modified.split(s)
        else:
            modified = list(map(lambda p: p.split(s), modified))
            merged = []
            for parts in modified:
                merged = merged + parts
            modified = merged
    return modified


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
    if rank.lower() == "n/a" or rank.lower() == "unranked":
        if str(parts[1]).lower() == "n/a" or str(parts[1]).lower() == "unranked":
            return (False, [None, None])
        return (False, [None])

    if "." in rank or "k" in rank:
        try:
            sr = int(float(rank.strip("k ,-?").replace(",", ".")) * 1000)
        except ValueError:
            sr = None
        return (True, [sr])
    elif rank in RANKS or rank in RANK_ALIASES:
        if rank not in RANKS:
            rank = RANK_ALIASES[rank]
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
    return text.strip(" ,.-()*|")


def strip_emojis(text: str) -> str:
    """
    Strips emojis on format ":name:" from front
    and end of string.
    """
    mod_text = text
    if mod_text.startswith(":") and mod_text.count(":") >= 2:
        mod_text = mod_text[mod_text.index(":", 1) + 1 :].lstrip()
    if mod_text.endswith(":") and mod_text.count(":") >= 2:
        mod_text = mod_text[: mod_text.index(":")].rstrip()
    return mod_text


def is_valid(text: str) -> bool:
    """
    Returns whether text contains valid information, or
    is just wrongly placed punctuation.
    """
    return (len(text) > 1 or text in "12345") and not (
        text.startswith(":") and text.endswith(":")
    )


@tree.command(
    name="parse_season",
    description="Parses category for groups, matches, and rosters.",
    guild=discord.Object(id=server_id),
)
@app_commands.checks.has_role(admin_role_id)
@app_commands.describe(
    category="Category to look for 'spelartrupper' and 'spelschema' in."
)
async def parse_season(
    interaction: discord.Interaction, category: discord.CategoryChannel
):
    season_data = await parse_groups(category)
    season_data = await parse_teams(season_data, category)
    season: int = season_data["season"]

    with open(f"parsed_data/season_{season}.json", "w") as file:
        json.dump(season_data, file, indent=1)

    await interaction.channel.send(
        f"Got data from {season}:",
        file=discord.File(f"parsed_data/season_{season}.json"),
    )
    pass


client.run(token)
