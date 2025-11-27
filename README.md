# JICK

## General information

Jick is a web-spider that can crawl websites 'intelligently'. 
Whereas normal crawlers will generally not submit GET or POST forms
(thereby failing to crawl significant portions of the targeted
websites), Jick has the ability to intelligently generate
form data for GET and POST forms which it then submits in order
to facilitate crawling.

Jick can generate form data for text input, passwords, emails,
textareas, radio buttons, checkboxes, select drop-down menus, e.t.c.

It outputs a simple text file which contains a list of discovered
URLs, query parameter names and values, and either "GET" or "POST"
depending on whether the parameter names/values are sent in a
GET or POST request, respectively.

## Usage


Edit the form_parameters.ini file to alter how Jick will generate
data for form submissions. Or just stick with the default settings,
which will probably work well, in most cases.

Then, Jick can be used in the command-line

``
./jick.py --urls https://www.example.com/ --href --iframe --robots --site-map --get --post --output crawler_output.txt
``

or

``
python jick.py --urls https://www.example.com --href --iframe --output crawler_output.txt
``

The following arguments are supported:

``
--urls
``

Used to declare what URLs to begin crawling at. You may supply a single URL, or a comma-separated list, such as:

``
./jick.py --urls https://www.example.com,https://www.example.com/nowhere.html,https://www.example.com/nowhere/nowhere.php
``

Just be sure that all of the supplied URLs are for the same hostname.

``
--href
``

Extracts links from href attributes in anchor tags.

``
--iframe
``

Extracts iframe sources, e.g <iframe src='https://www.example/'/>

``
--get
``

Generates form submission data, submits forms for, and crawls GET forms.

``
--post
``

Does the same thing as --get, but for POST forms.

``
--robots
``

Crawls and scrapes robots.txt

``
--site-map
``

Crawls and scrapes sitemap.xml

``
--user-agent "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
``

Sets the User-Agent header for the crawler. The crawler also has a default user agent that disguise it as a regular desktop
browser.

``
--proxy 127.0.0.1:8080
``

Sets a proxy. In this case, 127.0.0.1:8080
Does not work with HTTPS.

``
--max-time 180
``

Sets the maximum time to crawl, in seconds. This value may be slightly exceeded, because the crawler may be in the middle of
visiting a web page when the maximum time limit is reached. The default is 10 minutes (600 seconds).

``
--max-results 100
``

Stops crawling after 100 pages have been located. This does not mean all 100 pages have been visited and crawled; it just
simply means the page has been located.

In practice, when the crawler finishes, it may output well over whatever the line number is that you specify. If, for
example, it currently has located 95 URLs, but then scrapes data for 1 more page and then locates another 20 URLs, it will
add all 20 of these new URLs to the list of URLs it has discovered, and it will output all 115 of them.

``
--timeout
``

Sets the timeout for each HTTP request. If the timeout is reached, the crawler does not continue trying to visit that
particular page. The default is 5.

``
--min-delay
``

and

``
--max-delay
``

establishes a minimum and maximum delay (in seconds) to sleep for, after each HTTP request is made. The actual amount of time
spent sleeping will be a random value between the minimum and maximum delay.

Setting these 2 numbers to be the same will result in it not delaying at all. The default setting is having no delay at all.

``
--use-cookies
``

Tells the crawler to use cookies throughout the crawling session. By default, no cookies will be stored.

``
--output output.txt
``

Specifies the output file. If no filename is specified, a filename will be generated and used by the crawler.


## Contribution
This project was made by [VyperLabs](https://www.securityandpentesting.org/) at [https://www.securityandpentesting.org](https://www.securityandpentesting.org )

It's a small project, but feel free to submit a pull request, if you want to contribute.
