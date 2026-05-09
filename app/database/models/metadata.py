from sqlalchemy import (
    ARRAY,
    JSON,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func

metadata = MetaData()

# -------------------
# Base tables
# -------------------

epics = Table(
    "epics",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50), nullable=False),
    Column("project_id", String(50), nullable=False),
    UniqueConstraint("name", "project_id"),
)

features = Table(
    "features",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("epic_id", ForeignKey("epics.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("description", Text),
    Column("filename", Text, nullable=False),
    Column("tags", Text),
    Column("project_id", String(50), nullable=False),
    UniqueConstraint("project_id", "filename"),
)

scenarios = Table(
    "scenarios",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("scenario_id", Text, nullable=False),
    Column("feature_id", ForeignKey("features.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("description", Text),
    Column("steps", Text),
    Column("tags", Text),
    Column("isoutline", Boolean),
    Column("project_id", String(50), nullable=False),
    Column("is_deleted", Boolean, nullable=False, server_default="false"),
    UniqueConstraint("scenario_id", "feature_id", "project_id"),
    CheckConstraint("is_deleted IS NOT NULL"),
)

operations = Table(
    "operations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("type", String(20), nullable=False),
    Column("op_user", String(100), nullable=False),
    Column("op_order", Integer, nullable=False),
    Column("content", String),
    UniqueConstraint("type", "op_order"),
)

# -------------------
# Projects / versions
# -------------------

projects = Table(
    "projects",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(64), nullable=False),
    Column("alias", String(64), nullable=False),
    UniqueConstraint("name"),
)

versions = Table(
    "versions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("project_id", ForeignKey("projects.id"), nullable=False),
    Column("version", String(50), nullable=False),
    Column("created", TIMESTAMP, server_default=func.now(), nullable=False),
    Column("updated", TIMESTAMP, server_default=func.now(), nullable=False),
    Column("started", TIMESTAMP),
    Column("end_forecast", TIMESTAMP),
    Column("status", String(50), server_default="recorded"),
    Column("open", Integer, server_default="0"),
    Column("cancelled", Integer, server_default="0"),
    Column("blocked", Integer, server_default="0"),
    Column("in_progress", Integer, server_default="0"),
    Column("done", Integer, server_default="0"),
    Column("open_blocking", Integer, server_default="0"),
    Column("open_major", Integer, server_default="0"),
    Column("open_minor", Integer, server_default="0"),
    Column("closed_blocking", Integer, server_default="0"),
    Column("closed_major", Integer, server_default="0"),
    Column("closed_minor", Integer, server_default="0"),
    UniqueConstraint("project_id", "version"),
    CheckConstraint(
        "started IS NULL OR end_forecast IS NULL OR started < end_forecast", name="check_started_before_end_forecast"
    ),
)

# -------------------
# Tickets / users
# -------------------

tickets = Table(
    "tickets",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("reference", String(50), nullable=False),
    Column("description", String),
    Column("status", String(50), server_default="open"),
    Column("created", TIMESTAMP, server_default=func.now(), nullable=False),
    Column("updated", TIMESTAMP, server_default=func.now(), nullable=False),
    Column("current_version", ForeignKey("versions.id"), nullable=False),
    Column("past_versions", ARRAY(String(50))),
    Column("delivery_date", TIMESTAMP),
    Column("project_id", ForeignKey("projects.id"), nullable=False),
    UniqueConstraint("project_id", "reference"),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(255), nullable=False),
    Column("password", String, nullable=False),
    Column("scopes", JSON),
    UniqueConstraint("username"),
    CheckConstraint(
        "username ~* '([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\\.[A-Za-z]{2,})+'", name="check_email"
    ),
)

# -------------------
# Campaigns
# -------------------

campaigns = Table(
    "campaigns",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("project_id", ForeignKey("projects.id"), nullable=False),
    Column("version", String(50), nullable=False),
    Column("occurrence", Integer),
    Column("description", Text),
    Column("status", Text),
    UniqueConstraint("project_id", "version", "occurrence"),
)

campaign_tickets = Table(
    "campaign_tickets",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("campaign_id", ForeignKey("campaigns.id"), nullable=False),
    Column("ticket_reference", String(50), nullable=False),
    Column("ticket_id", ForeignKey("tickets.id")),
    UniqueConstraint("campaign_id", "ticket_reference"),
)

campaign_ticket_scenarios = Table(
    "campaign_ticket_scenarios",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("campaign_ticket_id", ForeignKey("campaign_tickets.id"), nullable=False),
    Column("scenario_id", ForeignKey("scenarios.id"), nullable=False),
    Column("status", Text),
    UniqueConstraint("campaign_ticket_id", "scenario_id"),
)

# -------------------
# Test results
# -------------------

test_scenario_results = Table(
    "test_scenario_results",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("run_date", TIMESTAMP, nullable=False),
    Column("project_id", String(50), nullable=False),
    Column("version", String(50), nullable=False),
    Column("campaign_id", ForeignKey("campaigns.id"), nullable=False),
    Column("epic_id", ForeignKey("epics.id"), nullable=False),
    Column("feature_id", ForeignKey("features.id"), nullable=False),
    Column("scenario_id", ForeignKey("scenarios.id"), nullable=False),
    Column("status", String(50), nullable=False),
    Column("is_partial", Boolean, server_default="false"),
)

test_feature_results = Table(
    "test_feature_results",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("run_date", TIMESTAMP, nullable=False),
    Column("project_id", String(50), nullable=False),
    Column("version", String(50), nullable=False),
    Column("campaign_id", ForeignKey("campaigns.id"), nullable=False),
    Column("epic_id", ForeignKey("epics.id"), nullable=False),
    Column("feature_id", ForeignKey("features.id"), nullable=False),
    Column("status", String(50), nullable=False),
    Column("is_partial", Boolean, server_default="false"),
)

test_epic_results = Table(
    "test_epic_results",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("run_date", TIMESTAMP, nullable=False),
    Column("project_id", String(50), nullable=False),
    Column("version", String(50), nullable=False),
    Column("campaign_id", ForeignKey("campaigns.id"), nullable=False),
    Column("epic_id", ForeignKey("epics.id"), nullable=False),
    Column("status", String(50), nullable=False),
    Column("is_partial", Boolean, server_default="false"),
)

# -------------------
# Bugs
# -------------------

bugs = Table(
    "bugs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("url", String),
    Column("description", String),
    Column("project_id", ForeignKey("projects.id"), nullable=False),
    Column("version_id", ForeignKey("versions.id"), nullable=False),
    Column("fix_version_id", Integer),
    Column("criticality", String(20), nullable=False),
    Column("status", String(20), nullable=False),
    Column("created", TIMESTAMP, server_default=func.now()),
    Column("updated", TIMESTAMP, server_default=func.now()),
    UniqueConstraint("project_id", "version_id", "title"),
    CheckConstraint("length(title) > 1", name="title_length"),
)

bugs_issues = Table(
    "bugs_issues",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("bug_id", ForeignKey("bugs.id")),
    Column("occurrence", Integer),
    Column("ticket_reference", String(50)),
    Column("scenario_id", ForeignKey("scenarios.id")),
    UniqueConstraint("bug_id", "occurrence", "ticket_reference", "scenario_id"),
)
