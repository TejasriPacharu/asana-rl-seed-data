"""
Project generator for Asana simulation.

Generates projects with proper temporal consistency.

Temporal Consistency Rules:
- created_at >= team.created_at
- start_date = created_at.date()
- due_date >= start_date
- updated_at >= created_at AND updated_at <= min(due_date, current_time)
"""

import uuid
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from src.utils.database import Database
from src.utils.date_helpers import random_datetime_in_range

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate UUIDv4 to simulate Asana's GID format."""
    return str(uuid.uuid4())


def generate_projects(
    db: Database,
    teams: Dict[str, Dict],
    organizations: Dict[str, Dict],
    users: Dict[str, Dict],
    managers: set,
    history_start: datetime,
    current_time: datetime,
    TWO_WEEK_SPRINT_RATE: float = 0.591,
    random_seed: int = None
) -> Dict[str, Dict]:
    """
    Generate projects for teams.
    
    Temporal Consistency:
    - created_at >= team.created_at (project created after team)
    - start_date = created_at.date() (project starts when created)
    - due_date >= start_date (due date after start)
    - updated_at between created_at and min(due_date, current_time)
    
    Args:
        db: Database instance
        teams: Dictionary of team_id -> team data
        organizations: Dictionary of organization_id -> organization data
        users: Dictionary of user_id -> user data
        managers: Set of manager user_ids
        history_start: Start of history period
        current_time: Current timestamp
        TWO_WEEK_SPRINT_RATE: Rate of 2-week sprints
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary mapping project_id to project data
    """
    logger.info("Generating projects...")
    logger.info("  Source: Asana Public Templates")
    logger.info(f"  Sprint: {TWO_WEEK_SPRINT_RATE*100:.1f}% use 2-week sprints (Parabol research)")
    
    if random_seed:
        random.seed(random_seed)
    
    PROJECT_TYPES = ["sprint", "campaign", "process", "cross_functional", "oversight"]
    PROJECT_NAME_TEMPLATES = {
        "sprint": ["Sprint {num} - Engineering", "Q{quarter} Engineering Sprint", "Sprint {num} - Product"],
        "campaign": ["Q{quarter} Product Launch", "Holiday Campaign", "Q{quarter} Growth Campaign"],
        "process": ["Sales Pipeline", "Support Tickets", "Customer Onboarding"],
        "cross_functional": ["Q{quarter} Cross-Team Initiative", "Product Launch Q{quarter}"],
        "oversight": ["Q{quarter} Strategic Planning", "Executive Review"],
    }
    
    projects = []
    user_ids = list(users.keys())
    manager_ids = list(managers) if managers else user_ids
    
    # Group teams by organization
    teams_by_org: Dict[str, List[Dict]] = {}
    for team_id, team in teams.items():
        org_id = team["organization_id"]
        if org_id not in teams_by_org:
            teams_by_org[org_id] = []
        teams_by_org[org_id].append(team)
    
    for team_id, team in teams.items():
        org_id = team["organization_id"]
        org = organizations[org_id]
        
        # Get team creation time (temporal consistency: project after team)
        team_created = datetime.strptime(team["created_at"], "%Y-%m-%d %H:%M:%S")
        
        # Number of projects per team
        num_projects = random.randint(2, 4)
        
        # Get users from this team's organization
        org_users = [uid for uid, user in users.items() if user["organization_id"] == org_id]
        org_managers = [uid for uid in org_users if uid in managers]
        
        for i in range(num_projects):
            proj_type = random.choice(PROJECT_TYPES)
            proj_id = generate_uuid()
            
            # Name from templates
            quarter = (i % 4) + 1
            sprint_num = 40 + (i % 15)
            templates = PROJECT_NAME_TEMPLATES.get(proj_type, PROJECT_NAME_TEMPLATES["sprint"])
            name_template = random.choice(templates)
            name = name_template.format(num=sprint_num, quarter=quarter)
            
            # Creator (prefer managers)
            creator = random.choice(org_managers) if org_managers else random.choice(org_users)
            
            # created_at: after team created_at, within history period (temporal consistency)
            earliest = max(team_created, history_start)
            created_at = random_datetime_in_range(earliest, current_time)
            
            # start_date = created_at (temporal consistency)
            start_date = created_at.date()
            
            # Due date: sprints use 2-week (59.1%)
            if proj_type == "sprint" and random.random() < TWO_WEEK_SPRINT_RATE:
                due_date = start_date + timedelta(days=14)
            else:
                due_date = start_date + timedelta(days=random.randint(14, 90))
            
            # updated_at: MUST be between created_at and min(due_date, current_time)
            # This ensures updated_at never exceeds the project's due date
            due_datetime = datetime.combine(due_date, datetime.max.time())
            latest_update = min(due_datetime, current_time)
            
            if latest_update > created_at:
                # Random time between created_at and latest_update
                delta_seconds = (latest_update - created_at).total_seconds()
                random_seconds = random.random() * delta_seconds
                updated_at = created_at + timedelta(seconds=random_seconds)
            else:
                updated_at = created_at
            
            proj = {
                "project_id": proj_id,
                "organization_id": org_id,
                "team_id": team_id,
                "name": name,
                "description": f"Project: {name}",
                "color": random.choice(["dark-blue", "dark-green", "dark-purple", "dark-orange"]),
                "is_archived": random.random() < 0.30,
                "is_public": random.random() < 0.90,
                "project_type": proj_type,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "due_date": due_date.strftime("%Y-%m-%d"),
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "created_by_id": creator,
            }
            projects.append(proj)
    
    # Insert into database
    db.insert_dicts("projects", projects)
    logger.info(f"  Generated {len(projects)} projects")
    
    return {proj["project_id"]: proj for proj in projects}