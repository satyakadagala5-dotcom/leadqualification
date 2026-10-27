
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END

from database import get_lead, qualify_lead


class LeadState(TypedDict):
    lead_id: str
    status: Optional[str]
    next_action: Optional[str]


def check_qualification(state: LeadState):
    status = qualify_lead(state["lead_id"])

    if status == "SQL":
        action = "export_and_appointment"
    elif status == "OPTED_OUT":
        action = "stop"
    elif status == "MQL":
        action = "followup"
    else:
        action = "not_found"

    return {
        "status": status,
        "next_action": action,
    }


def route_lead(state: LeadState):
    if state["next_action"] == "export_and_appointment":
        return "sql"

    if state["next_action"] == "followup":
        return "mql"

    return "stop"


def sql_action(state: LeadState):
    # The dashboard exports SQL leads to Excel.
    # Connect your appointment agent here.
    print(
        f"Lead {state['lead_id']} qualified as SQL. "
        "Ready for appointment processing."
    )
    return {"next_action": "appointment_ready"}


def mql_action(state: LeadState):
    # The scheduler handles the actual timed follow-up.
    return {"next_action": "followup_pending"}


def stop_action(state: LeadState):
    return {"next_action": state["next_action"]}


builder = StateGraph(LeadState)

builder.add_node("qualify", check_qualification)
builder.add_node("sql_action", sql_action)
builder.add_node("mql_action", mql_action)
builder.add_node("stop_action", stop_action)

builder.add_edge(START, "qualify")

builder.add_conditional_edges(
    "qualify",
    route_lead,
    {
        "sql": "sql_action",
        "mql": "mql_action",
        "stop": "stop_action",
    },
)

builder.add_edge("sql_action", END)
builder.add_edge("mql_action", END)
builder.add_edge("stop_action", END)

lead_graph = builder.compile()


def process_lead(lead_id):
    if not get_lead(lead_id):
        return {
            "status": None,
            "next_action": "not_found",
        }

    return lead_graph.invoke({
        "lead_id": str(lead_id),
        "status": None,
        "next_action": None,
    })


if __name__ == "__main__":
    print("Lead qualification workflow is ready.")