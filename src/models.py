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