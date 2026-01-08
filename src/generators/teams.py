"""
Team generator for Asana simulation.

Generates teams for each department with unique names.
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
    
    Each team has a unique name within its department.
    If more teams are needed than base names available, 
    numbered suffixes are added (e.g., "Backend Team 2").
    
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
    
    # Department-specific team names
    TEAM_NAMES = {
        "Product Engineering": [
            "Backend", "Frontend", "Mobile", "Platform", "Infrastructure",
            "DevOps", "Security", "QA", "Data", "ML/AI"
        ],
        "Marketing": [
            "Content", "Demand Gen", "Product Marketing", "Brand", "Events", "Growth"
        ],
        "Sales/HR/Customer Success": [
            "Enterprise Sales", "SMB Sales", "Customer Success",
            "Support", "Recruiting", "People Ops"
        ],
        "Upper Management": [
            "Executive", "Strategy", "Operations", "Finance"
        ]
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
        avg_size = sum(OPTIMAL_TEAM_SIZE) // 2  # 6
        num_teams = max(1, len(user_ids) // avg_size)
        
        # Get team names for this department type
        base_names = TEAM_NAMES.get(dept["name"], TEAM_NAMES["Product Engineering"])
        
        # Generate unique team names for this department
        team_names_to_create = []
        
        for i in range(num_teams):
            base_name = base_names[i % len(base_names)]
            iteration = i // len(base_names)
            
            if iteration == 0:
                team_name = f"{base_name} Team"
            else:
                # Add number suffix for subsequent iterations
                team_name = f"{base_name} Team {iteration + 1}"
            
            team_names_to_create.append((base_name, team_name))
        
        # Create team records
        for base_name, team_name in team_names_to_create:
            team_id = generate_uuid()
            
            # Team created after organization (temporal consistency)
            max_days = max(1, (datetime.now() - org_created).days)
            days_after_org = random.randint(1, max_days)
            team_created = org_created + timedelta(days=days_after_org)
            
            team = {
                "team_id": team_id,
                "organization_id": org_id,
                "department_id": dept_id,
                "name": team_name,
                "description": f"The {base_name} team within {dept['name']}.",
                "created_at": team_created.strftime("%Y-%m-%d %H:%M:%S"),
            }
            teams[team_id] = team
    
    # Insert into database
    db.insert_dicts("teams", list(teams.values()))
    logger.info(f"  Generated {len(teams)} teams (unique names per department)")
    
    return teams