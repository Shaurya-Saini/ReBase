"""API request/response shapes — CONTRACT.md §2 (enums) and §4 (schemas).

If this file and CONTRACT.md disagree, this file is wrong.
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    # Lets routers build responses straight from SQLModel rows.
    model_config = ConfigDict(from_attributes=True)


# ---------- §2 Enums ----------

class MachineType(str, Enum):
    excavator = "excavator"
    wheel_loader = "wheel_loader"
    drill_rig = "drill_rig"
    dump_truck = "dump_truck"


class MachineStatus(str, Enum):
    available = "available"
    in_use = "in_use"
    maintenance = "maintenance"


class Experience(str, Enum):
    novice = "novice"
    intermediate = "intermediate"
    expert = "expert"


class Lang(str, Enum):
    en_IN = "en-IN"
    hi_IN = "hi-IN"
    ta_IN = "ta-IN"
    te_IN = "te-IN"


class JobStatus(str, Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    done = "done"


class Shift(str, Enum):
    day = "day"
    night = "night"


class RestStatus(str, Enum):
    ok = "ok"
    warning = "warning"
    must_rest = "must_rest"


class SessionState(str, Enum):
    pre_start = "pre_start"
    briefing = "briefing"
    active = "active"
    ended = "ended"


class ChecklistStatus(str, Enum):
    pending = "pending"
    ok = "ok"
    defect = "defect"
    na = "na"


class AlertType(str, Enum):
    seatbelt_off = "seatbelt_off"
    drowsiness = "drowsiness"
    distraction = "distraction"
    operator_absent = "operator_absent"
    proximity = "proximity"
    excessive_idle = "excessive_idle"
    overheat = "overheat"
    overload = "overload"
    unsafe_operation = "unsafe_operation"


class AlertSource(str, Enum):
    edge_cv = "edge_cv"
    telemetry = "telemetry"


class Severity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


# SimEvent = any AlertType value, or "normal"
SIM_EVENTS: list[str] = ["normal"] + [t.value for t in AlertType]


# ---------- §4 Schemas ----------

class Health(Schema):
    status: str
    version: str


class LoginRequest(Schema):
    operator_id: str
    pin: str


class Rest(Schema):
    status: RestStatus
    next_allowed_start: datetime | None = None
    reason: str | None = None


class Operator(Schema):
    id: str
    name: str
    lang: Lang
    experience: dict[MachineType, Experience]
    hours_today: float
    hours_7d: float
    rest: Rest


class Machine(Schema):
    id: str
    type: MachineType
    model: str
    serial: str
    hour_meter: float
    status: MachineStatus
    last_inspection: datetime | None = None


class Job(Schema):
    id: str
    project_id: str
    title: str
    site: str
    machine_type: MachineType
    scheduled_start: datetime
    planned_hours: float
    status: JobStatus


class Assignment(Schema):
    id: str
    operator_id: str
    date: date
    shift: Shift
    job: Job
    machine: Machine


class AssignmentCreate(Schema):
    operator_id: str
    job_id: str
    machine_id: str
    date: date
    shift: Shift = Shift.day


class EstimateFactor(Schema):
    name: str
    effect_pct: float
    note: str


class Estimate(Schema):
    job_id: str
    estimated_hours: float
    range_hours: tuple[float, float]
    factors: list[EstimateFactor]
    project_completion_date: date | None = None


class SessionCreate(Schema):
    operator_id: str
    machine_id: str
    job_id: str


class Session(Schema):
    id: str
    operator_id: str
    machine_id: str
    job_id: str
    state: SessionState
    started_at: datetime | None = None
    ended_at: datetime | None = None


class SessionSummary(Schema):
    session_id: str
    duration_hours: float
    alerts_total: int
    alerts_critical: int
    idle_minutes: float


class ChecklistItem(Schema):
    id: str
    text: str
    critical: bool
    status: ChecklistStatus
    note: str | None = None


class ChecklistSection(Schema):
    title: str
    items: list[ChecklistItem]


class Checklist(Schema):
    session_id: str
    machine_type: MachineType
    standard_refs: list[str]
    sections: list[ChecklistSection]


class ChecklistItemUpdate(Schema):
    status: ChecklistStatus
    note: str | None = None


class Briefing(Schema):
    session_id: str
    lang: Lang
    machine_summary: str
    job_summary: str
    estimated_hours: float
    hazards: list[str]
    reminders: list[str]


class AlertCreate(Schema):
    type: AlertType
    source: AlertSource
    severity: Severity
    message: str
    ts: datetime | None = None  # server fills in now() if missing


class Alert(Schema):
    id: str
    session_id: str
    type: AlertType
    source: AlertSource
    severity: Severity
    message: str
    ts: datetime
    acknowledged: bool


class SimScenarioRequest(Schema):
    session_id: str
    event: str  # SimEvent


class AssistantRequest(Schema):
    machine_id: str
    session_id: str | None = None
    question: str
    lang: Lang = Lang.en_IN


class Source(Schema):
    doc: str
    section: str


class AssistantAnswer(Schema):
    answer: str
    lang: Lang
    sources: list[Source]


class TtsRequest(Schema):
    text: str
    lang: Lang


class TranslateRequest(Schema):
    text: str
    target: Lang
    source: Lang | None = None


class TranslateResponse(Schema):
    text: str
    lang: Lang


class TrainingStep(Schema):
    kind: str  # text | video | tip
    content: str
    url: str | None = None


class QuizQuestion(Schema):
    q: str
    options: list[str]
    answer_index: int


class TrainingModule(Schema):
    id: str
    machine_type: MachineType
    level: Experience
    title: str
    duration_min: int
    steps: list[TrainingStep]
    quiz: list[QuizQuestion]


class TrainingCompleteRequest(Schema):
    operator_id: str
    score: float


class Ok(Schema):
    ok: bool
