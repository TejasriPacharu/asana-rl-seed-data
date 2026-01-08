"""
Date and time generation utilities.
Handles realistic temporal patterns for Asana data.
"""

import random
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import math


def get_simulation_time_range(history_months: int = 6) -> Tuple[datetime, datetime]:
    """Get the simulation time range.
    
    Args:
        history_months: Number of months of history to generate
        
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=history_months * 30)
    return start_date, end_date


def random_datetime_in_range(
    start: datetime,
    end: datetime,
    business_hours_weight: float = 0.7
) -> datetime:
    """Generate random datetime within range.
    
    Args:
        start: Start of range
        end: End of range
        business_hours_weight: Probability of falling in business hours
        
    Returns:
        Random datetime
    """
    # Random date
    delta = end - start
    random_days = random.random() * delta.days
    result_date = start + timedelta(days=random_days)
    
    # Weight towards business hours (9 AM - 6 PM)
    if random.random() < business_hours_weight:
        hour = random.randint(9, 17)
    else:
        hour = random.randint(0, 23)
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return result_date.replace(hour=hour, minute=minute, second=second, microsecond=0)


def random_date_in_range(start: date, end: date) -> date:
    """Generate random date within range.
    
    Args:
        start: Start date
        end: End date
        
    Returns:
        Random date
    """
    delta = (end - start).days
    if delta <= 0:
        return start
    random_days = random.randint(0, delta)
    return start + timedelta(days=random_days)


def weighted_day_of_week(dt: datetime) -> datetime:
    """Adjust datetime to weight towards certain days.
    
    Based on research: Higher task creation Mon-Wed, lower Thu-Fri.
    Tuesdays have highest completion rates.
    
    Args:
        dt: Input datetime
        
    Returns:
        Potentially adjusted datetime
    """
    # Day of week: 0=Monday, 6=Sunday
    day = dt.weekday()
    
    # Weights for each day (Mon-Sun)
    # Higher = more likely to keep
    weights = [0.85, 0.95, 0.90, 0.75, 0.65, 0.20, 0.15]
    
    if random.random() > weights[day]:
        # Shift to a more likely day
        shift = random.choice([-1, 1, 2]) if day > 2 else random.choice([0, 1])
        new_day = (day + shift) % 5
        delta = new_day - day
        dt = dt + timedelta(days=delta)
    
    return dt


def avoid_weekends(d: date, probability: float = 0.85) -> date:
    """Adjust date to avoid weekends with given probability.
    
    Args:
        d: Input date
        probability: Probability of avoiding weekends
        
    Returns:
        Adjusted date (moved to Monday if was weekend)
    """
    if random.random() < probability:
        if d.weekday() == 5:
            d = d + timedelta(days=2)
        elif d.weekday() == 6:
            d = d + timedelta(days=1)
    return d


def sprint_boundary_date(
    base_date: date,
    sprint_length_days: int = 14,
    sprint_start_day: int = 0  # Monday
) -> date:
    """Align date to sprint boundary.
    
    Args:
        base_date: Input date
        sprint_length_days: Length of sprint in days (default 14)
        sprint_start_day: Day of week sprint starts (0=Monday)
        
    Returns:
        Date aligned to sprint end
    """
    # Find the next sprint end from base_date
    days_since_sprint_start = (base_date.weekday() - sprint_start_day) % 7
    days_until_sprint_end = sprint_length_days - days_since_sprint_start
    
    if days_until_sprint_end <= 0:
        days_until_sprint_end += sprint_length_days
    
    return base_date + timedelta(days=days_until_sprint_end)


def generate_due_date(
    created_at: datetime,
    project_type: str,
    current_time: Optional[datetime] = None
) -> Optional[date]:
    """Generate realistic due date based on project type.
    
    Distribution based on research:
    - 25% within 1 week
    - 40% within 1 month
    - 20% 1-3 months out
    - 10% no due date
    - 5% overdue (before now)
    
    Args:
        created_at: Task creation timestamp
        project_type: Type of project (sprint, campaign, process)
        current_time: Current time reference
        
    Returns:
        Due date or None
    """
    if current_time is None:
        current_time = datetime.now()
    
    # 10% have no due date
    if random.random() < 0.10:
        return None
    
    roll = random.random()
    
    if roll < 0.05:
        # 5% overdue - due date before now
        days_overdue = random.randint(1, 14)
        due = created_at.date() + timedelta(days=random.randint(1, 7))
        # Ensure it's actually overdue
        due = min(due, current_time.date() - timedelta(days=days_overdue))
    elif roll < 0.30:
        # 25% within 1 week
        due = created_at.date() + timedelta(days=random.randint(1, 7))
    elif roll < 0.70:
        # 40% within 1 month
        due = created_at.date() + timedelta(days=random.randint(8, 30))
    else:
        # 20% 1-3 months out
        due = created_at.date() + timedelta(days=random.randint(31, 90))
    
    # Avoid weekends for 85% of tasks
    due = avoid_weekends(due)
    
    # Align to sprint boundaries for engineering projects
    if project_type == "sprint" and random.random() < 0.7:
        due = sprint_boundary_date(due)
    
    return due


def generate_completion_date(
    created_at: datetime,
    due_date: Optional[date],
    is_completed: bool
) -> Optional[datetime]:
    """Generate completion timestamp.
    
    Follows log-normal distribution with median ~3 days.
    Based on cycle time benchmarks.
    
    Args:
        created_at: Task creation timestamp
        due_date: Task due date (if any)
        is_completed: Whether task is completed
        
    Returns:
        Completion timestamp or None
    """
    if not is_completed:
        return None
    
    # Log-normal distribution for completion time
    # Median ~3 days, can range from hours to 2 weeks
    log_mean = 1.1 
    log_std = 0.8
    
    days_to_complete = random.lognormvariate(log_mean, log_std)
    days_to_complete = min(days_to_complete, 14)  # Cap at 2 weeks
    days_to_complete = max(days_to_complete, 0.1)  # Minimum ~2 hours
    
    completed_at = created_at + timedelta(days=days_to_complete)
    
    # Don't complete in the future
    now = datetime.now()
    if completed_at > now:
        completed_at = now - timedelta(hours=random.randint(1, 48))
    
    return completed_at


def generate_company_history_date(
    company_created: datetime,
    current_time: datetime,
    weight: str = "uniform"
) -> datetime:
    """Generate date within company history.
    
    Args:
        company_created: Company founding date
        current_time: Current time
        weight: Distribution type (uniform, early, recent, growth)
        
    Returns:
        Random date within company history
    """
    total_days = (current_time - company_created).days
    
    if weight == "early":
        # Weighted towards early dates (S-curve start)
        days = int(total_days * (random.random() ** 2))
    elif weight == "recent":
        # Weighted towards recent dates
        days = int(total_days * (1 - (random.random() ** 2)))
    elif weight == "growth":
        # S-curve: sparse early, dense in middle, moderate recent
        x = random.random()
        # Sigmoid-like transformation
        days = int(total_days * (1 / (1 + math.exp(-10 * (x - 0.3)))))
    else:
        # Uniform
        days = random.randint(0, total_days)
    
    return company_created + timedelta(days=days)


def datetime_after(
    base: datetime,
    min_hours: int = 1,
    max_hours: int = 168  # 1 week
) -> datetime:
    """Generate datetime after a base time.
    
    Args:
        base: Base datetime
        min_hours: Minimum hours after base
        max_hours: Maximum hours after base
        
    Returns:
        Datetime after base
    """
    hours = random.randint(min_hours, max_hours)
    result = base + timedelta(hours=hours)
    
    # Don't go into the future
    now = datetime.now()
    if result > now:
        result = now - timedelta(minutes=random.randint(1, 60))
    
    return result


def ensure_after(dt: datetime, reference: datetime) -> datetime:
    """Ensure datetime is after reference.
    
    Args:
        dt: Datetime to check
        reference: Reference datetime
        
    Returns:
        datetime that is guaranteed to be after reference
    """
    if dt <= reference:
        # Add 1 minute to 1 day
        dt = reference + timedelta(minutes=random.randint(1, 1440))
    return dt


def format_datetime(dt: datetime) -> str:
    """Format datetime for SQLite.
    
    Args:
        dt: Datetime to format
        
    Returns:
        ISO format string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_date(d: date) -> str:
    """Format date for SQLite.
    
    Args:
        d: Date to format
        
    Returns:
        ISO format string
    """
    return d.strftime("%Y-%m-%d")