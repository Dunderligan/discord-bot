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
    season_with_teams = copy.deepcopy(season)

    for channel in category.text_channels:
        if "spelartrupper" in channel.name:
            channel_info = channel.name.split("-")
            if len(channel_info) == 3:
                if channel_info[1].lower() == "dunderligan" or channel_info[1].lower() == "dl":
                    division = "Dunderligan"
                else:
                    division = "Division " + channel_info[1][-1] 
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
                    if roster_player == "" or roster_player.isspace():
                        continue
                    player_tokens = get_player_tokens(roster_player)
                    member = copy.deepcopy(PLAYER)

                    if player_tokens["rank"] is not None:
                        rank = player_tokens["rank"]
                        if len(rank) == 2:
                            member["rank"] = rank[0]
                            member["tier"] = rank[1]
                        else:
                            member["sr"] = rank[0]
                            if rank[0] is not None:
                                season_with_teams["legacy_ranks"] = True
                            
                    if player_tokens["role"] is not None:
                        role = player_tokens["role"]
                        member["role"] = role

                    if player_tokens["battletag"] is not None:
                        tag = player_tokens["battletag"]
                        member["battletag"] = tag

                    if player_tokens["is_captain"] is not None:
                        member["is_captain"] = True

                    team["players"].append(member)
    return season_with_teams


def get_player_tokens(line: str) -> dict:
    """
    Takes a line from a roster.
    Returns a dictionary containing 'rank', 'role', 'battletag', and 'is_captain'
    """
    # RULES: # can only appear once, in battletag
    # order is rank -> role -> tag -> captain
    # rank can be on form '2.5k', '2,5k', '2000', 'Diamond 3', 'N/A', 'Unranked'
    def is_separator(index: int) -> bool:
        return line[index] in ": ,-"
    
    def index_next_separator(index: int) -> int:
        for k in range(len(line[index:])):
            if line[index+k] in ": ,-":
                return index + k

    RANKS = ["bronze", "silver", "gold", "platinum", "diamond", "master", "grandmaster", "champion"]
    RANKS_SPELLING = {"brons": "bronze", "guld": "gold", "gm": "grandmaster", "masters": "master", "plat": "platinum"}
    ROLES = ["support", "damage", "tank", "coach", "flex"]
    ROLES_SPELLING = {"suppprt": "support", "dps": "damage", "suport": "support"}
    tokens: dict[str, str] = {"rank": None, "role": None, "battletag": None, "is_captain": None}
    current_token = ""
    ignore_until = -1
    for i in range(len(line)):
        c = line[i]
        # print(c, current_token, i, ignore_until)
        if i <= ignore_until:
            continue
        elif c == "<" and line.count(">") > 0:
            ignore_until = line.index(">", i)
            continue
        elif c == ":" and line[i+1:].count(":") > 0:
            #found emoji, ignore until end
            ignore_until = line.index(":", i+1)
            continue
        elif c not in ": ,-*?~_":
            current_token += c
        if current_token.lower() in ["n/a", "unranked", "undranked"]:
            if tokens.get("rank") is None:
                tokens["rank"] = [None]
            current_token = ""
            ignore_until = index_next_separator(i)

        if tokens.get("rank") is None:
            if "🧠" in current_token.lower():
                tokens["rank"] = [None]
                current_token = ""
            elif current_token.lower().endswith("k") and is_separator(i + 1):
                sr = int(float(current_token[:-1]) * 1000)
                if sr >= 10000:
                    sr = sr // 10
                tokens["rank"] = [sr]
                current_token = ""
                ignore_until = index_next_separator(i)
            elif current_token.lower() in RANKS or current_token.lower() in RANKS_SPELLING:
                rank = current_token.lower()
                if rank in RANKS_SPELLING:
                    rank = RANKS_SPELLING[rank]
                for k in range(len(line[i+1:])):
                    if line[k+i] in "12345?":
                        tier = line[k+i]
                        if tier == "?":
                            tier = "1"
                        tokens["rank"] = [rank, int(tier)]
                        current_token = ""
                        ignore_until = index_next_separator(k+i)
                        break
            elif len(current_token) == 4:
                for k in current_token:
                    if k not in "0123456789":
                        break
                else:
                    tokens["rank"] = [int(current_token)]
                    current_token = ""
                    ignore_until = index_next_separator(i)
        elif tokens.get("role") is None:
            if current_token and current_token[0] in "0123456789":
                current_token = current_token[1:]
            if current_token.lower() in ROLES or current_token.lower() in ROLES_SPELLING:
                role = current_token.lower()
                if role in ROLES_SPELLING:
                    role = ROLES_SPELLING[role]
                tokens["role"] = role
                current_token = ""
                ignore_until = index_next_separator(i)
        elif tokens.get("battletag") is None:
            if not current_token.isspace() and not current_token == "" and (len(line) == i+1 or is_separator(i + 1)):
                tokens["battletag"] = current_token
                current_token = ""
                ignore_until = index_next_separator(i)
        elif tokens.get("is_captain") is None:
            if current_token.lower() == "c":
                tokens["is_captain"] = True
                break

    if tokens.get("battletag") is None:
        raise Exception(f"Couldn't get battletag from {line}")
    elif tokens["battletag"] in ROLES or tokens["battletag"] in RANKS:
        raise Exception(f"Got invalid battletag '{tokens.get("battletag")}' from {line}")
    elif len(tokens["rank"]) == 2 and tokens["rank"][1] > 5:
        raise Exception(f"Got invalid rank '{tokens["rank"]} from {line}")
    
    return tokens


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
            channel_info = split_on_multiple(channel.name, "-", "_")
            season["season"] = int(category.name.split()[-1])
            if len(channel_info) == 3:
                if channel_info[1].lower() == "dunderligan" or channel_info[1].lower() == "dl":
                    division = "Dunderligan"
                else:
                    division = "Division " + channel_info[1][-1] 
            else:
                division = "Division " + channel_info[2][0]

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
                added_teams_this_round = 0
                multiple_groups = False
                for row in rows:
                    line = strip_punc(row)
                    if line.lower().startswith("slutspel"):
                        break
                    elif line.lower().startswith("omgång") or line.lower().startswith(
                        "division") or line.lower().startswith("dunderligan"):
                        rounds.append([])
                        ready = True
                        if not multiple_groups:
                            current_round += 1
                        current_group = 0
                        added_teams_this_round = 0
                    elif current_round == 0:
                        continue
                    elif ready and (line.isspace() or line == "") and checked_teams >= 0 and added_teams_this_round > 0:
                        current_group += 1
                        multiple_groups = True
                    elif line.lower().startswith("senast") or line.lower().startswith("spelas "):
                        continue
                    elif line != "":
                        line = split_on_multiple(line.replace("||", ""), "vs.", " - ", " – ")

                        rosterA: str = strip_punc(line[0])
                        rosterB: str = strip_punc(line[1])
                        teamAScore: int = 0
                        teamBScore: int = 0
                        draws: int = 0

                        if "..." in line[1] or "…" in line[1]:
                            rest = split_on_multiple(line[1], "...", "…", "..")
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

                        group_number = max(current_group, 0) #message_count)
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

                        added_teams_this_round += 1

                message_count += 1
    return season



def test_tokens():
    tests = ["- :champion: Champion 5, DPS - Stenis#21529 C", 
             "- :plat: 2.6k, Flex - Androseli C", 
             "- :guld: 2.1k, Flex - Snuggegus", 
             "- :dia: Diamond 1, DPS - szanto#21770 C ✅", 
             "- :gm: : 4k, Tank/Flex - AxelnByback", 
             "- :gm: GM 5, Support - MakaronerBTW#2983 C", 
             "-:master: Master 3, DPS - origo#21428 C ✅ ",
             "-:dia: 3k, DPS - skk",
             "- :plat: 2,6k, Tank - TheChadd",
             "- N/A Unranked, Tank - Ssamv ✅", 
             "- :guld: Gold 5-1, DPS - November ✅", 
             "- N/A Undranked, Support - EEstraada ✅",
             "-:dia:  - Diamond 4, Support - Bobbo356 ✅"]

    for test in tests:
        print(get_player_tokens(test))
test_tokens()


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
