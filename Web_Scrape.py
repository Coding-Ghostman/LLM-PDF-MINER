from googlesearch import search
from bs4 import BeautifulSoup


from langchain_community.retrievers import ArxivRetriever
from langchain_community.document_loaders import PyMuPDFLoader


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC


def search_google(query, stop=10):
    links = []
    for link in search(query, tld="com", num=15, stop=stop, pause=1):
        links.append(link)
    return links


def scrape_data(url):
    service = Service(executable_path="./webdriver/chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--enable-javascript")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("prefs", {"download_restrictions": 3})
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=options, service=service)

    print(f"scraping url: {url}...")
    driver.get(url)

    delay = 3
    try:
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.TAG_NAME, "body")))
        print(f"Page is ready!")
    except TimeoutException:
        print("Loading took too much time!")

    # check if url is a pdf or arxiv link
    if url.endswith(".pdf"):
        loader = PyMuPDFLoader(url)
        text = str(loader.load())

    elif "arxiv" in url:
        doc_num = url.split("/")[-1]
        retriever = ArxivRetriever(load_max_docs=2)
        text = retriever.get_relevant_documents(query=doc_num)[0].page_content

    else:

        page_source = driver.execute_script("return document.body.outerHTML;")
        soup = BeautifulSoup(page_source, "html.parser")
        soup.encode(
            'utf-8', errors='ignore'
        ).decode('utf-8')

        # for script in soup(["script", "style"]):
        #     script.extract()

        text = ""
        tags = ["h1", "h2", "h3", "h4", "h5", "p"]
        for element in soup.find_all(tags):
            text += element.text + "\n"

    # For Creating individual tokens from the website
    # lines = (line.strip() for line in text.splitlines())
    # chunks = (token.strip() for line in lines for token in line.split(" "))
    # tokens = "\n".join(chunk for chunk in chunks if chunk)

    print("scraped data added")
    driver.quit()
    return text
