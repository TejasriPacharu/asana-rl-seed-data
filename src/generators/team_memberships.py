"""
Team membership generator for Asana simulation.

Generates team memberships with proper temporal consistency.
"""

import uuid
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from src.utils.database import Database
from src.utils.date_helpers import datetime_after

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate UUIDv4 to simulate Asana's GID format."""
    return str(uuid.uuid4())


def generate_team_memberships(
    db: Database,
    teams: Dict[str, Dict],
    users: Dict[str, Dict],
    users_by_dept: Dict[str, List[str]],
    random_seed: int = None
) -> int:
    """
    Generate team memberships.
    
    Args:
        db: Database instance
        teams: Dictionary of team_id -> team data
        users: Dictionary of user_id -> user data
        users_by_dept: Dictionary mapping department_id to list of user_ids
        random_seed: Random seed for reproducibility
        
    Returns:
        Number of memberships created
    """
    logger.info("Generating team memberships...")
    logger.info("  Rule RC-8: Each user has exactly one primary team")
    logger.info("  Cross-functional: 15% users in multiple teams")
    
    if random_seed:
        random.seed(random_seed)
    
    # Group teams by department
    teams_by_dept: Dict[str, List[str]] = {}
    for team_id, team in teams.items():
        dept_id = team["department_id"]
        if dept_id not in teams_by_dept:
            teams_by_dept[dept_id] = []
        teams_by_dept[dept_id].append(team_id)
    
    memberships = []
    
    for dept_id, user_ids in users_by_dept.items():
        team_ids = teams_by_dept.get(dept_id, [])
        if not team_ids:
            continue
        
        for user_id in user_ids:
            user = users[user_id]
            user_created = datetime.strptime(user["created_at"], "%Y-%m-%d %H:%M:%S")
            
            # Primary team
            primary_team = random.choice(team_ids)
            team = teams[primary_team]
            team_created = datetime.strptime(team["created_at"], "%Y-%m-%d %H:%M:%S")
            
            # Role based on manager status
            role = "lead" if user["is_manager"] else random.choices(
                ["member", "lead", "admin"], weights=[0.80, 0.15, 0.05])[0]
            
            # joined_at: after both user and team created_at (temporal consistency)
            earliest = max(user_created, team_created)
            joined_at = datetime_after(earliest, min_hours=1, max_hours=720)
            
            memberships.append({
                "membership_id": generate_uuid(),
                "team_id": primary_team,
                "user_id": user_id,
                "role": role,
                "is_primary_team": True,  # RC-8: Exactly one primary
                "joined_at": joined_at.strftime("%Y-%m-%d %H:%M:%S"),
            })
            
            # 15% have secondary team
            if random.random() < 0.15 and len(team_ids) > 1:
                secondary = random.choice([t for t in team_ids if t != primary_team])
                secondary_team = teams[secondary]
                secondary_team_created = datetime.strptime(secondary_team["created_at"], "%Y-%m-%d %H:%M:%S")
                
                # joined_at: after both user and secondary team created_at
                earliest_secondary = max(user_created, secondary_team_created)
                joined_secondary = datetime_after(earliest_secondary, min_hours=24, max_hours=720)
                
                memberships.append({
                    "membership_id": generate_uuid(),
                    "team_id": secondary,
                    "user_id": user_id,
                    "role": "member",
                    "is_primary_team": False,
                    "joined_at": joined_secondary.strftime("%Y-%m-%d %H:%M:%S"),
                })
    
    db.insert_dicts("team_memberships", memberships)
    logger.info(f"  Generated {len(memberships)} team memberships")
    return len(memberships)

