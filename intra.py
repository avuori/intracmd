import httplib, urllib, sys, re
from datetime import datetime
from BeautifulSoup import BeautifulSoup

def error(s):
	sys.stderr.write(s + "\n")
	sys.exit(-1)


HOST = "intra.fast.sh"

passwd = open(".passwd", "r").read().split("\n")

try:
	USER = passwd[0]
	PASSWORD = passwd[1]
except IndexError:
	error("Invalid .passwd file.")

DAY_STARTS = "0900"
DAY_ENDS = "1630"

def _get_arg_or_default(n, default):
	if len(sys.argv) > n:
		return sys.argv[n]
	else:
		return default

now = datetime.now()

day = _get_arg_or_default(1, now.day)
month = _get_arg_or_default(2, now.month)
year = _get_arg_or_default(3, now.year)

print year, month, day, "%s-%s" % (DAY_STARTS, DAY_ENDS)


def _post(conn, target, params, session_id=None):
	headers = {"Content-Type": "application/x-www-form-urlencoded"}
	if session_id:
		headers["Cookie"] = session_id
	conn.request("POST", 
		     	 target, 
		     	 urllib.urlencode(params),
				 headers)
	r = conn.getresponse()
	return r.read(), conn, r.getheader("Set-Cookie", session_id)

def login():
	params = {"loginform": "1",
		      "loginstring": USER,
	       	  "user_pw": PASSWORD}
	conn = httplib.HTTPConnection(HOST)
	#conn.set_debuglevel(100)
	return _post(conn, "/index.php", params)

def open_timecard(*args):
	conn = args[1]
	session_id = args[2]
	params = {"mode": "data",
			  "action": "fills",
			  "ID": "",
			  "month": month,
			  "year": year,
			  "day": day,
			  "time": DAY_STARTS,
              "anfang": "",
              "x": "0",
              "y": "0"}
	return _post(conn, "/timecard/timecard.php", params, session_id)

def close_timecard(*args):
	resp = args[0]

	# Locate item id from the DOM
	soup = BeautifulSoup(resp)
	trs = soup.findAll("tr", ondblclick=re.compile(r"timecard\.php"))
	hiddens = trs[0].findAll("input", type="hidden")
	try:
		item_id = int(hiddens[2]["value"])
	except IndexError:
		error("Timecard was not opened.")

	conn = args[1]
	session_id = args[2]
	params = {"mode": "data",
			  "action": "fills",
			  "ID": item_id,
              "time": DAY_ENDS}
	return _post(conn, "/timecard/timecard.php", params, session_id)

def attach_hours(*args):
	conn = args[1]
	session_id = args[2]
	return "", conn

def close(*args):
	conn = args[1]
	conn.close()

close(
	*attach_hours(
		*close_timecard(
			*open_timecard(
				*login()))))
sys.exit(0)
