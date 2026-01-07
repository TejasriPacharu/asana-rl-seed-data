"""
Validators for temporal and relational consistency.
Ensures generated data meets all consistency rules.
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class ConsistencyValidator:
    """Validates temporal and relational consistency of generated data."""
    
    def __init__(self):
        """Initialize validator with tracking sets."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def reset(self):
        """Reset error and warning lists."""
        self.errors = []
        self.warnings = []
    
    # =========================================================================
    # TEMPORAL CONSISTENCY VALIDATORS
    # =========================================================================
    
    def validate_datetime_order(
        self,
        earlier: datetime,
        later: datetime,
        earlier_name: str,
        later_name: str,
        entity_id: str
    ) -> bool:
        """Validate that earlier datetime comes before later datetime.
        
        Args:
            earlier: The datetime that should be earlier
            later: The datetime that should be later
            earlier_name: Name of earlier field
            later_name: Name of later field
            entity_id: ID of entity for error message
            
        Returns:
            True if valid
        """
        if earlier and later and earlier > later:
            self.errors.append(
                f"TC Error [{entity_id}]: {earlier_name} ({earlier}) is after {later_name} ({later})"
            )
            return False
        return True
    
    def validate_not_future(
        self,
        dt: datetime,
        field_name: str,
        entity_id: str,
        reference_time: Optional[datetime] = None
    ) -> bool:
        """Validate datetime is not in the future.
        
        Args:
            dt: Datetime to validate
            field_name: Name of field
            entity_id: ID of entity
            reference_time: Reference time (defaults to now)
            
        Returns:
            True if valid
        """
        reference = reference_time or datetime.now()
        if dt and dt > reference:
            self.errors.append(
                f"TC Error [{entity_id}]: {field_name} ({dt}) is in the future"
            )
            return False
        return True
    
    def validate_task_temporal(
        self,
        task_id: str,
        created_at: datetime,
        completed_at: Optional[datetime],
        updated_at: datetime,
        due_date: Optional[date],
        start_date: Optional[date]
    ) -> bool:
        """Validate task temporal consistency.
        
        Rules:
        - TC-1: completed_at > created_at
        - TC-4: completed_at <= NOW
        - TC-5: updated_at >= created_at
        - TC-6: if completed, updated_at >= completed_at
        - TC-3: start_date <= due_date
        
        Returns:
            True if all validations pass
        """
        valid = True
        
        # TC-1: Can't complete before creation
        if completed_at:
            valid &= self.validate_datetime_order(
                created_at, completed_at, "created_at", "completed_at", task_id
            )
        
        # TC-4: Can't complete in future
        if completed_at:
            valid &= self.validate_not_future(completed_at, "completed_at", task_id)
        
        # TC-5: updated_at >= created_at
        valid &= self.validate_datetime_order(
            created_at, updated_at, "created_at", "updated_at", task_id
        )
        
        # TC-6: if completed, updated_at >= completed_at
        if completed_at:
            valid &= self.validate_datetime_order(
                completed_at, updated_at, "completed_at", "updated_at", task_id
            )
        
        # TC-3: start_date <= due_date
        if start_date and due_date and start_date > due_date:
            self.errors.append(
                f"TC Error [{task_id}]: start_date ({start_date}) is after due_date ({due_date})"
            )
            valid = False
        
        return valid
    
    def validate_comment_temporal(
        self,
        comment_id: str,
        comment_created_at: datetime,
        task_created_at: datetime
    ) -> bool:
        """Validate comment temporal consistency.
        
        Rule TC-7: comment.created_at >= task.created_at
        """
        return self.validate_datetime_order(
            task_created_at, comment_created_at,
            "task.created_at", "comment.created_at", comment_id
        )
    
    def validate_membership_temporal(
        self,
        membership_id: str,
        joined_at: datetime,
        user_created_at: datetime,
        entity_created_at: datetime,
        entity_type: str
    ) -> bool:
        """Validate membership temporal consistency.
        
        Rules:
        - TC-18/20: joined_at >= user.created_at
        - TC-19/21: joined_at >= team/project.created_at
        """
        valid = True
        
        valid &= self.validate_datetime_order(
            user_created_at, joined_at,
            "user.created_at", "joined_at", membership_id
        )
        
        valid &= self.validate_datetime_order(
            entity_created_at, joined_at,
            f"{entity_type}.created_at", "joined_at", membership_id
        )
        
        return valid
    
    def validate_approval_temporal(
        self,
        approval_id: str,
        requested_at: datetime,
        responded_at: Optional[datetime],
        task_created_at: datetime,
        status: str
    ) -> bool:
        """Validate approval temporal consistency.
        
        Rules:
        - TC-22: requested_at >= task.created_at
        - TC-23: responded_at >= requested_at
        - TC-24: responded_at is NULL if status = pending
        """
        valid = True
        
        # TC-22
        valid &= self.validate_datetime_order(
            task_created_at, requested_at,
            "task.created_at", "requested_at", approval_id
        )
        
        # TC-23
        if responded_at:
            valid &= self.validate_datetime_order(
                requested_at, responded_at,
                "requested_at", "responded_at", approval_id
            )
        
        # TC-24
        if status == "pending" and responded_at is not None:
            self.errors.append(
                f"TC Error [{approval_id}]: pending approval should not have responded_at"
            )
            valid = False
        
        return valid
    
    # =========================================================================
    # RELATIONAL CONSISTENCY VALIDATORS
    # =========================================================================
    
    def validate_foreign_key(
        self,
        fk_value: Optional[str],
        valid_ids: Set[str],
        fk_name: str,
        entity_id: str,
        allow_null: bool = True
    ) -> bool:
        """Validate foreign key reference.
        
        Args:
            fk_value: Foreign key value to validate
            valid_ids: Set of valid IDs
            fk_name: Name of FK field
            entity_id: ID of entity
            allow_null: Whether NULL is allowed
            
        Returns:
            True if valid
        """
        if fk_value is None:
            if not allow_null:
                self.errors.append(
                    f"RC Error [{entity_id}]: {fk_name} cannot be NULL"
                )
                return False
            return True
        
        if fk_value not in valid_ids:
            self.errors.append(
                f"RC Error [{entity_id}]: {fk_name} '{fk_value}' not found in valid IDs"
            )
            return False
        
        return True
    
    def validate_section_belongs_to_project(
        self,
        task_project_id: str,
        section_id: Optional[str],
        project_id: str,
        section_project_map: Dict[str, str]
    ) -> bool:
        """Validate section belongs to project (RC-2).
        
        Args:
            task_project_id: Task-project association ID
            section_id: Section ID
            project_id: Project ID
            section_project_map: Map of section_id to project_id
            
        Returns:
            True if valid
        """
        if section_id is None:
            return True
        
        actual_project = section_project_map.get(section_id)
        if actual_project != project_id:
            self.errors.append(
                f"RC Error [{task_project_id}]: Section {section_id} belongs to project "
                f"{actual_project}, not {project_id}"
            )
            return False
        
        return True
    
    def validate_one_primary_team(
        self,
        user_id: str,
        memberships: List[Dict]
    ) -> bool:
        """Validate user has exactly one primary team (RC-8).
        
        Args:
            user_id: User ID
            memberships: List of user's team memberships
            
        Returns:
            True if valid
        """
        primary_count = sum(1 for m in memberships if m.get("is_primary_team"))
        
        if primary_count != 1:
            self.errors.append(
                f"RC Error [{user_id}]: User has {primary_count} primary teams, expected 1"
            )
            return False
        
        return True
    
    def validate_one_project_owner(
        self,
        project_id: str,
        memberships: List[Dict]
    ) -> bool:
        """Validate project has exactly one owner (RC-9).
        
        Args:
            project_id: Project ID
            memberships: List of project memberships
            
        Returns:
            True if valid
        """
        owner_count = sum(1 for m in memberships if m.get("role") == "owner")
        
        if owner_count != 1:
            self.errors.append(
                f"RC Error [{project_id}]: Project has {owner_count} owners, expected 1"
            )
            return False
        
        return True
    
    def validate_no_self_dependency(
        self,
        dependency_id: str,
        blocking_task_id: str,
        blocked_task_id: str
    ) -> bool:
        """Validate task doesn't depend on itself (RC-14).
        
        Returns:
            True if valid
        """
        if blocking_task_id == blocked_task_id:
            self.errors.append(
                f"RC Error [{dependency_id}]: Task cannot depend on itself"
            )
            return False
        return True
    
    def validate_completed_task_in_done_section(
        self,
        task_id: str,
        is_completed: bool,
        section_name: str
    ) -> bool:
        """Validate completed tasks are in Done section (RC-6).
        
        Note: This is a soft validation - generates warning not error.
        
        Returns:
            True always (warnings only)
        """
        if is_completed and section_name and "done" not in section_name.lower():
            self.warnings.append(
                f"RC Warning [{task_id}]: Completed task not in 'Done' section ({section_name})"
            )
        
        return True
    
    def validate_manager_is_manager(
        self,
        approval_id: str,
        approver_id: str,
        managers: Set[str]
    ) -> bool:
        """Validate approver is a manager (RC-13).
        
        Returns:
            True if valid
        """
        if approver_id not in managers:
            self.errors.append(
                f"RC Error [{approval_id}]: Approver {approver_id} is not a manager"
            )
            return False
        return True
    
    def validate_custom_field_value(
        self,
        value_id: str,
        text_value: Optional[str],
        number_value: Optional[float],
        date_value: Optional[date],
        enum_option_id: Optional[str],
        people_value_user_id: Optional[str]
    ) -> bool:
        """Validate only one value column is populated (RC-11).
        
        Returns:
            True if valid
        """
        values = [text_value, number_value, date_value, enum_option_id, people_value_user_id]
        populated = sum(1 for v in values if v is not None)
        
        if populated > 1:
            self.errors.append(
                f"RC Error [{value_id}]: Multiple value columns populated ({populated})"
            )
            return False
        
        return True
    
    # =========================================================================
    # BATCH VALIDATION
    # =========================================================================
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results.
        
        Returns:
            Dictionary with error and warning counts and lists
        """
        return {
            "valid": len(self.errors) == 0,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors[:20],  # First 20 errors
            "warnings": self.warnings[:20],  # First 20 warnings
        }
    
    def print_summary(self):
        """Print validation summary to log."""
        summary = self.get_validation_summary()
        
        if summary["valid"]:
            logger.info("✓ All validations passed!")
        else:
            logger.error(f"✗ Validation failed with {summary['error_count']} errors")
            for error in summary["errors"]:
                logger.error(f"  {error}")
        
        if summary["warning_count"] > 0:
            logger.warning(f"⚠ {summary['warning_count']} warnings")
            for warning in summary["warnings"][:5]:
                logger.warning(f"  {warning}")


def detect_circular_dependencies(
    dependencies: List[Tuple[str, str]]
) -> List[List[str]]:
    """Detect circular dependencies in task dependency graph.
    
    Args:
        dependencies: List of (blocking_task_id, blocked_task_id) tuples
        
    Returns:
        List of circular dependency chains (empty if none found)
    """
    # Build adjacency list
    graph: Dict[str, List[str]] = {}
    for blocking, blocked in dependencies:
        if blocking not in graph:
            graph[blocking] = []
        graph[blocking].append(blocked)
    
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node: str, path: List[str]) -> bool:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor, path):
                    return True
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
                return True
        
        path.pop()
        rec_stack.remove(node)
        return False
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles