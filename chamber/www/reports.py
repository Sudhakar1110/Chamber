"""Context provider for the portal reports page."""
import frappe
from frappe.utils import add_days, today


def get_context(context):
    context.no_cache = 1
    context.title = "Reports"
    context.is_manager = "System Manager" in frappe.get_roles()
    context.is_guest = frappe.session.user == "Guest"
    context.verticals = []
    context.today = today()
    context.horizon = add_days(today(), 90)
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
    return context
