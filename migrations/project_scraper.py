# ensure python is installed in the PATH environment variable
# pip install requests
import requests
# pip install beautifulsoup4
from bs4 import BeautifulSoup
# pip install pymysql
import pymysql
import time
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    # connection to sql server
    connection = pymysql.connect(
        host='127.0.0.1',
        user='flask_user',
        password=os.environ.get('DB_PASSWORD'),
        database='project_explorer_db',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = connection.cursor()

    # base URL for concantenation purposes
    base_url = "https://eecs.engineering.oregonstate.edu/capstone/submission/"
    # contains ALL projects (including ones not in just CS 467)
    browse_projects_url = base_url + "pages/browseProjects.php"

    # obtains each project's url and puts them in a list
    project_urls = []
    project_urls = get_urls(base_url, browse_projects_url)

    # calls scrape function for each project then inserts into the database
    for project_url in project_urls:
        title, description, details = scrape(project_url)
        insert_project(connection, title, description, details, project_url)
        connection.commit()
        time.sleep(1)

    cursor.close()
    connection.close()


#------------------------------ Project URL Scraper Function ------------------------------#
# will get each project's url
def get_urls(base_url, browse_projects_url):
    # HTTP GET request
    response = requests.get(browse_projects_url)
    # converts response from bitstream into a readable text
    html_string = response.text
    # parses the response text?
    soup = BeautifulSoup(html_string, "html.parser")

    project_urls = []

    """ Filtering for CS 467 Projects Only"""
    # finds the div class "masonry-brick"/"masontry-brick reqNDA"
    for project in soup.select(".masonry-brick"):
        filter = project.select_one(".card-body .text-muted")
        
        if filter:
            # strip=True removes all excess whitespace (including tab and newlines)
            text = filter.get_text(strip=True)
            
            if "Courses: CS467" in text:
                a_tag = project.select_one("a")
                
                if a_tag:
                    project_urls.append(base_url + a_tag.get("href"))
                    time.sleep(1)

    return project_urls
#------------------------------ Project URL Scraper Function ------------------------------#


#------------------------------ Scrape Function ------------------------------#
# will get the title, objectives, motivations, and details
def scrape(url):
    response = requests.get(url)
    html_string = response.text
    soup = BeautifulSoup(html_string, "html.parser")

    # title
    title_filter = soup.select_one(".viewSingleProject h1")
    if title_filter:
        title = title_filter.get_text(strip=True)
    else:
        None

    # title_desc/summary, div class = .col-lg-12
    # part of everything under the title/h1 tag

    # description (keep format)
    description_filter = soup.select_one(".col-md-8.mb-5")
    if description_filter:
        description = str(description_filter)
    else:
        None

    # details (keep format)
    details_filter = soup.select_one(".col-md-4.mb-5")
    if details_filter:
        details = str(details_filter)
    else:
        None

    return title, description, details
#------------------------------ Scrape Function ------------------------------#


#------------------------------ SQL - Insert Project Info Function ------------------------------#
def insert_project(connection, title, description, details, url):
    with connection.cursor() as cursor:
        sql_script = """
                    insert into projects (title, description, details, url)
                    values (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE title = title
                    """
        cursor.execute(sql_script, (title, description, details, url))
        print(f"Inserted: {title}")
#------------------------------ SQL - Insert Project Info Function ------------------------------#


if __name__ == "__main__":
    main()
