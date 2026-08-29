def checkin_player(discord_id: str, battletag: str) -> str:
    """
        Checks in player into website. Returns a string response to be displayed to the user.
    """
    if not validate_battletag(battletag):
        return "Failed to check in: Invalid battletag format. Battletags should be written like 'Gnome#1337'."
    


def validate_battletag(battletag: str) -> bool:
    """Returns True if string is on form Name#0000, i.e. a string, #, and number of digits greater than 2 and fewer than 6."""
    try:
        split_tag = battletag.split("#")
        if len(split_tag) != 2 or len(split_tag[0]) == 0 or len(split_tag[1]) <= 2 or len(split_tag[1]) >= 7:
            return False
        int(split_tag[1])
        return True
    except ValueError:
        return False