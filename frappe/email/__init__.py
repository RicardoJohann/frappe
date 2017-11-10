# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.email.email_body import get_email
from frappe.email.smtp import send
from frappe.utils import markdown

def sendmail_md(recipients, sender=None, msg=None, subject=None, attachments=None, content=None,
	reply_to=None, cc=(), message_id=None, in_reply_to=None, retry=1, expose_recipients=None, is_notification=False):
	"""send markdown email"""
	sendmail(recipients, sender, markdown(content or msg), subject, attachments,
		reply_to=reply_to, cc=cc, retry=retry, expose_recipients=expose_recipients, is_notification = is_notification)

def sendmail(recipients, sender='', msg='', subject='[No Subject]', attachments=None, content=None,
	reply_to=None, cc=(), message_id=None, in_reply_to=None, retry=1, read_receipt=None, expose_recipients=None, is_notification=False):
	"""send an html email as multipart with attachments and all"""
	mail = get_email(recipients, sender, content or msg, subject, attachments=attachments,
		reply_to=reply_to, cc=cc, expose_recipients=expose_recipients)
	mail.set_message_id(message_id, is_notification)
	if in_reply_to:
		mail.set_in_reply_to(in_reply_to)

	if read_receipt:
		mail.msg_root["Disposition-Notification-To"] = sender
	send(mail, retry)

def sendmail_to_system_managers(subject, content):
	send(get_email(get_system_managers(), None, content, subject))

@frappe.whitelist()
def get_contact_list(txt):
	"""Returns contacts (from autosuggest)"""
	txt = txt.replace('%', '')

	def get_users():
		return filter(None, frappe.db.sql_list('select email from tabUser where email like %s',
			('%' + txt + '%')))
	try:
		out = filter(None, frappe.db.sql_list("""select distinct email_id from `tabContact` 
			where email_id like %(txt)s or concat(first_name, " ", last_name) like %(txt)s order by
			if (locate( %(_txt)s, concat(first_name, " ", last_name)), locate( %(_txt)s, concat(first_name, " ", last_name)), 99999),
			if (locate( %(_txt)s, email_id), locate( %(_txt)s, email_id), 99999)""",
		        {'txt': "%%%s%%" % frappe.db.escape(txt),
	            '_txt': txt.replace("%", "")
		        })
		)
		if not out:
			out = get_users()
	except Exception, e:
		if e.args[0]==1146:
			# no Contact, use User
			out = get_users()
		else:
			raise

	return out

def get_system_managers():
	return frappe.db.sql_list("""select parent FROM tabUserRole
		WHERE role='System Manager'
		AND parent!='Administrator'
		AND parent IN (SELECT email FROM tabUser WHERE enabled=1)""")
