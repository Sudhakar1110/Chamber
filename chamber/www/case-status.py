"""Context provider for the case status search page.

The search_matter API has been moved to chamber.api.case_status
to avoid the hyphen-in-filename import issue (case-status.py →
chamber.www.case_status fails as a Python module path).
"""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Check Case Status"
    context.is_manager = "System Manager" in frappe.get_roles()
    context.is_guest = frappe.session.user == "Guest"
