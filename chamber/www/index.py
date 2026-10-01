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
    context.total_matters = 0
    context.court_fees_paid = 0
    context.pending_signatures = 0
    context.caveats_active = 0
    context.overdue_deadlines = 0
    context.today_hearings = []
    context.upcoming_sessions = []
    context.upcoming_hearings = []
    context.recent_matters = []
    context.deadlines = []
    context.by_vertical = []
    context.by_status = []
    context.hearings30 = []
    context.chart_max_vertical = 1
    context.chart_max_status = 1
    context.chart_max_hearings = 1
    context.is_manager = "System Manager" in frappe.get_roles()
    context.is_guest = frappe.session.user == "Guest"

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

            # Desk-dashboard headline + chart data (items 1 and 9).
            try:
                from chamber.api.dashboard import get_stats

                stats = get_stats() or {}
                headline = stats.get("headline") or {}
                context.total_matters = headline.get("total_matters", 0)
                context.court_fees_paid = headline.get("court_fees_paid", 0)
                context.pending_signatures = headline.get("pending_signatures", 0)
                context.caveats_active = headline.get("caveats_active", 0)
                context.overdue_deadlines = headline.get("overdue_deadlines", 0)
                context.by_vertical = stats.get("by_vertical") or []
                context.by_status = stats.get("by_status") or []
                context.hearings30 = stats.get("hearings") or []
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Portal Dashboard Stats")

            # Upcoming deadlines feed for the dashboard panel.
            try:
                from chamber.api.deadlines import get_upcoming

                context.deadlines = (get_upcoming(horizon_days=90) or {}).get("deadlines", [])[:6]
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Portal Dashboard Deadlines")

            context.chart_max_vertical = max(
                [int(v.get("value") or 0) for v in context.by_vertical] or [1]
            )
            context.chart_max_status = max(
                [int(v.get("value") or 0) for v in context.by_status] or [1]
            )
            context.chart_max_hearings = max(
                [int(h.get("value") or 0) for h in context.hearings30] or [1]
            )
            for v in context.by_vertical:
                v["pct"] = int(100 * int(v.get("value") or 0) / context.chart_max_vertical)
            for v in context.by_status:
                v["pct"] = int(100 * int(v.get("value") or 0) / context.chart_max_status)
            for h in context.hearings30:
                h["pct"] = int(100 * int(h.get("value") or 0) / context.chart_max_hearings)

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
