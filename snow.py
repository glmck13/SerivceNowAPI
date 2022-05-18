#!/usr/bin/env python3

import sys
import os
import cgi
import json
import requests
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

APIHOST = os.getenv('APIHOST', '')
APIUSER = os.getenv('APIUSER', '')
APIPASS = os.getenv('APIPASS', '')
APIMETHOD = os.getenv('APIMETHOD', '')
APICONTENT= os.getenv('APICONTENT', '')
APIAUTH = HTTPBasicAuth(APIUSER, APIPASS)
APIPROXY = None

APIHOST = 'https://' + APIHOST

def nowhttp (uri, params, jid=None, payload=None, content="", method=""):

	headers = {}
	cookies = {}
	auth = APIAUTH

	if (jid):
		keys = jid.split(',')
		cookies["JSESSIONID"] = keys[0]
		if len(keys) > 1:
			headers["X-UserToken"] = keys[1]
			auth = None

	if not payload:
		if not method:
			method = "GET"
		reply = requests.request(method, APIHOST+uri, auth=auth, headers=headers, cookies=cookies, params=params, verify=False, proxies=APIPROXY)

	else:
		if not method:
			method = "POST"
		if content and content[0] == "@":
			content = content[1:]
			try:
				payload = open(payload, "rb").read()
			except:
				payload = None
		headers["Content-Type"] = content
		reply = requests.request(method, APIHOST+uri, auth=auth, headers=headers, cookies=cookies, params=params, verify=False, proxies=APIPROXY, data=payload)

	id = reply.cookies.get("JSESSIONID", cookies.get("JSESSIONID"))
	token = reply.headers.get("X-UserToken-Refresh", headers.get("X-UserToken"))
	if id:
		jid = id
		if token:
			jid += ',' + token

	return reply, jid
	
if __name__ == "__main__":

	form = cgi.FieldStorage()
	uri = form.getvalue('uri')
	save = form.getvalue('save')
	jid = form.getvalue('jid')
	export = form.getvalue('export')
	count = form.getvalue('count')
	fields = form.getvalue('fields')
	query = form.getvalue('query')
	action = form.getvalue('action')
	payload = form.getvalue('payload')
	content = form.getvalue('content')
	method = form.getvalue('method')

	banner = ""
	decode = True
	params = {}

	if export != "REST":
		params[export] = ""
		if fields:
			params["sysparm_fields"] = fields
		if count:
			params["sysparm_record_count"] = count
	else:
		if fields:
			for f in fields.split('&'):
				k = f.split('=')
				if len(k) > 1:
					params[k[0]] = k[1]
		if count:
			params["sysparm_limit"] = count

	if query:
		params["sysparm_query"] = query
	if action:
		params["sysparm_action"] = action

	if export in ("CSV", "XML"):
		params["sysparm_display_value"] = "true"
	elif export in ("JSONv2"):
		params["displayvalue"] = "all"
		params["displayvariables"] = "true"

	if payload:
		reply, jid = nowhttp(uri, params, jid, payload, content, method=method)
	else:
		reply, jid = nowhttp(uri, params, jid, method=method)

	if export == "XLSX":
		save = "yes"
		decode = False
		banner += "Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\n"
	elif export != "REST":
		banner += "Content-Type: text/plain\n"
	elif save == "yes":
		banner += "Content-Type: application/octet-stream\n"
		decode = False
	else:
		banner += "Content-Type: text/plain\n"

	if save == "yes":
		banner += "Content-Disposition: attachment; filename=snow.{}\n".format(export.lower())

	print("JSESSIONID = {}".format(jid), file=sys.stderr, flush=True)

	print(banner, flush=True)

	if export == "JSONv2":
		print(json.dumps(reply.json(), indent=4))
	elif decode:
		print(reply.content.decode("utf-8", "backslashreplace"))
	else:
		os.write(sys.stdout.fileno(), reply.content)
