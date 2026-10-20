from dataclasses import dataclass


@dataclass
class Roster:
    id: str
    name: str
    slug: str

    def from_json(json: dict):
        return Roster(json.get("id"), json.get("name"), json.get("slug"))


@dataclass
class Membership:
    rank: str
    tier: int
    sr: int
    is_captain: bool
    registered_name: str
    roster: Roster
    role: str

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


@dataclass
class Player:
    id: str
    battletag: str
    memberships: list[Membership]

    def from_json(json: dict):
        return Player(
            json.get("id"),
            json.get("battletag"),
            [Membership.from_json(m) for m in json.get("memberships")],
        )


@dataclass
class Bracket:
    id: str
    name: str

    def from_json(json: dict):
        return Bracket(json.get("id"), json.get("name"))


@dataclass
class Group:
    id: str
    name: str
    slug: str
    rosters: list[Roster] # rosters may be an empty list, some requests return groups without rosters

    def from_json(json: dict):
        return Group(
            json.get("id"),
            json.get("name"),
            json.get("slug"),
            [Roster.from_json(r) for r in json.get("rosters")]
            if json.get("rosters")
            else [],
        )


@dataclass
class Division:
    id: str
    name: str
    slug: str
    groups: list[Group]
    brackets: list[Bracket]

    def from_json(json: dict):
        return Division(
            json.get("id"),
            json.get("name"),
            json.get("slug"),
            [Group.from_json(g) for g in json.get("groups")],
            [Bracket.from_json(b) for b in json.get("brackets")],
        )


@dataclass
class Season:
    id: str
    name: str
    slug: str
    legacyRanks: bool
    hidden: bool
    startedAt: str
    endedAt: str | None
    divisions: list[Division]

    def from_json(json: dict):
        return Season(
            json.get("id"),
            json.get("name"),
            json.get("slug"),
            json.get("legacyRanks"),
            json.get("hidden"),
            json.get("startedAt"),
            json.get("endedAt"),
            [Division.from_json(d) for d in json.get("divisions")],
        )
