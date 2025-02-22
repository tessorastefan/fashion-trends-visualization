from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup

# Configure Selenium WebDriver
options = Options()
options.headless = True  # Run in headless mode (no visible browser)
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_vogue(num_pages=3):
    articles = []
    
    for page in range(1, num_pages + 1):
        url = f"https://www.vogue.com/fashion?page={page}"
        print(f"Scraping page: {url}")

        driver.get(url)
        time.sleep(5)  # Allow time for JavaScript to load content

        # Scroll to ensure all articles are loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Find all article elements
        article_elements = driver.find_elements(By.CLASS_NAME, "summary-item__hed-link")

        print(f"Found {len(article_elements)} articles")

        for article in article_elements:
            title = article.text.strip()
            link = article.get_attribute("href")

            if title and link:
                articles.append({"Title": title, "Link": link})

    return pd.DataFrame(articles)

# Run scraper
df_vogue = scrape_vogue(3)

# Close WebDriver
driver.quit()

if df_vogue.empty:
    print("No data was scraped. Try checking Vogue’s website manually again.")
else:
    print(df_vogue.head())
    df_vogue.to_csv("vogue_fashion_articles.csv", index=False)

def scrape_article_content(article_url):
    response = requests.get(article_url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract publication date
    date_tag = soup.find("time")
    date = date_tag.text.strip() if date_tag else "Unknown"

    # Extract author
    author_tag = soup.find("span", class_="byline__name")  # Update class based on Vogue's structure
    author = author_tag.text.strip() if author_tag else "Unknown"

    # Extract article text
    paragraphs = soup.find_all("p")
    content = " ".join([p.text for p in paragraphs])

    return {"Date": date, "Author": author, "Content": content}

# Apply function to all scraped articles
df_vogue["Details"] = df_vogue["Link"].apply(scrape_article_content)

# Expand into separate columns
df_vogue = df_vogue.dropna().reset_index(drop=True)
df_vogue = pd.concat([df_vogue.drop(columns=["Details"]), df_vogue["Details"].apply(pd.Series)], axis=1)

df_vogue.to_csv("vogue_fashion_articles_full.csv", index=False)