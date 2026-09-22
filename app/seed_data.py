"""
Database seed module.

Automatic seeding of hardcoded/sample operational records has been removed.
Tables start empty upon database initialization and are populated
exclusively via application workflows.
"""


def seed():
    """
    No-op: All operational tables (follow_up, rooms, beds, nurses, requests,
    staff, schedules, etc.) start empty unless created through the application.
    """
    pass


if __name__ == "__main__":
    seed()
