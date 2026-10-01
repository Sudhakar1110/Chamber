"""Context provider for the deadline tracker page."""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Deadline Tracker"
    context.is_manager = "System Manager" in frappe.get_roles()
    context.is_guest = frappe.session.user == "Guest"
    context.verticals = []
    context.deadlines = []
    context.counts = {}
    if context.is_guest:
        return context
    try:
        context.verticals = frappe.get_all(
            "Legal Vertical",
            fields=["name", "vertical_name"],
            filters={"enabled": 1},
            order_by="priority asc",
        )
    except Exception:
        context.verticals = []
    if frappe.has_permission("Legal Matter"):
        try:
            from chamber.api.deadlines import get_upcoming

            data = get_upcoming()
            context.deadlines = data.get("deadlines") or []
            context.counts = data.get("counts") or {}
        except Exception:
            frappe.clear_last_message()
    return context
