import re
import configparser
import crawler_generator

from lxml import html
from urllib import parse
from time import sleep
from random import choice

config = configparser.ConfigParser()
config.read("form_parameters.ini")

get_submissions = int(config["GET"]["Submissions"])
post_submissions = int(config["POST"]["Submissions"])

# returns True or False, depending on whether the supplied URL matches the host
def isValidHost(host, url):

	parsed_url = parse.urlparse(url)
	if parsed_url.hostname == host:
		return True
	return False

# returns True or False, depending on whether the supplied URL is absolute or not
def isAbsoluteUrl(url):

	scheme_pattern = "^https?\\:\\/\\/"
	if re.search(scheme_pattern, url):
		return True
	return False

# given the scheme and host, it returns the absolute URL as a string
def getAbsoluteUrl(scheme, host, url):

	if not isAbsoluteUrl(url):
		return scheme + "://" + host + "/" + re.sub("^\\/", "", url)
	return url

# returns True if the given URL has already been recorded, and false if not
# if it returns False, we will want to add the URL to our list of discovered URLs
# It only examines the URL type (e.g if it's a "GET" or "POST" URL) as well as the parameter names
# This means if 2 URLs have all the same parameter names but different parameter values, this function will still return True
# Also, if 2 URLs have the same path, but 1 is a GET request and the other uses POST, this function will return False
def isOldUrl(old_urls, url):

	parsed_url = parse.urlparse(url["body"])
	parameters = parsed_url.query.split("&")

	for index in range(0, len(parameters)):
		parameters[index] = re.sub("\\=.*", "", parameters[index]) # replace all parameter values with a null string, so we just have parameter names

	parameters.sort() # this is necessary, so it will produce the same string, every time

	for old_url in old_urls:

		if old_url["type"] != url["type"]:
			continue

		old_parsed_url = parse.urlparse(old_url["body"])
		old_parameters = old_parsed_url.query.split("&")

		for index in range(0, len(old_parameters)):
			old_parameters[index] = re.sub("\\=.*", "", old_parameters[index])

		old_parameters.sort()

		if parameters == old_parameters:
			return True

	return False


# given a query string (e.g "user=Alice&password=whatever") convert it into a dictionary
def getDictionaryFromQueryString(query_string):

		parameters = query_string.split("&")
		parameter_dict = {}

		for parameter in parameters:

			parsed_parameter = parameter.split("=")
			if len(parsed_parameter) != 2:
				continue

			parameter_name = parsed_parameter[0]
			parameter_value = parsed_parameter[1]

			parameter_dict[parameter_name] = parameter_value

		return parameter_dict

# do everything related to managing session settings, all in 1 convenient place
# so that this can all be executed with 1 line of code, i.e by calling this function
# clears cookies (if applicable) and implements the browser-delay (if applicable)
def manageSession(use_cookies=True, min_delay=0, max_delay=0, session=0):

	if not use_cookies:
		session.cookies.clear()

	if min_delay < max_delay:
		sleep(choice(range(min_delay, max_delay)))

# given the HTML text, extracts links given a tag and attribute name, e.g "a" and "href" or "iframe" and "src"
def extractLinks(tree, tag="a", attr="href", scheme="https", host="www.example.com", old_urls=[]):

	links_found = []
	xpath_query = "//" + tag + "[@" + attr + "]"
	xpath_results = tree.xpath(xpath_query)

	for xpath_result in xpath_results:

		absolute_link = getAbsoluteUrl(scheme, host, xpath_result.attrib[attr])
		if not isValidHost(host, absolute_link):
			continue

		complete_link = {}
		complete_link["type"] = "GET"
		complete_link["body"] = absolute_link

		if isOldUrl(old_urls, complete_link):
			continue

		links_found.append(complete_link)

	links_found = crawler_generator.stripRedundancies(links_found)
	return links_found

# extract URLs from robots.txt
def extractRobotsUrls(scheme, host, session, timeout=3, old_urls=[], proxy={}):

	host = re.sub("\\/.*$", "", host)
	url = scheme + "://" + host + "/robots.txt"

	try:
		http_response = session.get(url, timeout=timeout, proxies=proxy)
		crawler_functions.manageSession(use_cookies=use_cookies, min_delay=min_delay, max_delay=max_delay, session=session)
	except:
		return []

	url_exp = "llow\\:\\s+[a-zA-Z0-9\\/\\-\\?\\&\\=\\%\\*\\.]+"
	found_url_paths = re.findall(url_exp, http_response.text)

	completed_urls = []

	for index in range(0, len(found_url_paths)):
		url_path = re.sub("^llow\\:\\s+", "", found_url_paths[index])

		if isOldUrl(old_urls, {"type":"GET", "body":scheme + "://" + host + url_path}):
			continue

		completed_urls.append({"type":"GET", "body":getAbsoluteUrl(scheme, host, url_path)})

	completed_urls = crawler_generator.stripRedundancies(completed_urls)

	return completed_urls

# parses HTML for sitemap data, useful for crawling /sitemap.xml pages
def extractSiteMap(session, scheme="https", host="www.example.com", old_urls=[], timeout=3, proxy={}):

	pages_found = []
	xpath_query = "//sitemap/loc"
	url = scheme + "://" + re.sub("\\/.+$", "", host) + "/sitemap.xml"

	try:
		http_response = session.get(url, timeout=timeout, proxies=proxy)
		crawler_functions.manageSession(use_cookies=use_cookies, min_delay=min_delay, max_delay=max_delay, session=session)
	except:
		return []

	try:
		http_response_text = http_response.text
		http_response_text = http_response_text.encode()
	except:
		pass

	tree = html.fromstring(http_response_text)
	xpath_results = tree.xpath(xpath_query)

	for xpath_result in xpath_results:

		text_content = xpath_result.text_content()

		if not re.search("^(http|https|ftp)\\:\\/\\/", text_content):
			# just in case some other garbage is put inside of the <sitemap><loc> tags, that is not a valid URL
			continue

		if not isValidHost(host, text_content):
			continue

		if isOldUrl(old_urls, {"type":"GET", "body":text_content}):
			continue

		pages_found.append({"type":"GET", "body":text_content})

	pages_found = crawler_generator.stripRedundancies(pages_found)
	return pages_found

# returns a list of HTML texts, containing all of the data in a <form> tag, as long as the action path is either relative or references the given host
# form_type = either 'get' or 'post'
def extractForms(tree, form_type="GET", scheme="https", host="www.example.com", old_urls=[]):

	forms_found = []
	xpath_query = "//form[@method='" + form_type.lower() + "' and @action]"
	xpath_results = tree.xpath(xpath_query)

	for xpath_result in xpath_results:

		try:
			form_action = xpath_result.attrib["action"]
		except:
			continue
			# this should only happen if no 'action' attribute is in the HTML <form> tag
			# which would be an invalid HTML form, and shouldn't happen
			# nonetheless, we don't want an invalid HTML form to crash our crawler because of inadequate error-handling on our part

		absolute_form_url = getAbsoluteUrl(scheme, host, form_action)
		if not isValidHost(host, absolute_form_url):
			continue

		if "?" not in absolute_form_url:
			absolute_form_url += "?"

		if "=" in absolute_form_url and not absolute_form_url.endswith("&"):
			absolute_form_url += "&"

		# and now we want to extract all the parameter names from this form
		# and make sure that there isn't already a discovered URL that uses all of these same parameter names

		dummy_parameters = ""
		xpath_subquery = "//input[@name] | //textarea[@name] | //select[@name]"
		xpath_subresults = xpath_result.xpath(xpath_subquery)

		for xpath_subresult in xpath_subresults:
			dummy_parameters += xpath_subresult.attrib["name"] + "=null&"

		dummy_parameters = re.sub("\\&$", "", dummy_parameters)
		complete_url = {}
		complete_url["type"] = form_type.upper()
		complete_url["body"] = absolute_form_url + dummy_parameters

		if isOldUrl(old_urls, complete_url):
			continue

		forms_found.append(html.tostring(xpath_result))

	return forms_found

# does everything
# or at least everything you tell it to do
# extracts hrefs, iframes, generates and submits GET and POST forms
def harvestAllData(html_text, scheme="https", host="www.example.com", href=False, iframe=False, submit_get_forms=False, submit_post_forms=False, old_urls=[]):

	global get_submissions
	global post_submissions

	tree = html.fromstring(html_text.encode())

	link_data = []
	get_form_data = []
	post_form_data = []

	input_xpath_query = "//input[@type and @name and @type!='checkbox' and @type!='radio']"
	checkbox_xpath_query = "//input[@type='checkbox' and @name]"
	radio_xpath_query = "//input[@type='radio' and @name]"
	textarea_xpath_query = "//textarea[@name]"
	select_xpath_query = "//select[@name]"
	url_xpath_query = "//form[@action]"

	# collect hrefs
	if href:
		links = extractLinks(tree, "a", "href", scheme, host, old_urls)
	else:
		links = []

	# collect iframes
	if iframe:
		iframes = extractLinks(tree, "iframe", "src", scheme, host, old_urls)
	else:
		iframes = []

	# collect GET forms
	if submit_get_forms:
		get_forms = extractForms(tree, "GET", scheme, host, old_urls)
	else:
		get_forms = []

	# collect POST forms
	if submit_post_forms:
		post_forms = extractForms(tree, "POST", scheme, host, old_urls)
	else:
		post_forms = []


	# iterate through GET forms, generating URLS
	for get_form in get_forms:

		try:
			get_form = get_form.encode()
		except:
			pass

		form_tree = html.fromstring(get_form)
		form_inputs = form_tree.xpath(input_xpath_query)
		form_checkboxes = form_tree.xpath(checkbox_xpath_query)
		form_radios = form_tree.xpath(radio_xpath_query)
		form_textareas = form_tree.xpath(textarea_xpath_query)
		form_selects = form_tree.xpath(select_xpath_query)

		for counter in range(0, get_submissions):

			complete_parameter_string = ""

			form_action = form_tree.xpath(url_xpath_query)
			form_action = getAbsoluteUrl(scheme, host, form_action[0].attrib["action"])

			if "?" not in form_action:
				form_action += "?"

			if "=" in form_action and not form_action.endswith("&"):
				form_action += "&"

			for iteration in range(0, len(form_inputs)):
				complete_parameter_string += crawler_generator.generateInputParameter(form_inputs[iteration], iteration, "GET")

			for iteration in range(0, len(form_checkboxes)):
				complete_parameter_string += crawler_generator.generateCheckBoxParameter(form_checkboxes[iteration], iteration, "GET")

			for iteration in range(0, len(form_radios)):
				complete_parameter_string += crawler_generator.generateRadioParameter(form_radios[iteration], iteration, "GET")

			for iteration in range(0, len(form_textareas)):
				complete_parameter_string += crawler_generator.generateTextAreaParameter(form_textareas[iteration], iteration, "GET")

			for iteration in range(0, len(form_selects)):
				complete_parameter_string += crawler_generator.generateSelectParameter(form_selects[iteration], iteration, "GET")

			complete_parameter_string = re.sub("\\&$", "", complete_parameter_string) # replace the trailing '&' at the end
			get_form_data.append({"type":"GET", "body":form_action + complete_parameter_string})

	# and now do the same for the POST forms
	for post_form in post_forms:

		try:
			form_tree = form_tree.encode()
		except:
			pass

		form_tree = html.fromstring(post_form)
		form_inputs = form_tree.xpath(input_xpath_query)
		form_checkboxes = form_tree.xpath(checkbox_xpath_query)
		form_radios = form_tree.xpath(radio_xpath_query)
		form_textareas = form_tree.xpath(textarea_xpath_query)
		form_selects = form_tree.xpath(select_xpath_query)

		form_action = form_tree.xpath(url_xpath_query)
		form_action = getAbsoluteUrl(scheme, host, form_action[0].attrib["action"])

		for counter in range(0, post_submissions):

			complete_parameter_string = ""

			if "?" not in form_action:
				form_action += "?"

			if "=" not in form_action and not form_action.endswith("&"):
				form_action += "&"

			for iteration in range(0, len(form_inputs)):
				complete_parameter_string += crawler_generator.generateInputParameter(form_inputs[iteration], iteration, "POST")

			for iteration in range(0, len(form_checkboxes)):
				complete_parameter_string += crawler_generator.generateCheckBoxParameter(form_checkboxes[iteration], iteration, "POST")

			for iteration in range(0, len(form_radios)):
				complete_parameter_string += crawler_generator.generateRadioParameter(form_tree, iteration, "POST")

			for iteration in range(0, len(form_textareas)):
				complete_parameter_string += crawler_generator.generateTextAreaParameter(form_textareas[iteration], iteration, "POST")

			for iteration in range(0, len(form_selects)):
				complete_parameter_string += crawler_generator.generateSelectParameter(form_selects[iteration], iteration, "POST")

			complete_parameter_string = re.sub("\\&$", "", complete_parameter_string)
			post_form_data.append({"type":"POST", "body":form_action + complete_parameter_string})


	all_links = crawler_generator.stripRedundancies(links + iframes)

	for individual_link in all_links:
		link_data.append({"type":"GET", "body":individual_link})

	return all_links + get_form_data + post_form_data


# output crawled data to file
def outputDiscoveredUrls(output_filename, output_urls):
	handler = open(output_filename, "a")
	for url in output_urls:
		handler.write(url["type"] + " " + url["body"] + "\n")
	handler.close()
