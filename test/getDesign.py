import requests
from pyquery import PyQuery as pq
url="chrome-extension://lecdifefmmfjnjjinhaennhdlmcaeeeb/main.html#/"

resource=requests.get(url,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})
print(resource)


#根据上面的代码，写成一个函数
def getDesign(url):
    resource=requests.get(url,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})
    return resource
    # print(resource)
def getHtml(url):
    html=getDesign(url).text
    return html
def parseHtml(html):
    doc = pq(html)
    item_list = doc('#design-list > li')
    for item in item_list:
        title = pq(item).find('.design-name').text()
        href = 'https://www.behance.net' + pq(item).attr('data-project-permalink')
        print(title, href)