import asyncio
from bs4 import BeautifulSoup
from selenium import webdriver

driver = None

async def getYTData(query, count):
    global driver
    
    dataList = []
    
    options = webdriver.ChromeOptions()
    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1080,720')

    driver = webdriver.Chrome("D:\\ChromeDriver\\chromedriver", chrome_options=options)
    #driver.set_window_size(10, 10)
    driver.get("https://www.youtube.com/results?search_query=" + query)

    await asyncio.sleep(4)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    atag = soup.select("ytd-video-renderer #video-title")
    stag = soup.select("ytd-thumbnail-overlay-time-status-renderer")
    itag = soup.select("ytd-video-renderer ytd-thumbnail img")
    
    for i in range(0, count):
        dataList.append({
                    "title": str(atag[i].get_text().strip()),
                    "time": "[" + str(stag[i].get_text().strip()) + "]",
                    "img": str(itag[i].get("src")),
                    "url": "https://www.youtube.com" + str(atag[i].get("href"))
                    })
                    
    driver.close()
    
    return dataList

def genPlayList(list):
    res = ""
    for i in range(0, len(list)):
        res += str(i + 1) + "  Title: " + list[i]["title"] + "\tTime: " + list[i]["time"] + "\tURL: " + list[i]["url"]
        if (i < (len(list) - 1)):
            res += "\n"
            
    return res