import urllib2
from bs4 import BeautifulSoup
import locale
from collections import OrderedDict
from google import google

num_page = 2


def google_similarity(text1, text2):
    result = 0
    
    text1Search = google.search(text1, num_page)
    text2Search = google.search(text2, num_page)
    
    print( len(text1Search) )
    print( len(text2Search) )
    for a in text1Search:
		print(a.link)
    
    return result
    

google_similarity('hope','wish')
