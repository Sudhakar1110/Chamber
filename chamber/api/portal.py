"""Portal-only helpers: report tables, global search, and safe doc actions.

These mirror the desk Script Reports and controller methods so the public
portal pages can show the same data without desk access.
"""
import frappe

# (doctype, method) pairs the portal may run via run_action. All of these are
# @frappe.whitelist() controller methods; permission is checked on the doc.
DOC_ACTIONS = {
	("Generated Document", "advance_workflow"),
	("Generated Document", "suggest_clauses"),
}


@frappe.whitelist()
def report_court_fees(from_date=None, to_date=None, status=None):
	"""Court Fees report rows (mirrors chamber/report/court_fees)."""
	conditions = ["ca.docstatus < 2"]
	params = {}
	if from_date:
		conditions.append("ca.filing_date >= %(from_date)s")
		params["from_date"] = from_date
	if to_date:
		conditions.append("ca.filing_date <= %(to_date)s")
		params["to_date"] = to_date
	if status:
		conditions.append("ca.current_status = %(status)s")
		params["status"] = status

	rows = frappe.db.sql(
		"""select ca.name, ca.application_title, ca.matter, ca.court,
		ca.court_fees, ca.fee_receipt_reference, ca.current_status, ca.filing_date
		from `tabChamber Application` ca
		where {0}
		order by ca.filing_date desc, ca.name""".format(
			" and ".join(conditions)
		),
		params,
		as_dict=1,
	)
	return [dict(r) for r in rows]


@frappe.whitelist()
def report_matter_status(vertical=None):
	"""Matter Status report rows (mirrors chamber/report/matter_status)."""
	vertical_filter = ""
	params = []
	if vertical:
		vertical_filter = "where m.vertical = %s"
		params.append(vertical)

	rows = frappe.db.sql(
		"""
		select
			m.vertical,
			coalesce(v.vertical_name, m.vertical) as vertical_name,
			m.status,
			count(*) as `count`,
			sum(coalesce(m.claim_amount, 0)) as total_claim,
			sum(case when m.cnr_number is not null and m.cnr_number != '' then 1 else 0 end) as with_cnr
		from `tabLegal Matter` m
		left join `tabLegal Vertical` v on v.name = m.vertical
		{0}
		group by m.vertical, v.vertical_name, m.status
		order by `count` desc
		""".format(
			vertical_filter
		),
		params,
		as_dict=1,
	)
	return [dict(r) for r in rows]


@frappe.whitelist()
def report_upcoming_hearings(from_date=None, vertical=None, source=None):
	"""Upcoming Hearings report rows (mirrors chamber/report/upcoming_hearings)."""
	from frappe.utils import date_diff, getdate

	query_filters = {"hearing_date": (">=", from_date or getdate())}
	if vertical:
		matters = [
			m.name
			for m in frappe.db.get_all("Legal Matter", filters={"vertical": vertical}, fields=["name"])
		]
		if not matters:
			return []
		query_filters["legal_matter"] = ["in", matters]
	if source:
		query_filters["source"] = source

	hearings = frappe.db.get_all(
		"Hearing",
		filters=query_filters,
		fields=["name", "legal_matter", "hearing_date", "purpose", "court", "source"],
		order_by="hearing_date asc",
		limit=500,
	)
	matter_titles = {
		m.name: (m.matter_title, m.status)
		for m in frappe.db.get_all(
			"Legal Matter",
			filters={"name": ["in", [h.legal_matter for h in hearings]]},
			fields=["name", "matter_title", "status"],
		)
	}
	courts = {c.name: c.court_name for c in frappe.db.get_all("Court", fields=["name", "court_name"])}

	data = []
	for h in hearings:
		title, status = matter_titles.get(h.legal_matter, ("", ""))
		data.append(
			{
				"hearing_date": str(h.hearing_date),
				"days_left": date_diff(h.hearing_date, getdate()),
				"matter": h.legal_matter,
				"matter_title": title,
				"purpose": h.purpose,
				"court": courts.get(h.court) or h.court,
				"source": h.source,
				"matter_status": status,
			}
		)
	data.sort(key=lambda r: r["days_left"])
	return data


@frappe.whitelist(allow_guest=True)
def global_search(query):
	"""Quick matter lookup for the portal search overlay (Ctrl+K)."""
	query = (query or "").strip()
	if not query:
		return []
	rows = frappe.get_all(
		"Legal Matter",
		fields=["name", "matter_title", "case_number", "cnr_number", "status"],
		or_filters=[
			["name", "like", f"%{query}%"],
			["matter_title", "like", f"%{query}%"],
			["case_number", "like", f"%{query}%"],
			["cnr_number", "like", f"%{query}%"],
		],
		order_by="modified desc",
		limit_page_length=8,
	)
	return [dict(r) for r in rows]


@frappe.whitelist()
def run_action(doctype, name, method, args=None):
	"""Run an allowlisted whitelisted controller method from the portal.

	Only (doctype, method) pairs in DOC_ACTIONS are accepted, and the caller
	must be able to read the document.
	"""
	if (doctype, method) not in DOC_ACTIONS:
		frappe.throw("Not permitted", frappe.PermissionError)

	doc = frappe.get_doc(doctype, name)
	if not doc.has_permission("read"):
		frappe.throw("Not permitted", frappe.PermissionError)

	if isinstance(args, str):
		import json

		try:
			args = json.loads(args)
		except ValueError:
			args = None

	if isinstance(args, dict) and args:
		response = doc.run_method(method, **args)
	else:
		response = doc.run_method(method)
	return response
