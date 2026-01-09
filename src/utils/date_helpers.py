"""
Date and time generation utilities.
Handles realistic temporal patterns for Asana data.
"""

import random
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import math


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