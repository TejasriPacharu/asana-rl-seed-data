"""
User generator for Asana simulation.

Generates users with realistic names from Census and SSA data.
Distributes users across organizations and departments.
"""

import uuid
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set

from src.utils.database import Database

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate UUIDv4 to simulate Asana's GID format."""
    return str(uuid.uuid4())


def generate_users(
    db: Database,
    scraper,
    organizations: Dict[str, Dict],
    departments: Dict[str, Dict],
    num_users: int,
    current_time: datetime,
    company_created: datetime,
    random_seed: int = None
) -> Tuple[Dict[str, Dict], Dict[str, List[str]], Set[str]]:
    """
    Generate users for organizations and departments.
    
    Args:
        db: Database instance
        scraper: RealDataScraper instance
        organizations: Dictionary of organization_id -> organization data
        departments: Dictionary of department_id -> department data
        num_users: Total number of users to generate
        current_time: Current timestamp
        company_created: Base creation time for organizations
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (users dict, users_by_dept dict, managers set)
    """
    # #region agent log
    import json
    log_path = "/home/teja/preeh/asana/.cursor/debug.log"
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"id": "log_users_entry", "timestamp": int(datetime.now().timestamp() * 1000), "location": "users.py:generate_users", "message": "Function entry", "data": {"num_users": num_users, "num_orgs": len(organizations), "num_depts": len(departments)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
    except: pass
    # #endregion
    
    logger.info(f"Generating {num_users} users...")
    logger.info("  Source: US Census surnames + SSA first names")
    
    if random_seed:
        random.seed(random_seed)
    
    users = {}
    users_by_dept: Dict[str, List[str]] = {}
    managers: Set[str] = set()
    
    # Group departments by organization
    depts_by_org: Dict[str, List[Dict]] = {}
    for dept_id, dept in departments.items():
        org_id = dept["organization_id"]
        if org_id not in depts_by_org:
            depts_by_org[org_id] = []
        depts_by_org[org_id].append(dept)
    
    # #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"id": "log_users_depts_grouped", "timestamp": int(datetime.now().timestamp() * 1000), "location": "users.py:generate_users", "message": "Departments grouped by org", "data": {"depts_by_org_count": len(depts_by_org)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
    except: pass
    # #endregion
    
    # Distribute users across organizations (proportional to org size)
    # For simplicity, distribute evenly across organizations
    users_per_org = num_users // len(organizations)
    remaining_users = num_users % len(organizations)
    
    user_count = 0
    for org_idx, (org_id, org) in enumerate(organizations.items()):
        org_created = datetime.strptime(org["created_at"], "%Y-%m-%d %H:%M:%S")
        org_domain = org.get("domain", "example.com")
        
        # Assign users to this org
        org_user_count = users_per_org + (1 if org_idx < remaining_users else 0)
        
        # Get departments for this org
        org_depts = depts_by_org.get(org_id, [])
        if not org_depts:
            continue
        
        # Distribute users across departments based on user_percentage
        for dept in org_depts:
            dept_id = dept["department_id"]
            dept_pct = dept["user_percentage"]
            dept_user_count = int(org_user_count * dept_pct)
            
            # #region agent log
            try:
                with open(log_path, "a") as f:
                    f.write(json.dumps({"id": "log_users_dept_dist", "timestamp": int(datetime.now().timestamp() * 1000), "location": "users.py:generate_users", "message": "Distributing users to department", "data": {"dept_id": dept_id, "dept_name": dept["name"], "dept_pct": dept_pct, "dept_user_count": dept_user_count}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
            except: pass
            # #endregion
            
            if dept_id not in users_by_dept:
                users_by_dept[dept_id] = []
            
            # Generate users for this department
            for i in range(dept_user_count):
                user_id = generate_uuid()
                
                # Generate realistic name
                first_name = scraper.get_random_firstname()
                last_name = scraper.get_random_surname()
                
                # Generate email
                email_base = f"{first_name.lower()}.{last_name.lower()}"
                # Handle duplicates by adding number
                email = f"{email_base}@{org_domain}"
                counter = 1
                while any(u.get("email") == email for u in users.values()):
                    email = f"{email_base}{counter}@{org_domain}"
                    counter += 1
                
                # Job titles by department
                job_titles = {
                    "Product Engineering": ["Software Engineer", "Senior Software Engineer", "Staff Engineer", "Engineering Manager", "Tech Lead"],
                    "Marketing": ["Marketing Manager", "Content Creator", "Growth Marketer", "Brand Manager", "Marketing Director"],
                    "Sales/HR/Customer Success": ["Sales Rep", "Account Manager", "HR Manager", "Customer Success Manager", "Recruiter"],
                    "Upper Management": ["VP Engineering", "VP Marketing", "CEO", "CTO", "CFO", "COO"]
                }
                dept_name = dept["name"]
                title_options = job_titles.get(dept_name, job_titles["Product Engineering"])
                job_title = random.choice(title_options)
                
                # Determine if manager (20% chance, or if title suggests it)
                is_manager = "Manager" in job_title or "Director" in job_title or "VP" in job_title or "CEO" in job_title or "CTO" in job_title or "CFO" in job_title or "COO" in job_title
                if not is_manager and random.random() < 0.20:
                    is_manager = True
                
                if is_manager:
                    managers.add(user_id)
                
                # Temporal consistency: user created_at >= organization created_at
                # Spread users over organization history (0-5 years after org creation)
                days_after_org = random.randint(0, min(1825, (current_time - org_created).days))
                user_created = org_created + timedelta(days=days_after_org)
                
                # last_active_at between created_at and current_time
                if user_created < current_time:
                    days_since_created = (current_time - user_created).days
                    days_since_active = random.randint(0, days_since_created)
                    last_active = user_created + timedelta(days=days_since_active)
                else:
                    last_active = user_created
                
                user = {
                    "user_id": user_id,
                    "organization_id": org_id,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "job_title": job_title,
                    "department_id": dept_id,
                    "is_manager": is_manager,
                    "is_active": True,
                    "created_at": user_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_active_at": last_active.strftime("%Y-%m-%d %H:%M:%S"),
                    "profile_photo_url": None,
                }
                
                users[user_id] = user
                users_by_dept[dept_id].append(user_id)
                user_count += 1
                
                # #region agent log
                if user_count % 100 == 0:
                    try:
                        with open(log_path, "a") as f:
                            f.write(json.dumps({"id": "log_users_progress", "timestamp": int(datetime.now().timestamp() * 1000), "location": "users.py:generate_users", "message": "User generation progress", "data": {"users_generated": user_count, "total_target": num_users}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
                    except: pass
                # #endregion
    
    # #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"id": "log_users_complete", "timestamp": int(datetime.now().timestamp() * 1000), "location": "users.py:generate_users", "message": "Function complete", "data": {"total_users": len(users), "total_managers": len(managers), "depts_with_users": len(users_by_dept)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
    except: pass
    # #endregion
    
    # Insert into database
    db.insert_dicts("users", list(users.values()))
    logger.info(f"  Generated {len(users)} users")
    logger.info(f"  Managers: {len(managers)}")
    logger.info(f"  Departments with users: {len(users_by_dept)}")
    
    return users, users_by_dept, managers
