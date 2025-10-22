from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from importlib.metadata import version
from logging import Logger, getLogger

from bigdata_client import Bigdata, tracking_services
from pydantic import BaseModel, computed_field

from bigdata_research_tools import __version__

logger: Logger = getLogger(__name__)


class WorkflowStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class TraceEventNames(Enum):
    WORKFLOW_EXECUTION = "BigdataResearchToolsWorkflowExecution"
    QUERY_UNITS_CONSUMPTION = "BigdataResearchToolsQueryUnitsConsumption"

class TraceEventABC(ABC):
    @abstractmethod
    def to_trace_event(self) -> tracking_services.TraceEvent:
        ...

class WorkflowTraceEvent(BaseModel, TraceEventABC):
    start_date: datetime
    end_date: datetime
    name: str
    llm_model: str | None
    status: WorkflowStatus

    @computed_field
    def duration(self) -> float:
        return (self.end_date - self.start_date).total_seconds()

    def to_trace_event(self) -> tracking_services.TraceEvent:
        return tracking_services.TraceEvent(
            event_name=TraceEventNames.WORKFLOW_EXECUTION.value,
            properties={
                "workflow_name": self.name,
                "workflow_start_date": self.start_date.isoformat(),
                "workflow_end_date": self.end_date.isoformat(),
                "workflow_status": self.status.value,
                "llm_model": self.llm_model,
                "workflow_duration_seconds": self.duration,
                "bigdata_research_tools_version": __version__,
                "bigdata_client_version": version("bigdata-client"),
            }
        )
    

class ReportSearchUsageTraceEvent(BaseModel, TraceEventABC):
    workflow_name: str
    document_type: str
    start_date: str
    end_date: str
    query_units: float

    def to_trace_event(self) -> tracking_services.TraceEvent:
        return tracking_services.TraceEvent(
            event_name=TraceEventNames.QUERY_UNITS_CONSUMPTION.value,
            properties={
                "workflow_name": self.workflow_name,
                "document_type": self.document_type,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "query_units": self.query_units,
                "bigdata_research_tools_version": __version__,
                "bigdata_client_version": version("bigdata-client"),
            }
        )

def send_trace(bigdata: Bigdata, trace: TraceEventABC):
    tracking_services.send_trace(bigdata, trace.to_trace_event())
