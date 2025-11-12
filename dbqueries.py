import asyncpg

# v not needed
import asyncio

"""
Purpose of module:
Establish connection to database, and let other scripts retrieve SQL-queries.
Host standard functions to recieve particular data, such as matches, rosters, and divisions."""

conn: asyncpg.Connection = None


async def connect_db(postgres_link: str) -> None:
    global conn
    conn = await asyncpg.connect(postgres_link)


async def get_query(sql: str) -> list:
    """
    Tries to get and return values from database according to SQL-query.
    """
    try:
        if not conn:
            raise Exception("Has not connected to database...")
        values = await conn.fetch(sql, timeout=30)
        if not values:
            raise Exception(f"Found no values with query: \n{sql}")
        return values
    except Exception as e:
        print(f"Failed to get query, got error: {e}")


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


async def get_divisions(season: str) -> list:
    """
    Gets all division names for given season.
    """
    sql = f"""
        SELECT 
            d.name AS "division_name"
        FROM division d
            JOIN "season" s ON d.season_id = s.id
        WHERE s.slug = '{season}'
        ORDER BY d.name
        """

    values = await get_query(sql)
    values = [division["division_name"] for division in values]
    return values


async def get_matches(season: str, division: str) -> list:
    """
    Gets all matches played in given division, during given season.
    """
    sql = f"""
            SELECT 
                m.team_a_score,
                m.team_b_score,
                ra.name AS "roster_a_name",
                rb.name AS "roster_b_name",
                ra.id AS "roster_a_id",
                rb.id AS "roster_b_id",
                m.draws AS "draws"
            FROM division d
                JOIN "group" g ON g.division_id = d.id
                JOIN "match" m ON m.group_id = g.id
                JOIN "roster" ra ON m.roster_a_id = ra.id
                JOIN "roster" rb ON m.roster_b_id = rb.id
                JOIN "season" s ON d.season_id = s.id
            WHERE s.slug = '{season}'
                AND d.name = '{division}'
                """

    values = await get_query(sql)
    values = [
        (
            m["team_a_score"],
            m["team_b_score"],
            m["roster_a_name"],
            m["roster_b_name"],
            str(m["roster_a_id"]),
            str(m["roster_b_id"]),
            m["draws"],
        )
        for m in values
    ]
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
    values: list[asyncpg.Record] = asyncio.run(get_matches("test", "Division 1"))
    print(values)


if __name__ == "__main__":
    main()
