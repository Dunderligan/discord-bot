import asyncpg
import os

# v not needed
import asyncio

"""
Module should:
let user get send and recieve query.

Host standard-functions for queries from:
- players of roster
- matches from division"""

postgres_link = os.getenv("POSTGRES_LINK")


async def get_query(sql: str) -> list:
    """
        Opens connection to database and returns values of
        input SQL-string.
    """
    try:
        conn: asyncpg.Connection = await asyncpg.connect(postgres_link)
        values = await conn.fetch(sql, timeout=30)
        if not values:
            raise Exception(f"Found no values with SQL: {sql}")
        return values
    except Exception as e:
        print(f"Failed to get query, got error: {e}")
    finally:
        await conn.close()


async def get_rosters(season: str, division: str, team: str = None) -> list:
    """
        Gets all players (tag, rank, role, and if captain) of a division, 
        sorts them after team, and returns. Has option to filter 
        by specific team name as well.
    """
    sql = f"""
        SELECT
            p.battletag,
            m.rank,
            m.tier, 
            m.role,
            m.is_captain,
            r.name AS "roster_name"
        FROM player p
            JOIN "member" m ON m.player_id = p.id
            JOIN "roster" r ON r.id = m.roster_id
            JOIN "group" g ON g.id = r.group_id
            JOIN "division" d ON d.id = g.division_id
            JOIN "season" s ON s.id = d.season_id
        WHERE s.slug = '{season}'
            AND d.name = '{division}'"""
    if team:
        sql += f" AND r.name = '{team}'"

    values = await get_query(sql)
    values = sort_players_into_teams(values)
    return values


def sort_players_into_teams(players: list) -> dict:
    """
        Takes a list of players according to database structure, 
        and returns a dictionary where they have been sorted by according team.
    """
    teams: dict = {}
    for p in players:
        team: str = p["roster_name"]
        if not teams.get(team):
            teams[team] = []
        teams[team].append(
            (p["rank"], p["tier"], p["role"], p["battletag"], p["is_captain"])
        )
    return teams


def main():
    values: list[asyncpg.Record] = asyncio.run(get_rosters("test", "Division 1"))
    print(values)


if __name__ == "__main__":
    main()
