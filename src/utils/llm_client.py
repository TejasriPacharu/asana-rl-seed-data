"""
LLM client for generating realistic text content.
Falls back to template-based generation if LLM is not available.
"""

import os
import random
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Try to import anthropic, but don't fail if not available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic package not installed. Using template-based generation.")


class LLMClient:
    """Client for LLM-based text generation with template fallback."""
    
    def __init__(self, api_key: Optional[str] = None, use_llm: bool = False):
        """Initialize LLM client.
        
        Args:
            api_key: Anthropic API key
            use_llm: Whether to use LLM (False = template-based)
        """
        self.use_llm = use_llm and ANTHROPIC_AVAILABLE and api_key
        self.client = None
        
        if self.use_llm:
            try:
                self.client = anthropic.Anthropic(api_key=api_key)
                logger.info("LLM client initialized with Anthropic API")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                self.use_llm = False
    
    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """Generate text using LLM or templates.
        
        Args:
            prompt: Generation prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if self.use_llm and self.client:
            try:
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                logger.warning(f"LLM generation failed, using template: {e}")
        
        # Template fallback handled by specific methods
        return ""


# =============================================================================
# TEMPLATE-BASED GENERATORS (Used when LLM is not available)
# =============================================================================

# Engineering task name templates
ENGINEERING_TASK_TEMPLATES = {
    "feature": [
        "Implement {component} for {feature}",
        "Add {feature} support to {component}",
        "Create {component} service for {feature}",
        "Build {feature} functionality in {component}",
        "Develop {component} module for {feature}",
        "{component} - Implement {action} for {feature}",
        "Set up {component} integration with {service}",
        "Add {action} capability to {component}",
    ],
    "bug": [
        "[Bug]: {component} fails when {condition}",
        "[Bug]: {error_type} in {component}",
        "Fix {error_type} in {component}",
        "Fix {component} {error_type} issue",
        "Resolve {component} crash on {condition}",
        "[Bug]: {component} returns incorrect {data_type}",
        "Debug {component} {action} failure",
    ],
    "refactor": [
        "Refactor {component} for better {quality}",
        "Clean up {component} code",
        "Migrate {component} to {new_tech}",
        "Update {component} to use {new_tech}",
        "Optimize {component} {action}",
        "Improve {component} {quality}",
    ],
    "devops": [
        "Set up {tool} for {environment}",
        "Configure {tool} in {environment}",
        "Deploy {component} to {environment}",
        "Add {tool} monitoring for {component}",
        "Update {environment} {tool} configuration",
        "Create {tool} pipeline for {component}",
    ],
    "docs": [
        "Document {component} API",
        "Update {component} README",
        "Add documentation for {feature}",
        "Write {component} usage guide",
    ]
}

ENGINEERING_COMPONENTS = [
    "API", "Backend", "Frontend", "Database", "Auth", "User Service",
    "Payment Service", "Notification Service", "Search", "Cache",
    "Queue", "Webhook", "Dashboard", "Admin Panel", "Mobile App",
    "Analytics", "Reporting", "Settings", "Profile", "Onboarding"
]

ENGINEERING_FEATURES = [
    "user authentication", "rate limiting", "pagination", "filtering",
    "sorting", "export functionality", "bulk operations", "SSO integration",
    "two-factor auth", "password reset", "email notifications", "webhooks",
    "API versioning", "caching layer", "search indexing", "file uploads",
    "real-time updates", "audit logging", "role-based access", "data encryption"
]

ENGINEERING_ACTIONS = [
    "implementation", "validation", "processing", "rendering", "loading",
    "saving", "updating", "deletion", "synchronization", "migration"
]

ENGINEERING_ERRORS = [
    "null pointer", "timeout", "memory leak", "race condition",
    "validation error", "connection error", "parsing error", "encoding issue"
]

ENGINEERING_QUALITIES = [
    "performance", "readability", "testability", "maintainability",
    "scalability", "reliability", "security"
]

# Marketing task templates
MARKETING_TASK_TEMPLATES = [
    "Write {content_type} - {campaign}",
    "Create {asset_type} for {campaign}",
    "Design {asset_type} - {campaign}",
    "Review {content_type} with {stakeholder}",
    "Schedule {content_type} for {channel}",
    "Update {asset_type} v{version} - {campaign}",
    "Finalize {content_type} copy for {campaign}",
    "Get approval on {asset_type} from {stakeholder}",
    "Set up {tool} tracking for {campaign}",
    "Coordinate {event_type} logistics",
    "Prepare {content_type} brief for {campaign}",
    "A/B test {asset_type} for {campaign}",
]

MARKETING_CONTENT_TYPES = [
    "blog post", "email", "landing page copy", "social post",
    "press release", "case study", "whitepaper", "newsletter",
    "video script", "podcast outline", "webinar content"
]

MARKETING_ASSET_TYPES = [
    "banner", "email template", "social graphics", "landing page",
    "infographic", "presentation", "video thumbnail", "ad creative",
    "logo variant", "brand guidelines update"
]

MARKETING_CAMPAIGNS = [
    "Q1 Product Launch", "Q2 Product Launch", "Q3 Product Launch", "Q4 Product Launch",
    "Holiday Campaign", "Summer Campaign", "Back to School", "Year-End Review",
    "New Feature Announcement", "Customer Appreciation", "Partner Spotlight",
    "Industry Report", "Annual Conference", "Webinar Series", "Rebrand Initiative"
]

MARKETING_CHANNELS = [
    "LinkedIn", "Twitter", "email", "blog", "YouTube", "Instagram", "website"
]

MARKETING_STAKEHOLDERS = [
    "Product", "Legal", "Executive Team", "Sales", "Customer Success", "Design"
]

# Sales/CS task templates
SALES_TASK_TEMPLATES = [
    "Follow up with {company} - {context}",
    "Send {document} to {company}",
    "Schedule {meeting_type} with {company}",
    "Prepare {document} for {company}",
    "Complete {onboarding_step} for {company}",
    "Conduct {review_type} with {company}",
    "Address {issue_type} for {company}",
    "Update {company} in CRM",
    "Log call notes - {company}",
    "Escalate {issue_type} to {team}",
    "Process {document} for {company}",
    "Train {company} on {feature}",
]

SALES_DOCUMENTS = [
    "proposal", "contract", "pricing sheet", "SOW", "NDA",
    "case study", "ROI analysis", "implementation plan"
]

SALES_MEETING_TYPES = [
    "discovery call", "demo", "technical deep-dive", "executive briefing",
    "QBR", "kickoff call", "check-in", "renewal discussion"
]

SALES_ONBOARDING_STEPS = [
    "data migration", "user provisioning", "SSO setup", "API integration",
    "training session 1", "training session 2", "go-live checklist"
]

SALES_CONTEXTS = [
    "demo follow-up", "proposal review", "next steps", "contract questions",
    "pricing discussion", "feature request", "timeline confirmation"
]

SALES_COMPANIES = [
    "Acme Corp", "TechStart Inc", "Global Systems", "Innovate LLC",
    "Premier Solutions", "NextGen Tech", "Apex Industries", "Quantum Corp",
    "Stellar Dynamics", "Horizon Group", "Pinnacle Partners", "Elevate Co",
    "Synergy Inc", "Vertex Holdings", "Atlas Enterprise", "Momentum Labs"
]

# Management task templates
MANAGEMENT_TASK_TEMPLATES = [
    "Review {item} for Q{quarter}",
    "Approve {request_type} request",
    "Sign off on {item}",
    "Prepare {document} for board",
    "Finalize {item} budget",
    "Review {team} performance",
    "Approve {team} headcount request",
    "Strategic planning - {area}",
    "Quarterly review - {area}",
    "Align on {item} priorities",
]

MANAGEMENT_ITEMS = [
    "roadmap", "budget", "OKRs", "hiring plan", "launch plan",
    "strategy", "vendor contract", "partnership agreement"
]

MANAGEMENT_REQUEST_TYPES = [
    "budget", "headcount", "travel", "vendor", "contract", "policy exception"
]


def generate_engineering_task_name() -> str:
    """Generate realistic engineering task name."""
    task_type = random.choices(
        ["feature", "bug", "refactor", "devops", "docs"],
        weights=[0.45, 0.25, 0.15, 0.10, 0.05]
    )[0]
    
    template = random.choice(ENGINEERING_TASK_TEMPLATES[task_type])
    
    return template.format(
        component=random.choice(ENGINEERING_COMPONENTS),
        feature=random.choice(ENGINEERING_FEATURES),
        action=random.choice(ENGINEERING_ACTIONS),
        error_type=random.choice(ENGINEERING_ERRORS),
        condition=random.choice(["edge case", "high load", "empty input", "special characters", "concurrent access"]),
        quality=random.choice(ENGINEERING_QUALITIES),
        new_tech=random.choice(["TypeScript", "React 18", "PostgreSQL", "Redis", "GraphQL", "gRPC"]),
        tool=random.choice(["CI/CD", "Kubernetes", "Terraform", "Datadog", "PagerDuty", "GitHub Actions"]),
        environment=random.choice(["staging", "production", "development", "QA"]),
        service=random.choice(["Stripe", "Auth0", "SendGrid", "Twilio", "AWS S3", "Elasticsearch"]),
        data_type=random.choice(["results", "data", "response", "status code"])
    )


def generate_marketing_task_name() -> str:
    """Generate realistic marketing task name."""
    template = random.choice(MARKETING_TASK_TEMPLATES)
    
    return template.format(
        content_type=random.choice(MARKETING_CONTENT_TYPES),
        asset_type=random.choice(MARKETING_ASSET_TYPES),
        campaign=random.choice(MARKETING_CAMPAIGNS),
        channel=random.choice(MARKETING_CHANNELS),
        stakeholder=random.choice(MARKETING_STAKEHOLDERS),
        version=random.randint(1, 4),
        tool=random.choice(["UTM", "HubSpot", "Google Analytics", "Marketo"]),
        event_type=random.choice(["webinar", "conference", "meetup", "workshop"])
    )


def generate_sales_task_name() -> str:
    """Generate realistic sales/CS task name."""
    template = random.choice(SALES_TASK_TEMPLATES)
    
    return template.format(
        company=random.choice(SALES_COMPANIES),
        document=random.choice(SALES_DOCUMENTS),
        meeting_type=random.choice(SALES_MEETING_TYPES),
        onboarding_step=random.choice(SALES_ONBOARDING_STEPS),
        context=random.choice(SALES_CONTEXTS),
        review_type=random.choice(["QBR", "health check", "success review", "renewal review"]),
        issue_type=random.choice(["support ticket", "integration issue", "billing concern", "feature request"]),
        team=random.choice(["Engineering", "Product", "Support", "Billing"]),
        feature=random.choice(["reporting", "integrations", "admin console", "API", "SSO"])
    )


def generate_management_task_name() -> str:
    """Generate realistic management task name."""
    template = random.choice(MANAGEMENT_TASK_TEMPLATES)
    
    return template.format(
        item=random.choice(MANAGEMENT_ITEMS),
        request_type=random.choice(MANAGEMENT_REQUEST_TYPES),
        document=random.choice(["presentation", "report", "summary", "deck"]),
        team=random.choice(["Engineering", "Marketing", "Sales", "Product", "Operations"]),
        area=random.choice(["growth", "efficiency", "hiring", "product", "revenue"]),
        quarter=random.randint(1, 4)
    )


def generate_task_name(department: str) -> str:
    """Generate task name based on department.
    
    Args:
        department: Department name
        
    Returns:
        Generated task name
    """
    if "Engineering" in department or "Product" in department:
        return generate_engineering_task_name()
    elif "Marketing" in department:
        return generate_marketing_task_name()
    elif "Sales" in department or "HR" in department or "Customer" in department:
        return generate_sales_task_name()
    else:  # Management
        return generate_management_task_name()


# Task description templates
DESCRIPTION_TEMPLATES = {
    "engineering": [
        "Implement the {feature} functionality as specified in the requirements.\n\n**Acceptance Criteria:**\n- [ ] {criteria_1}\n- [ ] {criteria_2}\n- [ ] {criteria_3}\n\n**Technical Notes:**\n- {note}",
        "{context}\n\n**Definition of Done:**\n- Unit tests passing\n- Code reviewed\n- Documentation updated",
        "We need to {action} to improve {quality}.\n\nSee related ticket: #{ticket_num}",
        "",  # Empty description
        "{brief_description}",
    ],
    "marketing": [
        "**Objective:** {objective}\n\n**Target Audience:** {audience}\n\n**Key Messages:**\n- {message_1}\n- {message_2}\n\n**Deadline:** {deadline_context}",
        "Create {asset} for the {campaign} campaign.\n\nBrand guidelines: [link]\nPrevious examples: [link]",
        "{brief_description}",
        "",
    ],
    "sales": [
        "**Account:** {company}\n**Contact:** {contact_name}\n**Context:** {context}\n\n**Next Steps:**\n- {step_1}\n- {step_2}",
        "Follow up regarding {topic}. Last interaction was {time_ago}.",
        "{brief_description}",
        "",
    ],
    "management": [
        "Review and provide sign-off on {item}.\n\n**Key Considerations:**\n- {consideration_1}\n- {consideration_2}\n\n**Deadline:** {deadline_context}",
        "{brief_description}",
        "",
    ]
}


def generate_task_description(department: str, task_name: str) -> str:
    """Generate task description based on department.
    
    Args:
        department: Department name
        task_name: Task name for context
        
    Returns:
        Generated description
    """
    # 20% empty, 50% brief, 30% detailed
    roll = random.random()
    
    if roll < 0.20:
        return ""
    elif roll < 0.70:
        # Brief description
        return random.choice([
            f"Complete this task as part of the current sprint.",
            f"High priority - please complete ASAP.",
            f"See requirements doc for details.",
            f"Standard process - follow the usual workflow.",
            f"Coordinate with the team on this.",
        ])
    else:
        # Detailed description with context
        if "Engineering" in department or "Product" in department:
            return f"""Implement the required changes as specified.

**Acceptance Criteria:**
- [ ] Functionality works as expected
- [ ] Unit tests added and passing
- [ ] No regressions in existing functionality

**Technical Notes:**
- Follow existing code patterns
- Update documentation if needed

**Definition of Done:**
- Code reviewed and approved
- QA verification complete
- Deployed to staging"""
        elif "Marketing" in department:
            return f"""Create the deliverable for the campaign.

**Requirements:**
- Follow brand guidelines
- Optimize for target audience
- Include required CTAs

**Review Process:**
- Submit for design review
- Get stakeholder approval
- Final QA before publishing"""
        elif "Sales" in department or "HR" in department or "Customer" in department:
            return f"""Complete the required customer-facing activity.

**Context:**
- Review previous interactions in CRM
- Check for any open support tickets
- Verify account health status

**Next Steps:**
- Document outcome in CRM
- Schedule follow-up if needed
- Update team on any blockers"""
        else:
            return f"""Review and provide approval.

**Key Considerations:**
- Alignment with Q objectives
- Resource availability
- Risk assessment

**Timeline:**
- Review by end of week
- Provide feedback or approval"""


# Comment templates
COMMENT_TEMPLATES = {
    "status_update": [
        "Started working on this.",
        "Making good progress on this.",
        "About 50% done, should finish by EOD tomorrow.",
        "Completed the main implementation, working on tests now.",
        "This is ready for review.",
        "Pushed the changes to the feature branch.",
        "Done! Moving to QA.",
        "Wrapped this up. Let me know if any questions.",
    ],
    "question": [
        "Quick question - {question}",
        "Can someone clarify {topic}?",
        "@{name} what's the priority on this?",
        "Should we include {feature} in scope?",
        "Who should review this?",
        "Is there a deadline I should know about?",
    ],
    "blocker": [
        "Blocked - waiting for {dependency}.",
        "Can't proceed until {blocker} is resolved.",
        "Need access to {resource} to continue.",
        "Blocked by external dependency.",
        "Waiting on response from {team}.",
    ],
    "feedback": [
        "Looks good!",
        "LGTM 👍",
        "Approved!",
        "Nice work on this.",
        "A few minor comments, otherwise good.",
        "Left some suggestions on the PR.",
        "This needs some revisions - see notes.",
    ],
    "resolution": [
        "Fixed!",
        "Done - deployed to staging.",
        "Resolved. Root cause was {cause}.",
        "Closing this out - verified in production.",
        "Completed and documented.",
    ]
}


def generate_comment(comment_type: Optional[str] = None, context: dict = None) -> str:
    """Generate realistic comment.
    
    Args:
        comment_type: Type of comment (status_update, question, blocker, feedback, resolution)
        context: Optional context dict with name, team, etc.
        
    Returns:
        Generated comment
    """
    if comment_type is None:
        comment_type = random.choices(
            ["status_update", "question", "blocker", "feedback", "resolution"],
            weights=[0.35, 0.20, 0.15, 0.20, 0.10]
        )[0]
    
    template = random.choice(COMMENT_TEMPLATES[comment_type])
    
    context = context or {}
    
    return template.format(
        question=context.get("question", "what's the expected behavior here?"),
        topic=context.get("topic", "the requirements"),
        name=context.get("name", "team"),
        feature=context.get("feature", "this feature"),
        dependency=context.get("dependency", "upstream changes"),
        blocker=context.get("blocker", "the dependency"),
        resource=context.get("resource", "the staging environment"),
        team=context.get("team", "the other team"),
        cause=context.get("cause", "a configuration issue"),
    )


def generate_team_name(department: str, index: int) -> str:
    """Generate team name based on department.
    
    Args:
        department: Department name
        index: Team index for uniqueness
        
    Returns:
        Generated team name
    """
    if "Engineering" in department:
        teams = [
            "Backend", "Frontend", "Mobile", "Platform", "Infrastructure",
            "Data Engineering", "DevOps", "Security", "QA", "API",
            "Search", "Payments", "Analytics", "Core Services", "Developer Experience"
        ]
        suffix = ["", " Team", " Squad", ""]
    elif "Marketing" in department:
        teams = [
            "Content", "Demand Gen", "Product Marketing", "Brand",
            "Events", "SEO", "Paid Media", "Social", "Creative", "Communications"
        ]
        suffix = [" Marketing", " Team", "", ""]
    elif "Sales" in department or "HR" in department or "Customer" in department:
        teams = [
            "Enterprise Sales", "SMB Sales", "Mid-Market", "Customer Success",
            "Support", "Account Management", "Sales Development", "Renewals",
            "HR Operations", "Recruiting", "People Ops", "Training"
        ]
        suffix = ["", " Team", ""]
    else:
        teams = [
            "Executive", "Product Leadership", "Engineering Leadership",
            "Operations", "Strategy", "Finance", "Legal"
        ]
        suffix = [" Leadership", " Team", ""]
    
    base_name = teams[index % len(teams)]
    return base_name + random.choice(suffix)


def generate_project_name(department: str, team_name: str, project_type: str, index: int) -> str:
    """Generate project name.
    
    Args:
        department: Department name
        team_name: Team name
        project_type: Type of project
        index: Project index for uniqueness
        
    Returns:
        Generated project name
    """
    quarter = f"Q{((index % 4) + 1)}"
    sprint_num = 40 + (index % 20)
    
    if project_type == "sprint":
        templates = [
            f"Sprint {sprint_num} - {team_name}",
            f"{quarter} {team_name} Sprint",
            f"{team_name} - Sprint {sprint_num}",
        ]
    elif project_type == "campaign":
        campaigns = [
            f"{quarter} Product Launch", f"Holiday Campaign", f"Annual Conference",
            f"Summer Campaign", f"Partner Launch", f"Rebrand Initiative",
            f"Customer Appreciation", f"Industry Report"
        ]
        templates = [campaigns[index % len(campaigns)]]
    elif project_type == "process":
        processes = [
            "Sales Pipeline", "Support Tickets", "Onboarding", "Renewals Tracker",
            "Lead Qualification", "Account Health", "Training Program"
        ]
        templates = [f"{team_name} - {processes[index % len(processes)]}"]
    elif project_type == "cross_functional":
        templates = [
            f"{quarter} Product Launch - Cross-Team",
            f"Major Release {index % 10 + 1}.0",
            f"Platform Migration - Phase {index % 3 + 1}",
        ]
    else:
        templates = [
            f"{quarter} Strategic Planning",
            f"Executive Review - {team_name}",
            f"Board Prep - {quarter}",
        ]
    
    return random.choice(templates)