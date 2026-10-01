"""Context provider for the notifications page."""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Notifications"
    context.is_manager = "System Manager" in frappe.get_roles()
    context.is_guest = frappe.session.user == "Guest"
    context.notifications = []
    context.unread_count = 0
    if context.is_guest:
        return context
    try:
        context.notifications = frappe.get_all(
            "Notification Log",
            filters={"for_user": frappe.session.user},
            fields=[
                "name",
                "title",
                "subject",
                "document_type",
                "document_name",
                "from_user",
                "for_user",
                "read",
                "creation",
            ],
            order_by="creation desc",
            limit_page_length=100,
        )
        context.unread_count = len([n for n in context.notifications if not n.read])
    except Exception:
        context.notifications = []
    return context
