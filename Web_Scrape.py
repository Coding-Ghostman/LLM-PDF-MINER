from googlesearch import search
from bs4 import BeautifulSoup, Comment


from langchain_community.retrievers import ArxivRetriever
from langchain_community.document_loaders import PyMuPDFLoader


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import re


def search_google(query, stop=10):
    links = []
    for link in search(query, tld="com", num=15, stop=stop, pause=1):
        links.append(link)
    return links


def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style tags
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    # Remove unnecessary attributes
    for tag in soup():
        for attribute in ["class", "id", "name", "style"]:
            del tag[attribute]

    # Remove comments
    comments = soup.find_all(text=lambda text: isinstance(text, Comment))
    [comment.extract() for comment in comments]

    return soup.get_text()


def scrape_data(url):
    service = Service(executable_path=ChromeDriverManager().install())
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

    # Check if url is a pdf or arxiv link
    if url.endswith(".pdf"):
        loader = PyMuPDFLoader(url)
        text = str(loader.load())

    elif "arxiv" in url:
        doc_num = url.split("/")[-1]
        retriever = ArxivRetriever(load_max_docs=2)
        text = retriever.get_relevant_documents(query=doc_num)[0].page_content

    else:
        page_source = driver.execute_script("return document.body.outerHTML;")
        cleaned_text = clean_html(page_source)

    print("scraped data added")
    driver.quit()
    return cleaned_text
