# ensure python is installed in the PATH environment variable
# pip install requests
import requests
# pip install beautifulsoup4
from bs4 import BeautifulSoup
import time
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# database connection
conn = pymysql.connect(
    host='127.0.0.1',
    user='flask_user',
    password=os.environ.get('DB_PASSWORD'),
    database='project_explorer_db',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = conn.cursor()

# ------------------------------ Obtaining Project URLs ------------------------------ #
# base URL for concatenation purposes
base_url = "https://eecs.engineering.oregonstate.edu/capstone/submission/"
# contains ALL projects (including ones not in just CS 467)
browse_projects_url = base_url + "pages/browseProjects.php"

# HTTP GET request
response = requests.get(browse_projects_url)
# converts response from bitstream into readable text
html_string = response.text

# parses the response text
soup = BeautifulSoup(html_string, "html.parser")

""" Filtering for CS 467 Projects Only"""

project_links = []
project_links.clear()

# finds the div class "masonry-brick"/"masonry-brick reqNDA"
for project in soup.select(".masonry-brick"):
    filter = project.select_one(".card-body .text-muted")

    if filter:
        # strip=True removes all excess whitespace (including tab and newlines)
        text = filter.get_text(strip=True)

        if "Courses: CS467" in text:
            a_tag = project.select_one("a")

            if a_tag:
                project_links.append(base_url + a_tag.get("href"))

print(f"Found {len(project_links)} CS467 projects")
time.sleep(5)

# ------------------------------ Obtaining Individual Project Details ------------------------------ #
# loop through each project link
for project_link in project_links:
    response = requests.get(project_link)
    html_string = response.text
    soup = BeautifulSoup(html_string, "html.parser")

    filter = soup.select_one(".viewSingleProject")
    if filter:
        text = filter.select_one("h1")
        title = text.get_text(strip=True)

        # insert into database, skip if already exists
        cursor.execute("""
            INSERT INTO projects (title, url)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE title = title
        """, (title, project_link))
        conn.commit()
        print(f"Inserted: {title}")

    time.sleep(1)

cursor.close()
conn.close()
print("Done")