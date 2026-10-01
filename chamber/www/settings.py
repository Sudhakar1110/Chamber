"""Context provider for the portal settings page (System Manager only)."""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Settings"
    context.is_manager = "System Manager" in frappe.get_roles()
    context.is_guest = frappe.session.user == "Guest"
    context.portals = ["IP India", "NCLT / NCLAT", "State RERA"]
    return context
