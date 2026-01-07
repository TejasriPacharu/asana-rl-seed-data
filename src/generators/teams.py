"""
Team generator for Asana simulation.

Generates teams for each department.
"""

import uuid
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from src.utils.database import Database

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate UUIDv4 to simulate Asana's GID format."""
    return str(uuid.uuid4())


def generate_teams(
    db: Database,
    departments: Dict[str, Dict],
    organizations: Dict[str, Dict],
    users_by_dept: Dict[str, List[str]],
    random_seed: int = None
) -> Dict[str, Dict]:
    """
    Generate teams for departments.
    
    Args:
        db: Database instance
        departments: Dictionary of department_id -> department data
        organizations: Dictionary of organization_id -> organization data
        users_by_dept: Dictionary mapping department_id to list of user_ids
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary mapping team_id to team data
    """
    logger.info("Generating teams...")
    logger.info("  Target size: 5-7 members (QSM Research)")
    
    if random_seed:
        random.seed(random_seed)
    
    OPTIMAL_TEAM_SIZE = (5, 7)
    
    TEAM_NAMES = {
        "Product Engineering": ["Backend", "Frontend", "Mobile", "Platform", "Infrastructure",
                               "DevOps", "Security", "QA", "Data", "ML/AI"],
        "Marketing": ["Content", "Demand Gen", "Product Marketing", "Brand", "Events", "Growth"],
        "Sales/HR/Customer Success": ["Enterprise Sales", "SMB Sales", "Customer Success",
                                      "Support", "Recruiting", "People Ops"],
        "Upper Management": ["Executive", "Strategy", "Operations", "Finance"]
    }
    
    teams = {}
    
    for dept_id, dept in departments.items():
        org_id = dept["organization_id"]
        org = organizations[org_id]
        org_created = datetime.strptime(org["created_at"], "%Y-%m-%d %H:%M:%S")
        
        # Get users for this department
        user_ids = users_by_dept.get(dept_id, [])
        if not user_ids:
            continue
        
        # Calculate number of teams based on optimal size
        avg_size = sum(OPTIMAL_TEAM_SIZE) // 2
        num_teams = max(1, len(user_ids) // avg_size)
        
        # Get team names for this department
        names = TEAM_NAMES.get(dept["name"], TEAM_NAMES["Product Engineering"])
        
        for i in range(num_teams):
            team_id = generate_uuid()
            name = names[i % len(names)]
            
            # Team created after organization (temporal consistency)
            # Spread teams over organization history
            days_after_org = random.randint(1, (datetime.now() - org_created).days)
            team_created = org_created + timedelta(days=days_after_org)
            
            team = {
                "team_id": team_id,
                "organization_id": org_id,
                "department_id": dept_id,
                "name": f"{name} Team",
                "description": f"The {name} team within {dept['name']}.",
                "created_at": team_created.strftime("%Y-%m-%d %H:%M:%S"),
            }
            teams[team_id] = team
    
    # Insert into database
    db.insert_dicts("teams", list(teams.values()))
    logger.info(f"  Generated {len(teams)} teams")
    
    return teams

