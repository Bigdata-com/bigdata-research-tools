import dataclasses
from datetime import datetime, timezone
from enum import Enum
from importlib.metadata import version
from logging import Logger, getLogger
from queue import Queue

from bigdata_client import Bigdata, tracking_services

from bigdata_research_tools import __version__

logger: Logger = getLogger(__name__)


class TraceEventNames(Enum):
    NARRATIVE_MINER = "NarrativeMinersRun"
    THEMATIC_SCREENER = "ThematicScreenerRun"
    RISK_ANALYZER = "RiskAnalyzerRun"
    COMPANY_SEARCH = "CompanySearchRun"
    RUN_SEARCH = "SearchRun"

@dataclasses.dataclass
class Trace:
    event_name: TraceEventNames = None
    document_type: str = None
    start_date: str = None
    end_date: str = None
    rerank_threshold: float = None
    llm_model: str = None
    frequency: str = None
    result: str = None
    workflow_start_date: datetime = None
    workflow_end_date: datetime = None
    workflow_usage: str = None

    _query_units_queue: Queue = Queue()  # To protect against concurrent access issues

    @staticmethod
    def get_time_now():
        """Called when initializing the workflow start and end date to have the same format."""
        return datetime.now(timezone.utc)

    def add_query_units(self, query_units: int):
        self._query_units_queue.put(query_units)

    def to_trace_event(self):
        return tracking_services.TraceEvent(
            event_name=self.event_name.value,
            properties={
                "platform": "sdk",
                "documentType": self.document_type,
                "queryStartDate": self.start_date,
                "queryEndDate": self.end_date,
                "rerankThreshold": self.rerank_threshold,
                "llmModel": self.llm_model,
                "frequency": self.frequency,
                "bigdataResearchToolsVersion": __version__,
                "bigdataClientVersion": version("bigdata-client"),
                "result": self.result,
                "workflowStartDate": self.workflow_start_date.isoformat(
                    timespec="seconds"
                ),
                "workflowEndDate": self.workflow_end_date.isoformat(timespec="seconds"),
                "workflowUsage": sum(self._query_units_queue.queue),
            },
        )


def send_trace(bigdata: Bigdata, trace: Trace):
    try:
        tracking_services.send_trace(bigdata, trace.to_trace_event())
    except Exception:  # noqa
        logger.warning("Trace event could not be sent to BigData.")
