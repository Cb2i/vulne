from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.team import Team


def get_or_create_team(db: Session, *, name: str) -> Team:
    team = db.scalar(select(Team).where(Team.name == name))
    if team is None:
        team = Team(name=name)
        db.add(team)
        db.flush()
    return team
