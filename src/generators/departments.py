"""
Department generator for Asana simulation.

Generates departments for each organization.
"""

import uuid
import random
import logging
from datetime import datetime
from typing import Dict, List

from src.utils.database import Database

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate UUIDv4 to simulate Asana's GID format."""
    return str(uuid.uuid4())


def generate_departments(
    db: Database,
    organizations: Dict[str, Dict],
    random_seed: int = None
) -> Dict[str, Dict]:
    """
    Generate departments for organizations.
    
    Args:
        db: Database instance
        organizations: Dictionary of organization_id -> organization data
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary mapping department_id to department data
    """
    logger.info("Generating departments...")
    logger.info("  Distribution: Eng 40%, Marketing 15%, Sales/HR/CS 35%, Mgmt 10%")
    
    if random_seed:
        random.seed(random_seed)
    
    # Department definitions
    DEPARTMENTS = [
        ("Product Engineering", 0.40, "sprint_based"),
        ("Marketing", 0.15, "campaign_based"),
        ("Sales/HR/Customer Success", 0.35, "process_driven"),
        ("Upper Management", 0.10, "oversight"),
    ]
    
    departments = {}
    
    for org_id, org in organizations.items():
        org_created = datetime.strptime(org["created_at"], "%Y-%m-%d %H:%M:%S")
        
        for name, pct, workflow in DEPARTMENTS:
            dept_id = generate_uuid()
            dept = {
                "department_id": dept_id,
                "organization_id": org_id,
                "name": name,
                "description": f"{name} handles {workflow.replace('_', ' ')} workflows.",
                "user_percentage": pct,
                "workflow_type": workflow,
                "created_at": org_created.strftime("%Y-%m-%d %H:%M:%S"),
            }
            departments[dept_id] = dept
    
    # Insert into database
    db.insert_dicts("departments", list(departments.values()))
    logger.info(f"  Generated {len(departments)} departments")
    
    return departments

