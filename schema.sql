-- ============================================
-- ASANA SEED DATABASE SCHEMA FOR RL 
-- ============================================
-- Designed for: B2B SaaS Company (5,000-10,000 employees)
-- Database: SQLite
-- ============================================

-- ============================================
-- ORGANIZATION & WORKSPACE
-- ============================================

CREATE TABLE organizations (
    organization_id TEXT PRIMARY KEY,              -- UUID, simulates Asana GID
    name TEXT NOT NULL,                            
    domain TEXT UNIQUE,                            
    created_at TIMESTAMP NOT NULL,
    is_organization BOOLEAN DEFAULT TRUE           -- TRUE = organization (verified domain), FALSE = workspace
);

-- ============================================
-- DEPARTMENTS
-- ============================================
-- Note: Asana doesn't have "departments" natively, but we model this
-- as a logical grouping above teams for our simulation

CREATE TABLE departments (
    department_id TEXT PRIMARY KEY,                -- UUID
    organization_id TEXT NOT NULL,
    name TEXT NOT NULL,                            -- "Product Engineering", "Marketing", "Sales/HR/CS", "Upper Management"
    description TEXT,
    user_percentage REAL NOT NULL,                 -- Target % of users (0.40, 0.15, 0.35, 0.10)
    workflow_type TEXT NOT NULL,                   -- "sprint_based", "campaign_based", "process_driven", "oversight"
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

-- ============================================
-- TEAMS
-- ============================================

CREATE TABLE teams (
    team_id TEXT PRIMARY KEY,                      -- UUID
    organization_id TEXT NOT NULL,
    department_id TEXT NOT NULL,
    name TEXT NOT NULL,                            -- e.g., "Backend Infrastructure", "Content Marketing"
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- ============================================
-- USERS
-- ============================================

CREATE TABLE users (
    user_id TEXT PRIMARY KEY,                      -- UUID
    organization_id TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,                    -- firstname.lastname@domain.com
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    job_title TEXT,                                -- e.g., "Senior Software Engineer", "Marketing Manager"
    department_id TEXT NOT NULL,                   -- Primary department
    is_manager BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP,
    profile_photo_url TEXT,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- ============================================
-- TEAM MEMBERSHIPS (Many-to-Many)
-- ============================================
-- Users can belong to multiple teams (cross-functional)

CREATE TABLE team_memberships (
    membership_id TEXT PRIMARY KEY,                -- UUID
    team_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT DEFAULT 'member',                    -- "member", "lead", "admin"
    is_primary_team BOOLEAN DEFAULT FALSE,         -- User's main team
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(team_id, user_id)                       -- User can only be in a team once
);

-- ============================================
-- PROJECTS
-- ============================================

CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,                   -- UUID
    organization_id TEXT NOT NULL,
    team_id TEXT NOT NULL,                         -- Primary owning team
    name TEXT NOT NULL,                            -- e.g., "Q1 Product Launch - Mobile App"
    description TEXT,
    color TEXT,                                    -- Asana project color
    is_archived BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT TRUE,                -- Visible to organization
    project_type TEXT NOT NULL,                    -- "sprint", "campaign", "process", "cross_functional", "oversight"
    start_date DATE,
    due_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id TEXT,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (created_by_id) REFERENCES users(user_id)
);

-- ============================================
-- PROJECT MEMBERSHIPS (Many-to-Many)
-- ============================================
-- For cross-functional projects with members from multiple teams

CREATE TABLE project_memberships (
    project_membership_id TEXT PRIMARY KEY,        -- UUID
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT DEFAULT 'member',                    -- "owner", "editor", "commenter", "member"
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(project_id, user_id)
);

-- ============================================
-- SECTIONS
-- ============================================

CREATE TABLE sections (
    section_id TEXT PRIMARY KEY,                   -- UUID
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,                            -- e.g., "Backlog", "In Progress", "Done"
    position INTEGER NOT NULL,                     -- Order within project (0, 1, 2, ...)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- ============================================
-- TASKS
-- ============================================

CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,                      -- UUID
    organization_id TEXT NOT NULL,
    name TEXT NOT NULL,                            -- Task title
    description TEXT,                              -- Rich text description
    assignee_id TEXT,                              -- NULL = unassigned
    parent_task_id TEXT,                           -- NULL = top-level task, otherwise subtask
    
    -- Status
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    completed_by_id TEXT,
    
    -- Dates
    due_date DATE,
    due_time TIME,                                 -- Optional specific time
    start_date DATE,
    
    -- Metadata
    is_milestone BOOLEAN DEFAULT FALSE,
    priority TEXT,                                 -- Custom: "low", "medium", "high", "urgent" (if using custom field)
    estimated_hours REAL,
    actual_hours REAL,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id TEXT,
    
    -- Likes (Asana feature)
    num_likes INTEGER DEFAULT 0,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (assignee_id) REFERENCES users(user_id),
    FOREIGN KEY (parent_task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (completed_by_id) REFERENCES users(user_id),
    FOREIGN KEY (created_by_id) REFERENCES users(user_id)
);

-- ============================================
-- TASK-PROJECT ASSOCIATIONS (Multi-homing)
-- ============================================
-- A task can appear in MULTIPLE projects (critical Asana feature)
-- Example: Bug escalation appears in both "Sales - Acme Corp" and "Eng - Bug Triage"

CREATE TABLE task_projects (
    task_project_id TEXT PRIMARY KEY,              -- UUID
    task_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    section_id TEXT,                               -- Position within project
    position INTEGER DEFAULT 0,                    -- Order within section
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (section_id) REFERENCES sections(section_id),
    UNIQUE(task_id, project_id)                    -- Task can only be in a project once
);

-- ============================================
-- TASK DEPENDENCIES
-- ============================================
-- Task A blocks Task B (must complete A before B)
-- Example: "Deploy to Production" blocks "Publish Blog Post"

CREATE TABLE task_dependencies (
    dependency_id TEXT PRIMARY KEY,                -- UUID
    blocking_task_id TEXT NOT NULL,                -- This task blocks...
    blocked_task_id TEXT NOT NULL,                 -- ...this task
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id TEXT,
    FOREIGN KEY (blocking_task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (blocked_task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (created_by_id) REFERENCES users(user_id),
    UNIQUE(blocking_task_id, blocked_task_id),
    CHECK(blocking_task_id != blocked_task_id)     -- Can't block itself
);

-- ============================================
-- COMMENTS / STORIES
-- ============================================
-- Asana calls these "stories" - includes both comments and system events

CREATE TABLE comments (
    comment_id TEXT PRIMARY KEY,                   -- UUID
    task_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    content TEXT NOT NULL,                         -- Comment text (can include @mentions)
    comment_type TEXT DEFAULT 'comment',           -- "comment", "system" (auto-generated)
    is_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (author_id) REFERENCES users(user_id)
);

-- ============================================
-- CUSTOM FIELD DEFINITIONS
-- ============================================
-- Project-level or org-level custom fields

CREATE TABLE custom_field_definitions (
    custom_field_id TEXT PRIMARY KEY,              -- UUID
    organization_id TEXT NOT NULL,
    name TEXT NOT NULL,                            -- e.g., "Priority", "Effort", "Sprint"
    field_type TEXT NOT NULL,                      -- "enum", "number", "text", "date", "people"
    description TEXT,
    is_global BOOLEAN DEFAULT FALSE,               -- Available org-wide vs project-specific
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

-- ============================================
-- CUSTOM FIELD ENUM OPTIONS
-- ============================================
-- For enum-type custom fields, define the options

CREATE TABLE custom_field_enum_options (
    option_id TEXT PRIMARY KEY,                    -- UUID
    custom_field_id TEXT NOT NULL,
    name TEXT NOT NULL,                            -- e.g., "Low", "Medium", "High"
    color TEXT,                                    -- Display color
    position INTEGER NOT NULL,                     -- Order in dropdown
    is_enabled BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (custom_field_id) REFERENCES custom_field_definitions(custom_field_id)
);

-- ============================================
-- PROJECT CUSTOM FIELDS
-- ============================================
-- Links custom fields to projects

CREATE TABLE project_custom_fields (
    project_custom_field_id TEXT PRIMARY KEY,      -- UUID
    project_id TEXT NOT NULL,
    custom_field_id TEXT NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (custom_field_id) REFERENCES custom_field_definitions(custom_field_id),
    UNIQUE(project_id, custom_field_id)
);

-- ============================================
-- CUSTOM FIELD VALUES
-- ============================================
-- Actual values assigned to tasks

CREATE TABLE custom_field_values (
    value_id TEXT PRIMARY KEY,                     -- UUID
    task_id TEXT NOT NULL,
    custom_field_id TEXT NOT NULL,
    -- Store value based on type (only one will be populated)
    text_value TEXT,
    number_value REAL,
    date_value DATE,
    enum_option_id TEXT,                           -- FK to custom_field_enum_options
    people_value_user_id TEXT,                     -- FK to users (for people fields)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (custom_field_id) REFERENCES custom_field_definitions(custom_field_id),
    FOREIGN KEY (enum_option_id) REFERENCES custom_field_enum_options(option_id),
    FOREIGN KEY (people_value_user_id) REFERENCES users(user_id),
    UNIQUE(task_id, custom_field_id)               -- One value per field per task
);

-- ============================================
-- TAGS
-- ============================================
-- Organization-wide labels

CREATE TABLE tags (
    tag_id TEXT PRIMARY KEY,                       -- UUID
    organization_id TEXT NOT NULL,
    name TEXT NOT NULL,                            -- e.g., "Urgent", "Blocked", "Customer-Facing"
    color TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

-- ============================================
-- TASK TAGS (Many-to-Many)
-- ============================================

CREATE TABLE task_tags (
    task_tag_id TEXT PRIMARY KEY,                  -- UUID
    task_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    added_by_id TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id),
    FOREIGN KEY (added_by_id) REFERENCES users(user_id),
    UNIQUE(task_id, tag_id)
);

-- ============================================
-- ATTACHMENTS
-- ============================================

CREATE TABLE attachments (
    attachment_id TEXT PRIMARY KEY,                -- UUID
    task_id TEXT NOT NULL,
    name TEXT NOT NULL,                            -- Filename
    file_type TEXT,                                -- MIME type or extension
    file_size_bytes INTEGER,
    url TEXT,                                      -- Simulated URL
    uploaded_by_id TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (uploaded_by_id) REFERENCES users(user_id)
);

-- ============================================
-- TASK FOLLOWERS
-- ============================================
-- Users following a task (get notifications)

CREATE TABLE task_followers (
    follower_id TEXT PRIMARY KEY,                  -- UUID
    task_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    followed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(task_id, user_id)
);

-- ============================================
-- TASK LIKES
-- ============================================
-- Users who liked a task

CREATE TABLE task_likes (
    like_id TEXT PRIMARY KEY,                      -- UUID
    task_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    liked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(task_id, user_id)
);

-- ============================================
-- APPROVALS (For Upper Management Workflows)
-- ============================================
-- Tracks approval requests and responses

CREATE TABLE approvals (
    approval_id TEXT PRIMARY KEY,                  -- UUID
    task_id TEXT NOT NULL,
    requester_id TEXT NOT NULL,                    -- Who requested approval
    approver_id TEXT NOT NULL,                     -- Who needs to approve (manager)
    status TEXT DEFAULT 'pending',                 -- "pending", "approved", "rejected", "changes_requested"
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    response_comment TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (requester_id) REFERENCES users(user_id),
    FOREIGN KEY (approver_id) REFERENCES users(user_id)
);

