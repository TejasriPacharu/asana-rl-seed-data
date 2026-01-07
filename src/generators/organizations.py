"""
Organization generator for Asana simulation.

Generates multiple organizations with realistic names from Y Combinator directory.
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


def generate_organizations(
    db: Database,
    scraper,
    num_organizations: int,
    company_created: datetime,
    random_seed: int = None
) -> Dict[str, Dict]:
    """
    Generate organizations.
    
    Args:
        db: Database instance
        scraper: RealDataScraper instance
        num_organizations: Number of organizations to generate
        company_created: Base creation time for organizations
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary mapping organization_id to organization data
    """
    logger.info(f"Generating {num_organizations} organizations...")
    logger.info("  Source: Y Combinator company directory patterns")
    
    if random_seed:
        random.seed(random_seed)
    
    organizations = {}
    used_names = set()
    
    # Get unique company names
    available_names = scraper.company_names.copy()
    random.shuffle(available_names)
    
    for i in range(num_organizations):
        # Get unique company name
        company_name = None
        for name in available_names:
            if name not in used_names:
                company_name = name
                break
        
        if not company_name:
            # Fallback if we run out of unique names
            company_name = f"TechCorp{i+1}"
        
        used_names.add(company_name)
        
        # Generate domain from company name
        domain = company_name.lower().replace(" ", "").replace(".", "").replace("-", "") + ".com"
        
        # Organization created at different times (spread over 2-8 years)
        years_ago = random.uniform(2, 8)
        org_created = company_created - timedelta(days=int(years_ago * 365))
        
        org_id = generate_uuid()
        org = {
            "organization_id": org_id,
            "name": company_name,
            "domain": domain,
            "created_at": org_created.strftime("%Y-%m-%d %H:%M:%S"),
            "is_organization": True,
        }
        
        organizations[org_id] = org
    
    # Insert into database
    db.insert_dicts("organizations", list(organizations.values()))
    logger.info(f"  Generated {len(organizations)} organizations")
    
    return organizations

