#!/usr/bin/python

import requests
import sys
import time
import datetime
import crawler_functions

from urllib import parse
from lxml import html

now = datetime.datetime.now()

# SETTINGS
if "--urls" not in sys.argv:
	print("You must enter a URL to start crawling at, with the --urls argument.")
	sys.exit(1)
else:
	try:
		start_urls = sys.argv[sys.argv.index("--urls")+1].split(",")
	except:
		print("Invalid URL specified.")
		sys.exit(2)

if "--href" in sys.argv:
	follow_hrefs = True
else:
	follow_hrefs = False

if "--iframe" in sys.argv:
	follow_iframes = True
else:
	follow_iframes = False

if "--get" in sys.argv:
	submit_get_forms = True
else:
	submit_get_forms = False

if "--post" in sys.argv:
	submit_post_forms = True
else:
	submit_post_forms = False

if "--robots" in sys.argv:
	robots = True
else:
	robots = False

if "--site-map" in sys.argv:
	site_map = True
else:
	site_map = False

if "--user-agent" in sys.argv:
	try:
		user_agent = sys.argv[sys.argv.index("--user-agent")+1]
	except:
		user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
else:
	user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

if "--use-cookies" in sys.argv:
	use_cookies = True
else:
	use_cookies = False

if "--proxy" in sys.argv:
	try:
		proxy_addr = sys.argv[sys.argv.index("--proxy")+1]
		proxy = {"http":proxy_addr, "https":proxy_addr, "ftp":proxy_addr}
	except:
		proxy = {}
else:
	proxy = {}

if "--min-delay" in sys.argv:
	try:
		min_delay = int(sys.argv[sys.argv.index("--min-delay")+1])
	except:
		min_delay = 0
else:
	min_delay = 0

if "--max-delay" in sys.argv:
	try:
		max_delay = int(sys.argv[sys.argv.index("--max-delay")+1])
	except:
		max_delay = int(min_delay * 3)
else:
	max_delay = int(min_delay * 3)

if (min_delay < 0) or (max_delay < 0) or (max_delay < min_delay):
	min_delay = max_delay = 0


if "--output" in sys.argv:
	try:
		output_file = sys.argv[sys.argv.index("--output")+1]
	except:
		output_file = "web_crawler_output_" + str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "_" + str(now.hour) + "_" + str(now.minute) + ".txt"
else:
	output_file = "web_crawler_output_" + str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "_" + str(now.hour) + "_" + str(now.minute) + ".txt"

if "--max-time" in sys.argv:
	try:
		max_time = int(sys.argv[sys.argv.index("--max-time")+1])
	except:
		max_time = 60 * 10
else:
	max_time = 60 * 10

if "--max-results" in sys.argv:
	try:
		max_results = int(sys.argv[sys.argv.index("--max-results")+1])
	except:
		max_results = 300
else:
	max_results = 300

if "--timeout" in sys.argv:
	try:
		timeout = int(sys.argv[sys.argv.index("--timeout")+1])
	except:
		timeout = 5
else:
	timeout = 5

if (follow_hrefs == False) and (follow_iframes == False) and (submit_get_forms == False) and (submit_post_forms == False) and (robots == False) and (site_map == False):
	print("Nothing to do. You must configure the crawler to either follow hrefs, iframes, submit get forms, or submit post forms, or call robots.txt (with the --href, --iframe, --get, --post, --robots or --site-map arguments, respectively)")
	sys.exit(3)

# All the information regarding the host
parsed_url = parse.urlparse(start_urls[0])

# Keep a record of the time the crawler began, so that we know when we want to quit
start_time = int(time.time())

# A list of all URLs (which includes GET forms) and all POST forms, found so far
discovered_urls = []

# Let us now construct our crawler
http_headers = {"User-Agent":user_agent, "Host":parsed_url.hostname}
session = requests.session()
session.headers.update(http_headers)

# Now we will crawl the first pages to (hopefully) yield more pages
for url in start_urls:

	try:
		http_response = session.get(url, timeout=timeout, proxies=proxy)
		crawler_functions.manageSession(use_cookies=use_cookies, min_delay=min_delay, max_delay=max_delay, session=session)
		discovered_urls += crawler_functions.harvestAllData(str(http_response.text), parsed_url.scheme, parsed_url.hostname, follow_hrefs, follow_iframes, submit_get_forms, submit_post_forms, discovered_urls)
	except:
		continue

# now we will crawl sitemap.xml, if site_map == True
if site_map == True:
	discovered_urls += crawler_functions.extractSiteMap(session, parsed_url.scheme, parsed_url.hostname, discovered_urls, timeout, proxy)

# now we will do robots.txt, if robots == True
if robots == True:
	discovered_urls += crawler_functions.extractRobotsUrls(parsed_url.scheme, parsed_url.hostname, session, timeout, discovered_urls, proxy)

# if no result were found, exit
if len(discovered_urls) == 0:
	print("Did not find any new URLs. Done.")
	sys.exit(4)

# And now we can finally begin crawling everywhere!

for url in discovered_urls:

	if url["type"] == "GET":

		try:
			http_response = session.get(url["body"], timeout=timeout, proxies=proxy)
		except:
			# this will probably only happen due to an HTTP timeout
			continue

	elif url["type"] == "POST":
		try:

			parsed_post_url = type["body"].split("?")
			if len(parsed_post_url) != 2:
				continue

			direct_url = parsed_post_url[0]
			post_parameters = parsed_post_url[1]
			post_parameters = crawler_functions.getDictionaryFromQueryString(post_parameters)

			http_response = session.post(direct_url, data=post_parameters, proxies=proxy)
		except:
			# again, this is presumably because of an HTTP timeout
			continue

	else:
		# this should never happen, but I will put this else clause in here, just in case
		continue

	crawler_functions.manageSession(use_cookies=use_cookies, min_delay=min_delay, max_delay=max_delay, session=session)

	try:
		discovered_urls += crawler_functions.harvestAllData(str(http_response.text), parsed_url.scheme, parsed_url.hostname, follow_hrefs, follow_iframes, submit_get_forms, submit_post_forms, discovered_urls)
	except ValueError:
		# just in case the HTML document is weird and lxml isn't able to parse it
		continue

	# and now to determine whether or not to exit the script

	if int(time.time()) - start_time > max_time:
		print("Maximum run-time reached. Exiting.")
		crawler_functions.outputDiscoveredUrls(output_file, discovered_urls)
		sys.exit(0)

	if len(discovered_urls) >= max_results:
		print("Maximum discovered URLs reached. Exiting.")
		crawler_functions.outputDiscoveredUrls(output_file, discovered_urls)
		sys.exit(0)

print("Finished crawling. Exiting.")
crawler_functions.outputDiscoveredUrls(output_file, discovered_urls)
sys.exit(0)
