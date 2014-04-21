HttpRequestCapture
==================

RequestCapture, Combined HttpFox and FourthParty

Install:
1). ./build.sh name 
	Create a xpi file (Firefox extension) and install it on Firefox. It's highly suggested to install it on a clean profile. (you can start firefox with parameter -P)

2). This extension will create a new sqlite3 database (and remove the existing one) called "httpfox.sqlite" in the directory of current Firefox profile. For example, on Mac, the directory is in ~/Library/Application Support/Firefox/Profiles/profile_name

3). Once crawled all the URLs, copy the database to another location and use FindRedirection.py to get all the redirections.
