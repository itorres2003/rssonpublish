import os, re, logging, logging.handlers, requests, feedparser, tweepy, json, bitly_api
from sys import exit

# logger
logger = logging.getLogger('logger')

# ----------------------------------------------------------------------------------------
# SECRETS
# ----------------------------------------------------------------------------------------

def getSecret(service, token='null'):
    
    secrets_path = os.path.join(os.path.abspath(os.path.dirname(__file__)))
    #print "Service: {}".format(service)
    #print "Token: {}".format(token)
    with open("{}/secrets.json".format(secrets_path)) as data:
        s = json.load(data)
        #print s
        #print s['{}'.format(service)]['{}'.format(token)]
        # If there is no token, return whole parent object
        if token == 'null':
            secret = s['{}'.format(service)]
        else:
            secret = s['{}'.format(service)]['{}'.format(token)]
        logger.debug("EXIT secrets: {}".format(len(secret)))
        return secret

# ----------------------------------------------------------------------------------------
# RSS
# ----------------------------------------------------------------------------------------

def getrss(url, payload):
    
    # Make request
    # See: http://stackoverflow.com/a/16511493
    try:
        r = requests.get(url, params=payload, timeout=5)
        logger.debug("rss success")
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        print e
        logger.error("Requests error: {}".format(e))
    
    #print r.url
    html = r.text
    
    # Parse the RSS
    feed = feedparser.parse(html)
    logger.debug("EXIT rss: Feed length {}".format(len(feed)))
    return feed
    

# ----------------------------------------------------------------------------------------
# BITLY
# ----------------------------------------------------------------------------------------

def getURL(full_url):
    logger.debug("ENTER bitly")
    # Get access token from bitly object in secrets.json
    access_token = getSecret('bitly','access_token')
    
    # See: https://github.com/bitly/bitly-api-python
    bitly = bitly_api.Connection(access_token=access_token)
    try:
        bitlyurl = bitly.shorten(full_url)
        #print bitlyurl
        shorturl = str(bitlyurl[u'url'])
        logger.debug("ShortURL: {}".format(shorturl))
        #print "success"
    except bitly_api.bitly_api.BitlyError, err:
        shorturl = full_url
        logger.error(err)
        #print "Error: {}".format(err)
    logger.debug("EXIT bitly: {}".format(shorturl))
    return shorturl
    

# ----------------------------------------------------------------------------------------
# TEST FOR BAD HEADLINE
# ----------------------------------------------------------------------------------------

def testBadHed(hed):
    logger.debug("ENTER testBadHed()")
    # Set up regex, see docs/regex.py for more
    regex = '([a-zA-Z0-9]\.[a-zA-Z0-9]+\.[x0-9])|(^Hed\s|\shed\s)|(\shery$|\sherey$)'
    
    if re.search(regex,hed):
        # Log it
        logger.error("Bad headline: {0}".format(hed.encode('utf-8')))
        # This should send email from wave
        print "Bad headline: {0}".format(hed.encode('utf-8'))
        # Return hed as nothing so that if statement in main fails
        hed = ""
    
    logger.debug("EXIT testBadHed()")
    return hed
    

# ----------------------------------------------------------------------------------------
# TWEET
# ----------------------------------------------------------------------------------------

# Set vars for trimming punctuation off of headline
# Example: "Oregon Promise" aid for community college students went heavily to middle- and upper-income families,... #rgnews http://rgne.ws/2l76Y5j
enders = (u',', u'.', u'!', u'?')
connectors = (u' &', u' -', u'\u2014') # emdash
punctuation = enders + connectors

def removePunctuation(hed):
    logger.debug("ENTER removePunctuation()")
    if hed.endswith(enders):
        # Remove last character
        hed = hed[:-1]
    elif hed.endswith(connectors):
        # Remove last two characters
        hed = hed[:-2]
    
    # Check again, enter recursion if necessary
    if hed.endswith(punctuation):
        hed = removePunctuation(hed)
    
    logger.debug("EXIT removePunctuation()")
    return hed

def trim(hed):
    logger.debug("ENTER trim()")
    # While head is longer than 105 characters
    while len(hed) > 105:
        # Split string into list of words
        hedl = hed.split()
        # Pop off the last word
        hedl.pop()
        # Join list back into string
        hed = " ".join(hedl)
        # Repeat popping words until string less than 105 characters
        
    # Check for punctuation
    if hed.endswith(punctuation):
        hed = removePunctuation(hed)
    
    # Add ellipsis character
    hed = hed + u"\u2026"
    logger.debug("EXIT trim()")
    return hed

def hashtag(scripttype):
    hasht = ""
    if scripttype == "twitter-news":
        hasht = "#RGnews"
    elif scripttype == "twitter-NEW-news":
        hasht = "#RGnews"
    elif scripttype == "twitter-sports":
        hasht = "#RGsports"
    elif scripttype == "twitter-staging":
        hasht = "#RGstage"
    return hasht

def sendit(feed_url, feed_title, scripttype):
    logger.debug("ENTER tweet")
    success = False
    
    if len(feed_title) > 105:
        feed_title = trim(feed_title)
        logger.debug("trim headline")
    
    # Encode headline if there are any fancy characters, such as ellipsis used in trim()
    feed_title = feed_title.encode('utf-8')
    
    hasht = hashtag(scripttype)
    
    # Get access token from secrets.json
    secrets = getSecret(scripttype)
    consumer_key = secrets['consumer_key']
    consumer_secret = secrets['consumer_secret']
    access_token = secrets['access_token']
    access_token_secret = secrets['access_token_secret']
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    
    #bitly
    shorturl = getURL(feed_url)
    
    # construct string to tweet
    tweet_text = "{0} {1} {2}".format(feed_title, shorturl, hasht)
    
    # Comment out this line to not send the tweet
    try:
        # Comment out line below to not send tweet each test...
        # would be nice to make this a test variable or something
        #api.update_status(status=tweet_text) # Uncomment this to go live
        print tweet_text
        success = True
        #logger.debug('Success! Tweet sent: ' + tweet_text)
        logger.error('Success! Tweet sent: ' + tweet_text)
    except tweepy.TweepError, err:
        logger.error(err)
        success = False
    logger.debug("EXIT tweet: {}".format(success))
    # Use success as return for now...
    # would rather return api status code...
    # See: https://github.com/registerguard/rssonpublish/issues/1
    return success
    
