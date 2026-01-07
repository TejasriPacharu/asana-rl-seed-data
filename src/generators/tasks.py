"""
Task generator for Asana simulation.

Generates tasks with proper temporal and relational consistency.
"""

import uuid
import random
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional

from src.utils.database import Database
from src.utils.date_helpers import avoid_weekends

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate UUIDv4 to simulate Asana's GID format."""
    return str(uuid.uuid4())


def generate_tasks(
    db: Database,
    scraper,
    projects: Dict[str, Dict],
    users: Dict[str, Dict],
    managers: set,
    organizations: Dict[str, Dict],
    history_start: datetime,
    current_time: datetime,
    tasks_per_user: int,
    UNASSIGNED_TASK_RATE: float = 0.15,
    COMPLETION_RATES: Dict[str, tuple] = None,
    DAY_WEIGHTS: List[float] = None,
    random_seed: int = None
) -> Dict[str, Dict]:
    """
    Generate tasks for projects.
    
    Args:
        db: Database instance
        scraper: RealDataScraper instance
        projects: Dictionary of project_id -> project data
        users: Dictionary of user_id -> user data
        managers: Set of manager user_ids
        organizations: Dictionary of organization_id -> organization data
        history_start: Start of history period
        current_time: Current timestamp
        tasks_per_user: Average tasks per user
        UNASSIGNED_TASK_RATE: Rate of unassigned tasks
        COMPLETION_RATES: Completion rates by project type
        DAY_WEIGHTS: Weights for day of week
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary mapping task_id to task data
    """
    if COMPLETION_RATES is None:
        COMPLETION_RATES = {
            "sprint": (0.70, 0.85),
            "campaign": (0.60, 0.75),
            "process": (0.40, 0.50),
            "cross_functional": (0.55, 0.70),
            "oversight": (0.50, 0.65),
        }
    
    if DAY_WEIGHTS is None:
        DAY_WEIGHTS = [0.85, 0.95, 0.90, 0.75, 0.65, 0.20, 0.15]  # Mon-Sun
    
    total = len(users) * tasks_per_user
    logger.info(f"Generating ~{total} tasks...")
    logger.info("  Name patterns: GitHub Public Issues")
    logger.info(f"  Unassigned: {UNASSIGNED_TASK_RATE*100:.0f}% (Asana benchmark)")
    logger.info("  Day pattern: Higher Mon-Wed (Asana Year in Review)")
    
    if random_seed:
        random.seed(random_seed)
    
    patterns = scraper.github_patterns
    tasks = []
    proj_list = list(projects.values())
    
    user_ids = list(users.keys())
    non_manager_ids = [uid for uid in user_ids if uid not in managers]
    manager_ids = list(managers) if managers else user_ids
    
    for i in range(total):
        proj = random.choice(proj_list)
        proj_created = datetime.strptime(proj["created_at"], "%Y-%m-%d %H:%M:%S")
        proj_start = datetime.strptime(proj["start_date"], "%Y-%m-%d").date()
        
        # Get users from same organization as project
        org_id = proj["organization_id"]
        org_users = [uid for uid in user_ids if users[uid]["organization_id"] == org_id]
        org_non_mgrs = [uid for uid in org_users if uid not in managers]
        org_managers = [uid for uid in org_users if uid in managers]
        
        # Assignee: 15% unassigned
        if random.random() < UNASSIGNED_TASK_RATE:
            assignee = None
        else:
            # Prefer non-managers for IC tasks
            if org_non_mgrs:
                assignee = random.choice(org_non_mgrs)
            else:
                assignee = random.choice(org_users) if org_users else random.choice(user_ids)
        
        # Creator: 70% managers
        if random.random() < 0.70 and org_managers:
            creator = random.choice(org_managers)
        else:
            creator = assignee or (random.choice(org_users) if org_users else random.choice(user_ids))
        
        # Name from GitHub patterns
        task_name = _task_name(patterns)
        
        # Description: 20% empty, 50% brief, 30% detailed
        desc = _task_description()
        
        # Created at: after project created_at, weighted by day of week (temporal consistency)
        # Must be after project created_at
        earliest = max(proj_created, history_start)
        if earliest >= current_time:
            # If project was just created, allow tasks to be created at the same time
            earliest = proj_created
        created_at = _weighted_datetime(earliest, current_time, DAY_WEIGHTS)
        # Final check: ensure created_at >= proj_created
        if created_at < proj_created:
            created_at = proj_created + timedelta(hours=random.randint(1, 24))
        
        # Completion by project type
        comp_range = COMPLETION_RATES.get(proj["project_type"], (0.50, 0.70))
        is_completed = random.random() < random.uniform(*comp_range)
        
        # completed_at: log-normal 1-14 days, but MUST be > created_at (temporal consistency)
        completed_at = None
        completed_by = None
        if is_completed:
            days = min(14, max(0.1, random.lognormvariate(1.1, 0.8)))
            completed_at = created_at + timedelta(days=days)
            # TC-1: completed_at MUST be > created_at
            if completed_at <= created_at:
                completed_at = created_at + timedelta(hours=random.randint(1, 24))
            # Don't complete in future
            if completed_at > current_time:
                completed_at = current_time - timedelta(hours=random.randint(1, 48))
            # Final check for TC-1
            if completed_at <= created_at:
                completed_at = created_at + timedelta(minutes=random.randint(30, 1440))
            completed_by = assignee or creator
        
        # Due date per distribution
        due_date = _due_date(created_at, current_time)
        
        # updated_at: between created_at and current_time (temporal consistency)
        days_since_creation = (current_time - created_at).total_seconds() / 86400
        if days_since_creation > 0:
            update_days = random.uniform(0, min(days_since_creation, 30))
            updated_at = created_at + timedelta(days=update_days)
            if updated_at > current_time:
                updated_at = current_time
        else:
            updated_at = created_at
        
        # Use completed_at if task is completed
        if is_completed and completed_at:
            updated_at = completed_at
        
        task_id = generate_uuid()
        task = {
            "task_id": task_id,
            "organization_id": org_id,
            "name": task_name,
            "description": desc,
            "assignee_id": assignee,
            "parent_task_id": None,
            "is_completed": is_completed,
            "completed_at": completed_at.strftime("%Y-%m-%d %H:%M:%S") if completed_at else None,
            "completed_by_id": completed_by,
            "due_date": due_date.strftime("%Y-%m-%d") if due_date else None,
            "due_time": None,
            "start_date": None,
            "is_milestone": random.random() < 0.03,
            "priority": random.choices(["low", "medium", "high", "urgent"], weights=[0.2, 0.45, 0.25, 0.1])[0],
            "estimated_hours": random.choice([None, 2, 4, 8]) if random.random() < 0.3 else None,
            "actual_hours": None,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "created_by_id": creator,
            "num_likes": random.choices([0, 1, 2, 3], weights=[0.7, 0.15, 0.1, 0.05])[0],
        }
        
        tasks.append(task)
        
        if (i + 1) % 10000 == 0:
            logger.info(f"  Generated {i + 1}/{total} tasks...")
    
    # Insert into database
    db.insert_dicts("tasks", tasks)
    logger.info(f"  Generated {len(tasks)} tasks")
    
    return {task["task_id"]: task for task in tasks}


def _task_name(patterns: Dict) -> str:
    """Generate task name from GitHub patterns."""
    comps = patterns.get("components", ["API", "Backend"])[:20]
    feats = patterns.get("features", ["auth"])[:15]
    errs = patterns.get("errors", ["timeout"])[:10]
    
    # Mix of engineering, marketing, and general tasks
    ttype = random.choices(["feat", "bug", "refactor", "marketing", "sales"], 
                           weights=[0.35, 0.25, 0.15, 0.15, 0.10])[0]
    
    if ttype == "feat":
        return f"Implement {random.choice(feats)} for {random.choice(comps)}"
    elif ttype == "bug":
        return f"[Bug]: {random.choice(comps)} {random.choice(errs)}"
    elif ttype == "refactor":
        return f"Refactor {random.choice(comps)}"
    elif ttype == "marketing":
        content = ["blog post", "email", "landing page", "social post"]
        return f"Write {random.choice(content)} for Q{random.randint(1,4)} campaign"
    else:  # sales
        cos = ["Acme Corp", "TechStart", "Global Inc", "Enterprise Co"]
        return f"Follow up with {random.choice(cos)}"


def _task_description() -> Optional[str]:
    """Generate task description."""
    roll = random.random()
    if roll < 0.20:
        return None
    elif roll < 0.70:
        return random.choice(["Complete per sprint goals.", "High priority.", "See docs for details."])
    else:
        return "Complete this task.\n\n**Acceptance Criteria:**\n- [ ] Functionality works\n- [ ] Tests pass"


def _weighted_datetime(start: datetime, end: datetime, day_weights: List[float]) -> datetime:
    """Generate datetime weighted by day of week."""
    delta = (end - start).total_seconds()
    dt = start + timedelta(seconds=random.random() * delta)
    
    # Potentially shift to more likely day
    day = dt.weekday()
    if random.random() > day_weights[day]:
        shift = random.choice([0, 1, 2]) - day  # Shift towards Mon-Wed
        dt = dt + timedelta(days=shift)
        if dt < start:
            dt = start
        elif dt > end:
            dt = end
    
    return dt


def _due_date(created: datetime, current_time: datetime) -> Optional[date]:
    """Generate due date per methodology distribution."""
    roll = random.random()
    
    if roll < 0.10:  # no_due_date
        return None
    elif roll < 0.15:  # overdue
        return created.date() - timedelta(days=random.randint(1, 14))
    elif roll < 0.40:  # within_1_week
        due = created.date() + timedelta(days=random.randint(1, 7))
        return avoid_weekends(due)
    elif roll < 0.80:  # within_1_month
        due = created.date() + timedelta(days=random.randint(8, 30))
        return avoid_weekends(due)
    else:  # 1_to_3_months
        due = created.date() + timedelta(days=random.randint(31, 90))
        return avoid_weekends(due)

