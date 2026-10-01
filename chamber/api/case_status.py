"""Case Status search API — called from the /case-status portal page."""
import frappe


@frappe.whitelist(allow_guest=True)
def search_matter(query):
    """Search for a Legal Matter by name, case_number, or cnr_number."""
    query = query.strip()
    if not query:
        return {"matter": None}

    # Search by matter title (partial match), case_number, or cnr_number
    matter = None

    # Try exact name match first
    if frappe.db.exists("Legal Matter", query):
        matter_name = query
    else:
        # Try partial match on matter_title
        result = frappe.db.get_value(
            "Legal Matter",
            {"matter_title": ["like", f"%{query}%"]},
            "name",
        )
        if not result:
            # Try case_number
            result = frappe.db.get_value(
                "Legal Matter",
                {"case_number": ["like", f"%{query}%"]},
                "name",
            )
        if not result:
            # Try cnr_number
            result = frappe.db.get_value(
                "Legal Matter",
                {"cnr_number": ["like", f"%{query}%"]},
                "name",
            )
        matter_name = result

    if not matter_name:
        return {"matter": None}

    # Get matter details with joins
    m = frappe.db.get_all(
        "Legal Matter",
        filters={"name": matter_name},
        fields=[
            "name", "matter_title", "status", "priority", "case_number", "cnr_number",
            "filing_date", "judge_name", "description", "vertical",
            "court", "sections_charged", "bail_status",
            "portal", "portal_status", "portal_status_date", "portal_status_notes",
            "last_sync", "last_sync_status", "ecourts_coverage",
        ],
        limit=1,
    )
    if not m:
        return {"matter": None}

    matter = m[0]

    # Get vertical name
    if matter.get("vertical"):
        matter["vertical_name"] = frappe.db.get_value(
            "Legal Vertical", matter["vertical"], "vertical_name"
        )

    # Get court name
    if matter.get("court"):
        matter["court_name"] = frappe.db.get_value("Court", matter["court"], "court_name")

    # Get upcoming hearings
    hearings = frappe.get_all(
        "Hearing",
        filters={"legal_matter": matter_name},
        fields=["hearing_date", "purpose", "judge", "next_hearing_date", "outcome"],
        order_by="hearing_date desc",
        limit=5,
    )

    # Get timeline entries
    timeline = frappe.get_all(
        "Timeline Entry",
        filters={"legal_matter": matter_name},
        fields=["entry_date", "event_type", "title", "description", "source"],
        order_by="entry_date desc",
        limit=10,
    )

    return {"matter": matter, "hearings": hearings, "timeline": timeline}
