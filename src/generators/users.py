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
    """

    logger.info(f"Generating {num_users} users...")
    logger.info("  Source: US Census surnames + SSA first names")

    if random_seed:
        random.seed(random_seed)

    users: Dict[str, Dict] = {}
    users_by_dept: Dict[str, List[str]] = {}
    managers: Set[str] = set()

    # Group departments by organization
    depts_by_org: Dict[str, List[Dict]] = {}
    for dept_id, dept in departments.items():
        depts_by_org.setdefault(dept["organization_id"], []).append(dept)

    # Distribute users evenly across organizations
    users_per_org = num_users // len(organizations)
    remaining_users = num_users % len(organizations)

    for org_idx, (org_id, org) in enumerate(organizations.items()):
        org_created = datetime.strptime(org["created_at"], "%Y-%m-%d %H:%M:%S")
        org_domain = org.get("domain", "example.com")

        org_user_count = users_per_org + (1 if org_idx < remaining_users else 0)
        org_depts = depts_by_org.get(org_id, [])
        if not org_depts:
            continue

        for dept in org_depts:
            dept_id = dept["department_id"]
            dept_user_count = int(org_user_count * dept["user_percentage"])
            users_by_dept.setdefault(dept_id, [])

            for _ in range(dept_user_count):
                user_id = generate_uuid()

                first_name = scraper.get_random_firstname()
                last_name = scraper.get_random_surname()

                email_base = f"{first_name.lower()}.{last_name.lower()}"
                email = f"{email_base}@{org_domain}"
                suffix = 1
                while any(u["email"] == email for u in users.values()):
                    email = f"{email_base}{suffix}@{org_domain}"
                    suffix += 1

                job_titles = {
                    "Product Engineering": [
                        "Software Engineer", "Senior Software Engineer",
                        "Staff Engineer", "Engineering Manager", "Tech Lead"
                    ],
                    "Marketing": [
                        "Marketing Manager", "Content Creator",
                        "Growth Marketer", "Brand Manager", "Marketing Director"
                    ],
                    "Sales/HR/Customer Success": [
                        "Sales Rep", "Account Manager",
                        "HR Manager", "Customer Success Manager", "Recruiter"
                    ],
                    "Upper Management": [
                        "VP Engineering", "VP Marketing",
                        "CEO", "CTO", "CFO", "COO"
                    ],
                }

                title_options = job_titles.get(dept["name"], job_titles["Product Engineering"])
                job_title = random.choice(title_options)

                is_manager = (
                    any(x in job_title for x in ["Manager", "Director", "VP", "CEO", "CTO", "CFO", "COO"])
                    or random.random() < 0.20
                )

                if is_manager:
                    managers.add(user_id)

                days_after_org = random.randint(
                    0, min(1825, (current_time - org_created).days)
                )
                created_at = org_created + timedelta(days=days_after_org)

                last_active = (
                    created_at + timedelta(days=random.randint(0, (current_time - created_at).days))
                    if created_at < current_time
                    else created_at
                )

                users[user_id] = {
                    "user_id": user_id,
                    "organization_id": org_id,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "job_title": job_title,
                    "department_id": dept_id,
                    "is_manager": is_manager,
                    "is_active": True,
                    "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_active_at": last_active.strftime("%Y-%m-%d %H:%M:%S"),
                    "profile_photo_url": None,
                }

                users_by_dept[dept_id].append(user_id)

    db.insert_dicts("users", list(users.values()))
    logger.info(f"  Generated {len(users)} users")
    logger.info(f"  Managers: {len(managers)}")

    return users, users_by_dept, managers
