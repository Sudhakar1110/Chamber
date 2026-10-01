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
	"""Quick matter lookup for the portal search overlay (Ctrl+K).

	Guests always get an empty list so matters cannot be enumerated
	without signing in, and signed-in users only see matters their
	role and matter-level permissions allow (frappe.get_list applies
	the chamber permission query conditions).
	"""
	query = (query or "").strip()
	if not query or frappe.session.user == "Guest":
		return []
	rows = frappe.get_list(
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


# ---------------------------------------------------------------- Chamber Settings
SETTINGS_FIELDS = [
	"enable_ecourts_sync", "ecourts_api_url", "ecourts_app_code",
	"ecourts_ordersheet_url", "ecourts_causelist_url", "ecourts_judgments_url",
	"enable_portal_sync", "portal_endpoint_ip_india", "portal_endpoint_nclt_nclat",
	"portal_endpoint_state_rera", "enforce_matter_level_permissions",
	"webhook_secret", "enable_hearing_reminders", "default_reminder_days",
	"reminder_recipient_role", "enable_esign", "esign_provider", "esign_api_url",
	"esign_api_key", "esign_callback_url", "esign_callback_secret", "enable_ai",
	"ai_provider", "ai_api_url", "ai_api_key", "ai_model", "ai_max_tokens",
	"require_lawyer_review_sensitive",
]
SETTINGS_PASSWORD_FIELDS = {
	"webhook_secret", "esign_api_key", "esign_callback_secret", "ai_api_key",
}
CHAMBER_ROLES = ("Chamber Manager", "Advocate", "Filing Clerk")


def _require_manager():
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Not permitted", frappe.PermissionError)


@frappe.whitelist()
def get_settings():
	"""Chamber Settings values for the portal configuration form.

	Password fields are never returned; they are reported as "" and are
	left untouched on save when blank.
	"""
	_require_manager()
	doc = frappe.get_doc("Chamber Settings")
	data = {}
	for f in SETTINGS_FIELDS:
		data[f] = "" if f in SETTINGS_PASSWORD_FIELDS else doc.get(f)
	return data


@frappe.whitelist()
def save_settings(values):
	"""Persist Chamber Settings from the portal (System Manager only).

	Blank password values keep whatever is already stored.
	"""
	import json

	if isinstance(values, str):
		try:
			values = json.loads(values)
		except ValueError:
			values = None
	_require_manager()
	if not isinstance(values, dict):
		frappe.throw("Invalid settings payload")
	doc = frappe.get_doc("Chamber Settings")
	meta = frappe.get_meta("Chamber Settings")
	for f in SETTINGS_FIELDS:
		if f not in values:
			continue
		v = values[f]
		if f in SETTINGS_PASSWORD_FIELDS and (v is None or str(v).strip() == ""):
			continue
		df = meta.get_field(f)
		if df and (v is None or str(v).strip() == ""):
			# store empty numerics/links as NULL instead of "" (DB-safe)
			if df.fieldtype in ("Int", "Check", "Float", "Link"):
				v = 0 if df.fieldtype == "Check" else None
		doc.set(f, v)
	doc.flags.ignore_permissions = True
	doc.save()
	return {f: ("" if f in SETTINGS_PASSWORD_FIELDS else doc.get(f)) for f in SETTINGS_FIELDS}


# ---------------------------------------------------------------- portal-only mode
@frappe.whitelist()
def list_users():
	"""Portal users plus the current desk/portal mode of the chamber roles."""
	_require_manager()
	rows = frappe.get_all(
		"User",
		fields=["name", "full_name", "user_type", "enabled"],
		order_by="creation asc",
		limit_page_length=300,
	)
	roles = {}
	for role in CHAMBER_ROLES:
		roles[role] = bool(frappe.db.get_value("Role", role, "desk_access"))
	return {
		"users": [dict(r) for r in rows],
		"roles": roles,
		"portal_only": not any(roles.values()),
	}


@frappe.whitelist()
def set_portal_only(enabled):
	"""Toggle portal-only mode for the chamber.

	Flips Role.desk_access on the chamber roles, then recomputes every
	enabled user's user_type exactly the way Frappe's User.validate does
	(has_desk_access -> System User / Website User). Portal-only users
	are forced to sign in again and never see the desk again; System
	Managers (or anyone with another desk role) keep full desk access.
	"""
	from frappe.sessions import clear_sessions

	_require_manager()
	enable = str(enabled).strip() in ("1", "true", "True", "yes")
	want = 0 if enable else 1
	for role in CHAMBER_ROLES:
		if not frappe.db.exists("Role", role):
			continue
		role_doc = frappe.get_doc("Role", role)
		if int(role_doc.desk_access or 0) != want:
			role_doc.desk_access = want
			role_doc.flags.ignore_permissions = True
			role_doc.save()

	changed = []
	for row in frappe.get_all("User", filters={"enabled": 1}, fields=["name"]):
		if row.name in ("Administrator", "Guest"):
			continue
		user = frappe.get_doc("User", row.name)
		new_type = "System User" if user.has_desk_access() else "Website User"
		if new_type != user.user_type:
			frappe.db.set_value("User", user.name, "user_type", new_type)
			clear_sessions(user=user.name, force=True)
			changed.append(user.name)
	return {"enabled": enable, "changed_users": changed, "count": len(changed)}
