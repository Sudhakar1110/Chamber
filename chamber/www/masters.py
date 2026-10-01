"""Context provider for the masters reference page."""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Masters"
    context.is_manager = "System Manager" in frappe.get_roles()
    context.is_guest = frappe.session.user == "Guest"
    context.matter_types = []
    context.courts = []
    context.clauses = []
    context.templates = []
    if context.is_guest:
        return context
    try:
        context.matter_types = frappe.get_all(
            "Matter Type",
            fields=["name", "matter_type", "vertical", "code", "enabled"],
            order_by="enabled desc, matter_type asc",
            limit_page_length=500,
        )
    except Exception:
        context.matter_types = []
    try:
        context.courts = frappe.get_all(
            "Court",
            fields=["name", "court_name", "court_tier", "state", "jurisdiction", "ecourts_enabled"],
            order_by="court_name asc",
            limit_page_length=500,
        )
    except Exception:
        context.courts = []
    try:
        context.clauses = frappe.get_all(
            "Clause Library",
            fields=["name", "clause_title", "clause_text", "applicable_drafting_type", "tags"],
            order_by="clause_title asc",
            limit_page_length=500,
        )
    except Exception:
        context.clauses = []
    try:
        context.templates = frappe.get_all(
            "Document Template",
            fields=["name", "template_name", "vertical", "drafting_type", "status", "version", "description"],
            order_by="status, template_name asc",
            limit_page_length=500,
        )
    except Exception:
        context.templates = []
    return context
