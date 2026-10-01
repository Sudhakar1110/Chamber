"""Context provider for the about page."""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "About"
    context.is_manager = "System Manager" in frappe.get_roles()
    context.is_guest = frappe.session.user == "Guest"
    return context
