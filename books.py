#  A SCRIPT THAT SCRAPE NAME, PRICE AND DESCRIPTION FROM A BOOKS SITE WEB THEN SAVE THE DATA IN DB WITH MYSQL

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import csv
import time
import mysql.connector
import re

class Scrape:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
        self.url = "https://books.toscrape.com/"
        self.driver.get(self.url)
        self.names = []
        self.prices = []
        self.description = []
        print("Attempting to connect to MySQL...")
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root123",  
                database="db"
            )
            self.cursor = self.connection.cursor()
            print("Database connection established.")
        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            self.connection = None

    def scroll_page(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        print("Scrolling completed, all content loaded.")

    def article_scraping(self):
        try:
            articles = WebDriverWait(self.driver, 30).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "product_pod"))
            )
            for article in articles:
                try:
                    article_name_element = article.find_element(By.XPATH, ".//h3/a")
                    article_name = article_name_element.text.strip()
                    if article_name:
                        article_name_element.click()

                        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                        product_main = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "col-sm-6.product_main"))
                        )
                        name = product_main.find_element(By.TAG_NAME, "h1").text.strip()
                        self.names.append(name)
                        print(f"Article Name : {name}")

                        value = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "price_color"))
                        ).text
                        price = value.replace("£", "").strip()
                        self.prices.append(price)
                        print(f"Article Price : {price}")

                        description = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//*[@id='content_inner']/article/p"))
                        ).text.strip()
                        self.description.append(description)
                        print(f"Article Description : {description}")

                        self.driver.back()
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "product_pod"))
                        )

                except Exception as e:
                    print(f"Erreur pour l'article {article_name} : {e}")
                    self.driver.back()

        except Exception as e:
            print(f"Erreur dans article_scraping : {e}")

    def scrape_all_pages(self):
        print(f"Scraping page : ")
        self.article_scraping()

        current_page = 1
        max_pages = 2

        while current_page <= max_pages:
            print(f"Scraping page {current_page}")
            try:
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "next"))
                ).find_element(By.TAG_NAME, "a")
                
                if "disabled" not in next_button.find_element(By.XPATH, "..").get_attribute("class"):
                    next_button.click()
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "product_pod"))
                    )
                    self.article_scraping()
                    current_page += 1
                else:
                    print("Bouton 'Next' désactivé, fin de la pagination.")
                    break
            except Exception as e:
                print(f"Fin de la pagination ou erreur : {e}")
                break

        self.save_to_csv()
        for name, price, description in zip(self.names, self.prices, self.description):
            self.import_to_db(name, price, description)
        print("data saved")

    def save_to_csv(self):
        with open('articles.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Nom de l'Article", "Price", "Description"])
            for name, price, description in zip(self.names, self.prices, self.description):
                writer.writerow([name, price, description])
        print("Données sauvegardées dans 'articles.csv'!")

    def import_to_db(self, name=None, price=None, description=None):
        if self.connection is None or not self.connection.is_connected():
            print("No active database connection.")
            return
        try:
            sql = "INSERT INTO laptops (name, price, description) VALUES (%s, %s, %s)"
            values = (name, price, description)
            self.cursor.execute(sql, values)
            self.connection.commit()
            print(f"Imported to DB: {name}")
        except mysql.connector.Error as e:
            print(f"DB error: {e}")

    def filter_data_with_price(self):
        try:
            self.cursor.execute("SELECT * FROM laptops WHERE price >= 20 ORDER BY price ASC") #DESC =! ASC
            rows = self.cursor.fetchall()
            print("\nData in laptops table: ")
            for row in rows:
                print(f"ID: {row[0]}, Name : {row[1]}, Price : {row[2]}")
        except mysql.connector.errors as e:
            print(f"Error fetching data {e}")
    
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Database connection closed.")
        self.driver.quit()

if __name__ == "__main__":
    scraper = Scrape()
    scraper.add_article()
    scraper.close()