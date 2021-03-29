import requests
from bs4 import BeautifulSoup

def strip_tags(soup, tag):    
    while True:
        x = soup.find(tag)
        if type(x) == type(None):
            break
        else:
            soup.find(tag).decompose()
    soup.prettify()

def grab_src_url(url):
    _r = requests.get(url)
    soup = BeautifulSoup(_r.text, 'html5lib')
    
    if 'gmbinder.com' in url:
        src_btn = soup.find("a", {"class": "btn btn-default","title": "View Source"})
        if src_btn != None:
            return src_btn['href']
        else:
            return url
    
    elif 'homebrewery.naturalcrit.com' in url:
        src_btn = soup.find("a", {"class": "navItem teal","icon":"fas fa-code"})
        if src_btn != None:
            return "https://homebrewery.naturalcrit.com"+src_btn['href']
        else:
            return url


def collect_text(url):
    _r = requests.get(url)
    soup = BeautifulSoup(_r.text, 'html5lib')

    noisy_tags = ['head','img','script','campaign-manager-header','campaign-manager-footer','style']
    for tag in noisy_tags:
        strip_tags(soup, tag)
    
    if 'gmbinder.com' in url:
        txt_area = soup.find('textarea')
        if txt_area != None:
            return txt_area.text
        else:
            return soup.text
   
    elif 'homebrewery.naturalcrit.com' in url:
        return soup.text
    
    else:
        return None

def remove_html(txt):
    soup = BeautifulSoup(txt, 'html5lib')
    return soup.text