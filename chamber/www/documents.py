"""Context provider for the documents workspace page."""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Documents"
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
    doc_param = (frappe.form_dict.get("doc") or "").strip()
    if not preselect and doc_param:
        try:
            preselect = frappe.db.get_value("Generated Document", doc_param, "legal_matter") or ""
        except Exception:
            preselect = ""
    if preselect and any(m.name == preselect for m in context.matters):
        context.preselect = preselect
    elif context.matters:
        context.preselect = context.matters[0].name
    return context
