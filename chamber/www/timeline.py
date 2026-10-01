"""Context provider for the matter timeline hub page."""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Matter Timeline"
    context.is_manager = "System Manager" in frappe.get_roles()
    context.is_guest = frappe.session.user == "Guest"
    context.matters = []
    context.preselect = ""
    if context.is_guest:
        return context
    try:
        context.matters = frappe.get_all(
            "Legal Matter",
            fields=["name", "matter_title", "case_number", "status"],
            order_by="modified desc",
            limit_page_length=200,
        )
    except Exception:
        context.matters = []
    preselect = (frappe.form_dict.get("matter") or "").strip()
    if preselect and any(m.name == preselect for m in context.matters):
        context.preselect = preselect
    elif context.matters:
        context.preselect = context.matters[0].name
    return context
