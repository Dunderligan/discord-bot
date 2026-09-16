class Roster:
    id: str
    name: str
    slug: str

    def __init__(self, id: str, name: str, slug: str):
        self.id = id
        self.name = name
        self.slug = slug

    def from_json(json: dict):
        return Roster(json.get("id"), json.get("name"), json.get("slug"))


class Membership:
    rank: str
    tier: int
    sr: int
    is_captain: bool
    registered_name: str
    roster: Roster
    role: str

    def __init__(
        self,
        rank: str,
        tier: int,
        sr: int,
        is_captain: bool,
        registered_name: str,
        roster: Roster,
        role: str,
    ):
        self.rank = rank
        self.tier = tier
        self.sr = sr
        self.is_captain = is_captain
        self.registered_name = registered_name
        self.roster = roster
        self.role = role

    def from_json(json: dict):
        return Membership(
            json.get("rank"),
            json.get("tier"),
            json.get("sr"),
            json.get("isCaptain"),
            json.get("registeredName"),
            Roster.from_json(json.get("roster")),
            json.get("role"),
        )


class Player:
    id: str
    battletag: str
    memberships: list[Membership]

    def __init__(self, id: str, battletag: str, memberships: list[Membership]):
        self.id = id
        self.battletag = battletag
        self.memberships = memberships

    def from_json(json: dict):
        return Player(
            json.get("id"),
            json.get("battletag"),
            [Membership.from_json(m) for m in json.get("memberships")],
        )