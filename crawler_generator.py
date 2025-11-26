import configparser
import random
import datetime

from math import ceil

config = configparser.ConfigParser()
config.read("form_parameters.ini")

def stripRedundancies(array):

	# receive an array as input
	# and return an array with all redundancies removed, e.g
	# [1, 1, 1, 2, 2, 3, 4, 4, 5] becomes [1, 2, 3, 4, 5]

	new_array = []
	for item in array:
		if new_array.count(item) == 0:
			new_array.append(item)

	return new_array

# return a number, representing the current week
# it will be 01 - 53, zero-padded
# this will be based on non-leap years, so it may occasionally be off by 1, but for our purposes, who cares
def getCurrentWeek(now):

	month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
	days_passed = 0

	for counter in month_lengths[0:now.month - 1]:
		# this loop does not include the current month
		days_passed += counter

	days_passed += now.day
	current_week_of_year = ceil(days_passed / 7.0)

	if len(str(current_week_of_year)) == 1:
		current_week_of_year = int("0" + str(current_week_of_year))

	return current_week_of_year


# return the appropriate value from the list of options in the config file
def getParameterValueFromIterationNumber(variable_name, iteration=0, form_type="GET"):

	global config
	selection_method = config[form_type]["Method"]

	if variable_name in config[form_type]:
		values = config[form_type][variable_name]

	else:
		values = config[form_type]["default"]

	values = values.split(",")

	if selection_method == "random":
		return random.choice(values)

	values_len = len(values)

	while iteration >= values_len:
		iteration -= values_len

	return values[iteration]

def generateRadioParameter(tree, iteration=0, form_type="GET"):

	# since radio buttons for a given name may be spread across a large area and not necessarily grouped together in the HTML document,
	# the tree passed to this function will represent the entire <form> element, and not just a given radio selection
	# and this function will locate all the different radio elements and work from there

	xpath_query = "//input[@type='radio' and @name and @value]"
	xpath_results = tree.xpath(xpath_query)
	complete_parameter_string = ""
	radio_names = []

	for xpath_result in xpath_results:
		radio_names.append(xpath_result.attrib["name"])

	radio_names = stripRedundancies(radio_names)

	for index in range(0, len(radio_names)):

		radio_name = parameter_name = radio_names[index]
		new_xpath_query = "//input[@type='radio' and @name='" + radio_name + "' and @value]"
		new_xpath_results = tree.xpath(new_xpath_query)

		current_value = getParameterValueFromIterationNumber("Radio", index, form_type)

		if current_value == "first":
			parameter_value = new_xpath_results[0].attrib["value"]

		elif current_value == "last":
			parameter_value = new_xpath_results[-1].attrib["value"]

		elif current_value == "random":
			parameter_value = random.choice(new_xpath_results).attrib["value"]

		else:
			return ""

		complete_parameter_string += parameter_name + "=" + parameter_value + "&"

	return complete_parameter_string

def generateCheckBoxParameter(tree, iteration=0, form_type="GET"):

	complete_parameter_string = ""
	checkbox_name = parameter_name = tree.attrib["name"]
	current_value = getParameterValueFromIterationNumber("Checkbox", iteration, form_type)

	if current_value == "random":

		if random.choice([True, False]):
			if "value" in tree.attrib:
				parameter_value = tree.attrib["value"]
			else:
				parameter_value = "on"
		else:
			return ""

	elif current_value == "all":

		if "value" in tree.attrib:
			parameter_value = tree.attrib["value"]
		else:
			parameter_value = "on"

	elif current_value == "none":
		return ""

	else:
		return ""

	complete_parameter_string += parameter_name + "=" + parameter_value + "&"
	return complete_parameter_string

def generateSelectParameter(tree, iteration=0, form_type="GET"):

	parameter_name = tree.xpath("//select[@name]")[0].attrib["name"]
	current_value = getParameterValueFromIterationNumber("Select", iteration, form_type)
	no_default_value = False

	if current_value == "default":

		xpath_query = "//option[@selected and @value]"
		xpath_results = tree.xpath(xpath_query)

		if len(xpath_results) < 1:
			no_default_value = True
			# since the user configured the crawler to use the default value for any <select> field
			# but in this case, there is no select field,
			# we will instead select one of the other options at random
		else:
			parameter_value = xpath_results[0].attrib["value"]

	elif current_value == "first":

		xpath_query = "//option[@value]"
		xpath_results = tree.xpath(xpath_query)

		if len(xpath_results) == 0:
			parameter_value = ""
			# if this happens, it means there are no options with values inside this form
			# this shouldn't happen, because if it does, that means the crawled web page has invalid - or at least improper - HTML
			# and we don' want this to crash our crawler, so we'll just return without sending any data
		else:
			parameter_value = xpath_results[0].attrib["value"]

	elif current_value == "last":

		xpath_query = "//option[@value]"
		xpath_results = tree.xpath(xpath_query)

		if len(xpath_results) == 0:
			parameter_value = ""
			# same as above, this means there are literally no <option> tags to choose from
		else:
			parameter_value = xpath_results[-1].attrib["value"]

	elif current_value == "random" or no_default_value == True:

		xpath_query = "//option[@value]"
		xpath_results = tree.xpath(xpath_query)

		if len(xpath_results) == 0:
			parameter_value = ""
		else:
			parameter_value = random.choice(xpath_results).attrib["value"]

	elif current_value == "none":
		# this means it is a value of 'none'
		# so we will return nothing - no parameter name OR a parameter value
		return ""

	return parameter_name + "=" + parameter_value + "&"


def generateTextAreaParameter(tree, iteration=0, form_type="GET"):

	xpath_query = "//textarea[@name]"
	xpath_result = tree.xpath(xpath_query)
	parameter_name = xpath_result[0].attrib["name"]
	current_value = getParameterValueFromIterationNumber("Textarea", iteration, form_type)

	if current_value != "intelligence":
		return parameter_name + "=" + current_value + "&"

	if "maxlength" in xpath_result[0].attrib:
		try:
			maxlength = int(xpath_result[0].attrib["maxlength"])
		except:
			maxlength = 0

	else:
		maxlength = 0

	if maxlength == 0:
		# this is still another way in which we can determine what the maximum length is likely to be
		if "rows" in xpath_result[0].attrib and "cols" in xpath_result[0].attrib:
			try:
				maxlength = int(int(xpath_result[0].attrib["rows"]) * int(xpath_result[0].attrib["cols"]) * 0.5)
			except:
				maxlength = 50
		else:
			maxlength = 50

	# I figure that, for textareas, forms expect a longer string of text than they would expect for an <input type='text'/> tag
	# for this reason, we will generate a slightly longer string of text than we would for a normal <input type='text'/> tag

	parameter_value = ""
	chars = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

	for counter in range(0, maxlength-1):
		parameter_value += random.choice(chars)

	return parameter_name + "=" + parameter_value + "&"

def generateInputParameter(tree, iteration=0, form_type="GET"):

	input_type = tree.attrib["type"]
	input_name = tree.attrib["name"]

	current_value = getParameterValueFromIterationNumber(input_type, iteration, form_type)

	if current_value != "intelligence":

		# this means that, in the case of these input types, if the value is not 'intelligence',
		# it just uses the raw value provided in the .ini file as the parameter value, itself
		return input_name + "=" + current_value + "&"

	# If we haven't returned from this function yet, this means we must intelligently generate a parameter value
	# So let us begin by attempting to collect all the tag attributes that may be helpful for us, in doing so
	# And we will generate 'default' values, in case there is no information in the tag attributes

	if "maxlength" in tree.attrib:
		try:
			maxlength = int(tree.attrib["maxlength"])
		except:
			# I made this into a try/except clause just in case the website erroneously uses a non-numerical value for it's maxlength attribute
			# we wouldn't want that to crash our crawler
			maxlength = 10
	else:
		maxlength = 10


	if "placeholder" in tree.attrib:
		placeholder = tree.attrib["placeholder"]
	else:
		placeholder = ""


	if "min" in tree.attrib:
		try:
			min = int(tree.attrib["min"])
		except:
			min = 0
	else:
		min = 0


	if "max" in tree.attrib:
		try:
			max = int(tree.attrib["max"])
		except:
			max = 100
	else:
		max = 100


	if "value" in tree.attrib:
		value = tree.attrib["value"]
	else:
		value = ""

	# we may need the current time, as well
	now = datetime.datetime.now()

	# we may need some other constants as well, for randomized data generation
	letters = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
	numbers = list("0123456789")
	punctuation = list("!?.")
	# for passwords. I know there is more punctuation than this, but this will be safer, as some websites have passform submission forms that
	# forbid the use of more obscure punctuation marks, such as ^ or | or \ or ; 
	letters_and_numbers = letters + numbers
	all = letters + numbers + punctuation
	password_chars = "Ax1!By2?Cz3." * 10
	# this password character set contains a combination of uppercase and lowercase letters, numbers, and punctuation
	# all in a constant, unchanging order, so that the password will not be randomized
	# this is crucial, in case a single form contains more than one <input type='password'> field,
	# and requires 2 different password inputs to be identical

	# we now have a default value for the following attributes:
	# maxlength, min, max, placeholder, and value


	if input_type == "text" or input_type == "search":
		if placeholder:
			parameter_value = placeholder
		else:
			parameter_value = ""
			for counter in range(0, maxlength-1):
				parameter_value += random.choice(letters_and_numbers)

	elif input_type == "password":
		parameter_value = ""
		if maxlength > len(password_chars):
			maxlength = len(password_chars)
		for counter in range(0, maxlength-1):
			parameter_value += password_chars[counter]

	elif input_type == "tel":
		parameter_value = "8882804331"

	elif input_type == "url":
		parameter_value = "http://www.example.com/"

	elif input_type == "hidden":
		if len(value) > 1:
			parameter_value = value
		else:
			parameter_value = ""
			for counter in range(0, maxlength-1):
				parameter_value += random.choice(letters_and_numbers)

	elif input_type == "email":
		random_number = ""
		for counter in range(0, 4):
			random_number += str(random.choice(range(0, 10)))
		parameter_value = "nobody" + random_number + "@gmail.com"

	elif input_type == "date":
		parameter_value = str(now.year) + "-" + str(now.month) + "-" + str(now.day)

	elif input_type == "datetime-local":
		parameter_value = str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "T" + str(now.hour) + ":" + str(now.minute)

	elif input_type == "time":
		parameter_value = str(now.hour) + ":" + str(now.minute)

	elif input_type == "month":
		parameter_value = str(now.year) + "-" + str(now.month)

	elif input_type == "week":
		parameter_value = str(now.year) + "-W" + str(getCurrentWeek(now))

	elif input_type == "number" or input_type == "range":
		parameter_value = str(int((max - min) * 0.5))

	elif input_type == "color":
		parameter_value = "#2ec27e"

	else:
		parameter_value = value

	return input_name + "=" + parameter_value + "&"
