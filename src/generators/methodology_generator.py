"""
Asana Data Generator - Main Orchestrator

Orchestrates data generation using separate generator modules.
Ensures temporal and relational consistency across all entities.
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.scrapers.real_data_scraper import RealDataScraper
from src.utils.database import Database

from src.generators.organizations import generate_organizations
from src.generators.departments import generate_departments
from src.generators.users import generate_users
from src.generators.teams import generate_teams
from src.generators.team_memberships import generate_team_memberships
from src.generators.projects import generate_projects
from src.generators.tasks import generate_tasks

logger = logging.getLogger(__name__)


class MethodologyBasedGenerator:
    """
    Main data generator orchestrator.
    
    Coordinates generation of all entities with proper temporal and relational consistency.
    """
    
    # Research-backed constants
    TWO_WEEK_SPRINT_RATE = 0.591  # 59.1% use 2-week sprints (Parabol research)
    UNASSIGNED_TASK_RATE = 0.15  # 15% of tasks unassigned (Asana benchmark)
    DAY_WEIGHTS = [0.85, 0.95, 0.90, 0.75, 0.65, 0.20, 0.15]  # Mon-Sun
    
    # Completion rates by project type
    COMPLETION_RATES = {
        "sprint": (0.70, 0.85),
        "campaign": (0.60, 0.75),
        "process": (0.40, 0.50),
        "cross_functional": (0.55, 0.70),
        "oversight": (0.50, 0.65),
    }
    
    def __init__(
        self,
        num_users: int = 5000,
        history_months: int = 6,
        tasks_per_user: int = 10,
        num_organizations: int = 3,
        random_seed: Optional[int] = None
    ):
        """
        Initialize generator.
        
        Args:
            num_users: Total number of users to generate
            history_months: Months of historical data
            tasks_per_user: Average tasks per user
            num_organizations: Number of organizations to generate
            random_seed: Random seed for reproducibility
        """
        self.random_seed = random_seed
        if random_seed:
            random.seed(random_seed)
        
        self.num_users = num_users
        self.history_months = history_months
        self.tasks_per_user = tasks_per_user
        self.num_organizations = num_organizations
        
        # Time boundaries
        self.current_time = datetime.now()
        self.company_created = self.current_time - timedelta(days=365 * 5)
        self.history_start = self.current_time - timedelta(days=history_months * 30)
        
        # Initialize real data scraper
        self.scraper = RealDataScraper()
        self.scraper.load_all()
        
        # Storage for generated entities
        self.organizations: Dict[str, Dict] = {}
        self.departments: Dict[str, Dict] = {}
        self.users: Dict[str, Dict] = {}
        self.users_by_dept: Dict[str, list] = {}
        self.managers: set = set()
        self.teams: Dict[str, Dict] = {}
        self.projects: Dict[str, Dict] = {}
        self.tasks: Dict[str, Dict] = {}
        
        logger.info("Initialized MethodologyBasedGenerator")
        logger.info(f"  Config: {num_organizations} orgs, {num_users} users, {history_months} months, {tasks_per_user} tasks/user")
        logger.info(f"  Random seed: {random_seed or 'None (random)'}")
    
    def generate_all(self, db: Database) -> Dict[str, int]:
        """
        Generate all data in dependency order.
        
        Temporal Consistency Rules:
        1. Users created_at >= organization created_at
        2. Users last_active_at between created_at and current_time
        3. Teams created_at >= organization created_at
        4. Projects created_at >= team created_at
        5. Projects start_date = created_at
        6. Projects due_date >= start_date
        7. Projects updated_at between start_date and current_time
        8. Tasks created_at >= project created_at
        9. Tasks completed_at >= created_at (if completed)
        10. Tasks updated_at between created_at and current_time
        
        Relational Consistency Rules:
        1. Users belong to organizations (via organization_id)
        2. Users belong to departments (via department_id)
        3. Teams belong to departments and organizations
        4. Projects belong to teams and organizations
        5. Tasks belong to organizations and projects
        6. Team memberships link users to teams
        """
        logger.info("=" * 60)
        logger.info("DATA GENERATION (Full: Organizations, Departments, Users, Teams, Projects, Tasks)")
        logger.info("=" * 60)
        
        counts = {}
        
        # 1. Generate organizations (foundation)
        logger.info("")
        logger.info("STEP 1: Organizations")
        logger.info("-" * 60)
        self.organizations = generate_organizations(
            db=db,
            scraper=self.scraper,
            num_organizations=self.num_organizations,
            company_created=self.company_created,
            random_seed=self.random_seed
        )
        counts["organizations"] = len(self.organizations)
        
        # 2. Generate departments (depend on organizations)
        logger.info("")
        logger.info("STEP 2: Departments")
        logger.info("-" * 60)
        self.departments = generate_departments(
            db=db,
            organizations=self.organizations,
            random_seed=self.random_seed
        )
        counts["departments"] = len(self.departments)
        
        # 3. Generate users (depend on organizations and departments)
        logger.info("")
        logger.info("STEP 3: Users")
        logger.info("-" * 60)
        # #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"id": "log_call_generate_users", "timestamp": int(datetime.now().timestamp() * 1000), "location": "methodology_generator.py:157", "message": "Calling generate_users", "data": {"num_users": self.num_users, "num_orgs": len(self.organizations), "num_depts": len(self.departments)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
        except: pass
        # #endregion
        self.users, self.users_by_dept, self.managers = generate_users(
            db=db,
            scraper=self.scraper,
            organizations=self.organizations,
            departments=self.departments,
            num_users=self.num_users,
            current_time=self.current_time,
            company_created=self.company_created,
            random_seed=self.random_seed
        )
        counts["users"] = len(self.users)
        
        # 4. Generate teams (depend on departments and organizations)
        logger.info("")
        logger.info("STEP 4: Teams")
        logger.info("-" * 60)
        self.teams = generate_teams(
            db=db,
            departments=self.departments,
            organizations=self.organizations,
            users_by_dept=self.users_by_dept,
            random_seed=self.random_seed
        )
        counts["teams"] = len(self.teams)
        
        # 5. Generate team memberships (depend on teams and users)
        logger.info("")
        logger.info("STEP 5: Team Memberships")
        logger.info("-" * 60)
        counts["team_memberships"] = generate_team_memberships(
            db=db,
            teams=self.teams,
            users=self.users,
            users_by_dept=self.users_by_dept,
            random_seed=self.random_seed
        )
        
        # 6. Generate projects (depend on teams, organizations, users)
        logger.info("")
        logger.info("STEP 6: Projects")
        logger.info("-" * 60)
        self.projects = generate_projects(
            db=db,
            teams=self.teams,
            organizations=self.organizations,
            users=self.users,
            managers=self.managers,
            history_start=self.history_start,
            current_time=self.current_time,
            TWO_WEEK_SPRINT_RATE=self.TWO_WEEK_SPRINT_RATE,
            random_seed=self.random_seed
        )
        counts["projects"] = len(self.projects)
        
        # 7. Generate tasks (depend on projects, users, organizations)
        logger.info("")
        logger.info("STEP 7: Tasks")
        logger.info("-" * 60)
        self.tasks = generate_tasks(
            db=db,
            scraper=self.scraper,
            projects=self.projects,
            users=self.users,
            managers=self.managers,
            organizations=self.organizations,
            history_start=self.history_start,
            current_time=self.current_time,
            tasks_per_user=self.tasks_per_user,
            UNASSIGNED_TASK_RATE=self.UNASSIGNED_TASK_RATE,
            COMPLETION_RATES=self.COMPLETION_RATES,
            DAY_WEIGHTS=self.DAY_WEIGHTS,
            random_seed=self.random_seed
        )
        counts["tasks"] = len(self.tasks)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("GENERATION COMPLETE")
        logger.info("=" * 60)
        
        return counts
