"""
Task generator for Asana simulation.

Generates tasks with realistic lifecycle behavior, enforcing
temporal and relational consistency.
"""

import uuid
import random
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple

from src.utils.database import Database
from src.utils.date_helpers import avoid_weekends

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------

def generate_uuid() -> str:
    return str(uuid.uuid4())


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

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
    random_seed: Optional[int] = None
) -> Dict[str, Dict]:

    if random_seed:
        random.seed(random_seed)

    COMPLETION_RATES = COMPLETION_RATES or {
        "sprint": (0.70, 0.85),
        "campaign": (0.60, 0.75),
        "process": (0.40, 0.50),
        "cross_functional": (0.55, 0.70),
        "oversight": (0.50, 0.65),
    }

    DAY_WEIGHTS = DAY_WEIGHTS or [0.85, 0.95, 0.90, 0.75, 0.65, 0.20, 0.15]

    total_tasks = len(users) * tasks_per_user
    logger.info(f"Generating ~{total_tasks} tasks")

    tasks: List[Dict] = []
    projects_list = list(projects.values())
    user_ids = list(users.keys())

    for i in range(total_tasks):
        project = random.choice(projects_list)

        task = _generate_single_task(
            scraper=scraper,
            project=project,
            users=users,
            user_ids=user_ids,
            managers=managers,
            history_start=history_start,
            current_time=current_time,
            completion_rates=COMPLETION_RATES,
            day_weights=DAY_WEIGHTS,
            unassigned_rate=UNASSIGNED_TASK_RATE,
        )

        tasks.append(task)

        if (i + 1) % 10_000 == 0:
            logger.info(f"  Generated {i + 1}/{total_tasks} tasks")

    db.insert_dicts("tasks", tasks)
    logger.info(f"Generated {len(tasks)} tasks")

    return {t["task_id"]: t for t in tasks}


# -------------------------------------------------------------------
# Task Generation (Single Task)
# -------------------------------------------------------------------

def _generate_single_task(
    scraper,
    project: Dict,
    users: Dict[str, Dict],
    user_ids: List[str],
    managers: set,
    history_start: datetime,
    current_time: datetime,
    completion_rates: Dict[str, Tuple[float, float]],
    day_weights: List[float],
    unassigned_rate: float,
) -> Dict:

    proj_created = datetime.strptime(project["created_at"], "%Y-%m-%d %H:%M:%S")
    proj_due = datetime.strptime(project["due_date"], "%Y-%m-%d").date()

    org_users = [
        uid for uid in user_ids
        if users[uid]["organization_id"] == project["organization_id"]
    ]
    org_managers = [uid for uid in org_users if uid in managers]
    org_non_managers = [uid for uid in org_users if uid not in managers]

    assignee = _pick_assignee(org_users, org_non_managers, unassigned_rate)
    creator = _pick_creator(org_users, org_managers, assignee)

    created_at = _task_created_at(
        start=max(proj_created, history_start),
        end=min(current_time, datetime.combine(proj_due, datetime.max.time())),
        day_weights=day_weights,
    )

    is_completed, completed_at, completed_by = _completion_state(
        project_type=project["project_type"],
        created_at=created_at,
        assignee=assignee,
        creator=creator,
        completion_rates=completion_rates,
        current_time=current_time,
    )

    due_date = _due_date(created_at, proj_due)

    updated_at = _updated_at(
        created_at=created_at,
        completed_at=completed_at,
        current_time=current_time,
    )

    return {
        "task_id": generate_uuid(),
        "organization_id": project["organization_id"],
        "name": _task_name(scraper.github_patterns, project["project_type"]),
        "description": _task_description(),
        "assignee_id": assignee,
        "parent_task_id": None,
        "is_completed": is_completed,
        "completed_at": completed_at.strftime("%Y-%m-%d %H:%M:%S") if completed_at else None,
        "completed_by_id": completed_by,
        "due_date": due_date.strftime("%Y-%m-%d") if due_date else None,
        "due_time": None,
        "start_date": created_at.date().strftime("%Y-%m-%d"),
        "is_milestone": random.random() < 0.03,
        "priority": random.choices(
            ["low", "medium", "high", "urgent"],
            weights=[0.2, 0.45, 0.25, 0.1]
        )[0],
        "estimated_hours": random.choice([None, 2, 4, 8]) if random.random() < 0.3 else None,
        "actual_hours": None,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "created_by_id": creator,
        "num_likes": random.choices([0, 1, 2, 3], weights=[0.7, 0.15, 0.1, 0.05])[0],
    }


# -------------------------------------------------------------------
# Lifecycle Helpers
# -------------------------------------------------------------------

def _pick_assignee(org_users, non_managers, unassigned_rate):
    if random.random() < unassigned_rate:
        return None
    return random.choice(non_managers or org_users)


def _pick_creator(org_users, managers, assignee):
    if random.random() < 0.7 and managers:
        return random.choice(managers)
    return assignee or random.choice(org_users)


def _task_created_at(start: datetime, end: datetime, day_weights: List[float]) -> datetime:
    delta = (end - start).total_seconds()
    dt = start + timedelta(seconds=random.random() * delta)

    if random.random() > day_weights[dt.weekday()]:
        dt += timedelta(days=random.choice([-2, -1, 0, 1]))

    return max(start, min(end, dt))


def _completion_state(
    project_type: str,
    created_at: datetime,
    assignee: Optional[str],
    creator: str,
    completion_rates: Dict[str, Tuple[float, float]],
    current_time: datetime,
) -> Tuple[bool, Optional[datetime], Optional[str]]:

    rate = completion_rates.get(project_type, (0.5, 0.7))
    is_completed = random.random() < random.uniform(*rate)

    if not is_completed:
        return False, None, None

    days = min(14, random.lognormvariate(1.1, 0.8))
    completed_at = created_at + timedelta(days=days)

    completed_at = min(completed_at, current_time)
    if completed_at <= created_at:
        completed_at = created_at + timedelta(hours=random.randint(1, 24))

    return True, completed_at, assignee or creator


def _updated_at(
    created_at: datetime,
    completed_at: Optional[datetime],
    current_time: datetime,
) -> datetime:

    if completed_at:
        return completed_at

    age_days = max((current_time - created_at).total_seconds() / 86400, 0)
    offset = (random.random() ** 2) * min(age_days, 30)

    return min(current_time, created_at + timedelta(days=offset))


# -------------------------------------------------------------------
# Content Generators
# -------------------------------------------------------------------

def _task_name(patterns: Dict, project_type: str) -> str:
    # Safety fallbacks (in case cache is empty or corrupted)
    components = patterns.get("components", []) or ["API"]
    features = patterns.get("features", []) or ["authentication"]
    errors = patterns.get("errors", []) or ["timeout"]
    qualities = patterns.get("qualities", []) or ["performance"]
    technologies = patterns.get("technologies", []) or ["Backend"]


    def fill(template: str) -> str:
        return template.format(
            component=random.choice(components),
            feature=random.choice(features),
            error=random.choice(errors),
            quality=random.choice(qualities),
            technology=random.choice(technologies),
            action=random.choice(["processing requests", "saving data", "loading page"]),
            condition=random.choice(["high load", "invalid input", "edge cases"]),
            platform=random.choice(["Linux", "Windows", "production"]),
            dependency=random.choice(technologies),
            result=random.choice(["results", "response", "data"]),
            expected_behavior=random.choice(["work correctly", "return results"]),
            scope=random.choice(["api", "ui", "core"]),
        )

    if project_type in {"sprint", "cross_functional"}:
        kind = random.choices(["bug", "refactor", "feature"], [0.4, 0.3, 0.3])[0]
    elif project_type == "campaign":
        templates = [
            "Draft content for Q{q} campaign",
            "Design assets for Q{q} launch",
            "Review messaging for Q{q} campaign",
            "Schedule social posts for Q{q}",
        ]
        return random.choice(templates).format(q=random.randint(1, 4))
    else:
        return "Operational follow-up"

    if kind == "bug":
        return fill(random.choice(patterns["bugs"]))
    if kind == "refactor":
        return fill(random.choice(patterns["refactors"]))
    return f"Implement {random.choice(features)} for {random.choice(components)}"

def _task_description() -> Optional[str]:
    roll = random.random()
    if roll < 0.20:
        return None
    if roll < 0.70:
        return random.choice([
            "Complete per sprint goals.",
            "High priority.",
            "See documentation for details."
        ])
    return (
        "Complete this task.\n\n"
        "**Acceptance Criteria:**\n"
        "- [ ] Functionality implemented\n"
        "- [ ] Tests passing\n"
        "- [ ] Reviewed and approved"
    )


def _due_date(created_at: datetime, project_due: date) -> Optional[date]:
    roll = random.random()

    if roll < 0.10:
        return None

    if roll < 0.15:
        due = created_at.date() - timedelta(days=random.randint(1, 14))
    elif roll < 0.40:
        due = created_at.date() + timedelta(days=random.randint(1, 7))
        due = avoid_weekends(due)
    elif roll < 0.80:
        due = created_at.date() + timedelta(days=random.randint(8, 30))
        due = avoid_weekends(due)
    else:
        due = created_at.date() + timedelta(days=random.randint(31, 90))
        due = avoid_weekends(due)

    # makiing sure that task due date is before project due date
    return min(due, project_due)
