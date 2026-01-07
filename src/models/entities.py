"""
Data models for Asana simulation entities.
Uses dataclasses for clean, type-hinted entity definitions.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


class DepartmentType(Enum):
    """Department workflow types."""
    ENGINEERING = "sprint_based"
    MARKETING = "campaign_based"
    SALES_HR_CS = "process_driven"
    MANAGEMENT = "oversight"


class ProjectType(Enum):
    """Project types mapped to departments."""
    SPRINT = "sprint"
    CAMPAIGN = "campaign"
    PROCESS = "process"
    CROSS_FUNCTIONAL = "cross_functional"
    OVERSIGHT = "oversight"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ApprovalStatus(Enum):
    """Approval workflow statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


@dataclass
class Organization:
    """Top-level organization/workspace."""
    organization_id: str
    name: str
    domain: str
    created_at: datetime
    is_organization: bool = True


@dataclass
class Department:
    """Department within organization."""
    department_id: str
    organization_id: str
    name: str
    description: Optional[str]
    user_percentage: float
    workflow_type: str
    created_at: datetime


@dataclass
class Team:
    """Team within a department."""
    team_id: str
    organization_id: str
    department_id: str
    name: str
    description: Optional[str]
    created_at: datetime


@dataclass
class User:
    """User/employee in the organization."""
    user_id: str
    organization_id: str
    email: str
    first_name: str
    last_name: str
    job_title: Optional[str]
    department_id: str
    is_manager: bool
    is_active: bool
    created_at: datetime
    last_active_at: Optional[datetime]
    profile_photo_url: Optional[str]


@dataclass
class TeamMembership:
    """User membership in a team."""
    membership_id: str
    team_id: str
    user_id: str
    role: str  # member, lead, admin
    is_primary_team: bool
    joined_at: datetime


@dataclass
class Project:
    """Project container for tasks."""
    project_id: str
    organization_id: str
    team_id: str
    name: str
    description: Optional[str]
    color: Optional[str]
    is_archived: bool
    is_public: bool
    project_type: str
    start_date: Optional[date]
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[str]


@dataclass
class ProjectMembership:
    """User membership in a project."""
    project_membership_id: str
    project_id: str
    user_id: str
    role: str  # owner, editor, commenter, member
    added_at: datetime


@dataclass
class Section:
    """Section within a project."""
    section_id: str
    project_id: str
    name: str
    position: int
    created_at: datetime


@dataclass
class Task:
    """Core task entity."""
    task_id: str
    organization_id: str
    name: str
    description: Optional[str]
    assignee_id: Optional[str]
    parent_task_id: Optional[str]
    is_completed: bool
    completed_at: Optional[datetime]
    completed_by_id: Optional[str]
    due_date: Optional[date]
    due_time: Optional[str]
    start_date: Optional[date]
    is_milestone: bool
    priority: Optional[str]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[str]
    num_likes: int = 0


@dataclass
class TaskProject:
    """Association between task and project (multi-homing)."""
    task_project_id: str
    task_id: str
    project_id: str
    section_id: Optional[str]
    position: int
    added_at: datetime


@dataclass
class TaskDependency:
    """Dependency between tasks."""
    dependency_id: str
    blocking_task_id: str
    blocked_task_id: str
    created_at: datetime
    created_by_id: Optional[str]


@dataclass
class Comment:
    """Comment on a task."""
    comment_id: str
    task_id: str
    author_id: str
    content: str
    comment_type: str  # comment, system
    is_edited: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class CustomFieldDefinition:
    """Custom field definition."""
    custom_field_id: str
    organization_id: str
    name: str
    field_type: str  # enum, number, text, date, people
    description: Optional[str]
    is_global: bool
    created_at: datetime


@dataclass
class CustomFieldEnumOption:
    """Enum option for custom fields."""
    option_id: str
    custom_field_id: str
    name: str
    color: Optional[str]
    position: int
    is_enabled: bool = True


@dataclass
class ProjectCustomField:
    """Custom field attached to project."""
    project_custom_field_id: str
    project_id: str
    custom_field_id: str
    is_required: bool


@dataclass
class CustomFieldValue:
    """Value of custom field on a task."""
    value_id: str
    task_id: str
    custom_field_id: str
    text_value: Optional[str] = None
    number_value: Optional[float] = None
    date_value: Optional[date] = None
    enum_option_id: Optional[str] = None
    people_value_user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Tag:
    """Organization-wide tag."""
    tag_id: str
    organization_id: str
    name: str
    color: Optional[str]
    created_at: datetime


@dataclass
class TaskTag:
    """Tag applied to task."""
    task_tag_id: str
    task_id: str
    tag_id: str
    added_at: datetime
    added_by_id: Optional[str]


@dataclass
class Attachment:
    """File attachment on task."""
    attachment_id: str
    task_id: str
    name: str
    file_type: Optional[str]
    file_size_bytes: Optional[int]
    url: Optional[str]
    uploaded_by_id: str
    created_at: datetime


@dataclass
class TaskFollower:
    """User following a task."""
    follower_id: str
    task_id: str
    user_id: str
    followed_at: datetime


@dataclass
class TaskLike:
    """Like on a task."""
    like_id: str
    task_id: str
    user_id: str
    liked_at: datetime


@dataclass
class Approval:
    """Approval request on task."""
    approval_id: str
    task_id: str
    requester_id: str
    approver_id: str
    status: str  # pending, approved, rejected, changes_requested
    requested_at: datetime
    responded_at: Optional[datetime]
    response_comment: Optional[str]