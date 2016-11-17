### Test for rss.py
# Should return RSS feed

from rss import rss

def test_rss():
    # Set vars
    url = 'http://registerguard.com/csp/cms/sites/rg/feeds/rss.csp'
    payload = {'pub': 'rg', 'section': 'local', 'area': 'Updates'}
    
    response = rss(url, payload)
    print response
    assert (len(response))
    
