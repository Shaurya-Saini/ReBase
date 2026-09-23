"""Database tables (SQLModel). API shapes live in app/schemas.py (CONTRACT §4).

Enum-valued columns are stored as plain strings; the allowed values are the
CONTRACT §2 enums defined in app/schemas.py. Datetimes are timezone-aware UTC
(SQLModel rejects naive ones on write and returns UTC on read).
"""

from datetime import date, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Operator(SQLModel, table=True):
    id: str = Field(primary_key=True)  # op_
    name: str
    lang: str  # Lang
    pin: str  # 4 digits, checked but not secure (hackathon)
    # {machine_type: Experience}
    experience: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))


class Machine(SQLModel, table=True):
    id: str = Field(primary_key=True)  # mc_
    type: str  # MachineType
    model: str
    serial: str
    hour_meter: float
    status: str = "available"  # MachineStatus
    last_inspection: datetime | None = None


class Project(SQLModel, table=True):
    id: str = Field(primary_key=True)  # prj_
    name: str
    site: str
    target_date: date | None = None


class Job(SQLModel, table=True):
    id: str = Field(primary_key=True)  # job_
    project_id: str = Field(foreign_key="project.id")
    title: str
    site: str
    machine_type: str  # MachineType
    scheduled_start: datetime
    planned_hours: float
    status: str = "scheduled"  # JobStatus
    # Estimator inputs (not exposed in the Job schema)
    weather: str = "clear"  # clear | rain | heat | wind
    hazards: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class Assignment(SQLModel, table=True):
    id: str = Field(primary_key=True)  # asg_
    operator_id: str = Field(foreign_key="operator.id", index=True)
    job_id: str = Field(foreign_key="job.id")
    machine_id: str = Field(foreign_key="machine.id")
    date: date
    shift: str = "day"  # Shift


class WorkSession(SQLModel, table=True):
    """A mounted operating session (API name: Session)."""

    __tablename__ = "session"

    id: str = Field(primary_key=True)  # ses_
    operator_id: str = Field(foreign_key="operator.id", index=True)
    machine_id: str = Field(foreign_key="machine.id")
    job_id: str = Field(foreign_key="job.id")
    state: str = "pre_start"  # SessionState
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None


class ChecklistItemState(SQLModel, table=True):
    """Per-session status of one checklist item (content comes from YAML)."""

    session_id: str = Field(foreign_key="session.id", primary_key=True)
    item_id: str = Field(primary_key=True)  # chk_
    status: str = "pending"  # ChecklistStatus
    note: str | None = None
    updated_at: datetime | None = None


class Alert(SQLModel, table=True):
    """Incident log. Created by the app (E18) from on-device detection."""

    id: str = Field(primary_key=True)  # alr_
    session_id: str = Field(foreign_key="session.id", index=True)
    type: str  # AlertType
    source: str  # AlertSource
    severity: str  # Severity
    message: str  # English, for logs
    ts: datetime
    acknowledged: bool = False


class JobLog(SQLModel, table=True):
    """Past job history — training data for the XGBoost estimator (B6)."""

    id: int | None = Field(default=None, primary_key=True)
    operator_id: str = Field(foreign_key="operator.id")
    machine_type: str  # MachineType
    operator_experience: str  # Experience
    weather: str  # clear | rain | heat | wind
    planned_hours: float
    actual_hours: float
    date: date


class TrainingCompletion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    operator_id: str = Field(foreign_key="operator.id", index=True)
    module_id: str  # trn_
    score: float
    completed_at: datetime
