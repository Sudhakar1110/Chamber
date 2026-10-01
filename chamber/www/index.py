"""Context provider for the portal dashboard page."""
import frappe
from frappe.utils import today


def get_context(context):
    context.no_cache = 1
    context.title = "Dashboard"

    # Safe defaults — the page still renders even if a query fails.
    context.open_matters = 0
    context.pending_intake = 0
    context.docs_to_review = 0
    context.today_hearings = []
    context.upcoming_sessions = []
    context.upcoming_hearings = []
    context.recent_matters = []

    try:
        if frappe.has_permission("Legal Matter"):
            closed = ["Disposed", "Withdrawn", "Closed"]
            context.open_matters = len(
                frappe.get_list(
                    "Legal Matter",
                    filters={"status": ["not in", closed], "is_archived": 0},
                    fields=["name"],
                    limit_page_length=1000,
                )
            )
            context.pending_intake = len(
                frappe.get_list(
                    "Legal Matter",
                    filters={"status": "Intake Pending"},
                    fields=["name"],
                    limit_page_length=1000,
                )
            )
            context.recent_matters = frappe.get_list(
                "Legal Matter",
                filters={"is_archived": 0},
                fields=[
                    "name",
                    "matter_title",
                    "status",
                    "case_number",
                    "filing_date",
                    "vertical",
                    "modified",
                ],
                order_by="modified desc",
                limit_page_length=5,
            )
            for row in context.recent_matters:
                row["vertical_name"] = frappe.db.get_value(
                    "Legal Vertical", row.get("vertical"), "vertical_name"
                )

        if frappe.has_permission("Generated Document"):
            context.docs_to_review = len(
                frappe.get_list(
                    "Generated Document",
                    filters={
                        "workflow_state": ["in", ["Internal Review", "Client Review"]]
                    },
                    fields=["name"],
                    limit_page_length=1000,
                )
            )

        if frappe.has_permission("Hearing"):
            context.today_hearings = frappe.get_list(
                "Hearing",
                filters={"hearing_date": today()},
                fields=[
                    "legal_matter",
                    "hearing_date",
                    "purpose",
                    "judge",
                    "next_hearing_date",
                ],
                order_by="hearing_date asc",
                limit_page_length=10,
            )
            context.upcoming_hearings = frappe.get_list(
                "Hearing",
                filters={"hearing_date": [">", today()]},
                fields=["legal_matter", "hearing_date", "purpose", "judge"],
                order_by="hearing_date asc",
                limit_page_length=10,
            )

        if frappe.has_permission("Mediation Session"):
            context.upcoming_sessions = frappe.get_list(
                "Mediation Session",
                filters={"session_date": [">=", today()], "status": "Scheduled"},
                fields=["legal_matter", "session_date", "purpose", "status"],
                order_by="session_date asc",
                limit_page_length=10,
            )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Portal Dashboard Context")
