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
    """Connect to the database and seed CS467 projects from the Capstone portal."""
    connection = pymysql.connect(
        host='127.0.0.1',
        user='flask_user',
        password=os.environ.get('DB_PASSWORD'),
        database='project_explorer_db',
        cursorclass=pymysql.cursors.DictCursor
    )

    # base URL for concatenation purposes
    base_url = "https://eecs.engineering.oregonstate.edu/capstone/submission/"
    # contains ALL projects (including ones not in just CS 467)
    browse_projects_url = base_url + "pages/browseProjects.php"

    # obtains each project's url and puts them in a list
    project_urls = get_urls(base_url, browse_projects_url)

    # calls scrape function for each project then inserts into the database
    for project_url in project_urls:
        try:
            title, description, details = scrape(project_url)
            insert_project(connection, title, description, details, project_url)
            connection.commit()
        except Exception as e:
            print(f"Failed to process {project_url}: {e}")
        time.sleep(1)

    connection.close()
    print("Done")


# ------------------------------ Project URL Scraper Function ------------------------------ #
def get_urls(base_url, browse_projects_url):
    """Fetch and return a list of CS467 project URLs from the Capstone portal."""
    # HTTP GET request
    response = requests.get(browse_projects_url)
    # converts response from bitstream into a readable text
    html_string = response.text
    # parses the response text
    soup = BeautifulSoup(html_string, "html.parser")

    project_urls = []

    """ Filtering for CS 467 Projects Only"""
    # finds the div class "masonry-brick"/"masonry-brick reqNDA"
    for project in soup.select(".masonry-brick"):
        course_filter = project.select_one(".card-body .text-muted")

        if course_filter:
            # strip=True removes all excess whitespace (including tab and newlines)
            text = course_filter.get_text(strip=True)

            if "Courses: CS467" in text:
                a_tag = project.select_one("a")

                if a_tag:
                    project_urls.append(base_url + a_tag.get("href"))

    return project_urls
# ------------------------------ Project URL Scraper Function ------------------------------ #


# ------------------------------ Scrape Function ------------------------------ #
def scrape(url):
    """Scrape title, description, and details text from a single project page."""
    response = requests.get(url)
    html_string = response.text
    soup = BeautifulSoup(html_string, "html.parser")

    # title
    title_filter = soup.select_one(".viewSingleProject h1")
    if title_filter:
        title = title_filter.get_text(strip=True)
    else:
        title = None

    # description (extract text, not raw HTML)
    description_filter = soup.select_one(".col-md-8.mb-5")
    if description_filter:
        description = description_filter.get_text(separator=" ", strip=True)
    else:
        description = None

    # details (extract text, not raw HTML)
    details_filter = soup.select_one(".col-md-4.mb-5")
    if details_filter:
        details = details_filter.get_text(separator=" ", strip=True)
    else:
        details = None

    return title, description, details
# ------------------------------ Scrape Function ------------------------------ #


# ------------------------------ SQL - Insert Project Info Function ------------------------------ #
def insert_project(connection, title, description, details, url):
    """Insert a project into the database, updating fields if content has changed."""
    with connection.cursor() as cursor:
        sql_script = """
                    insert into projects (title, description, details, url, scraped_at)
                    values (%s, %s, %s, %s, current_timestamp)
                    on duplicate key update
                        updated_at = if(
                            values(title) <> title
                            or values(description) <> description
                            or values(details) <> details,
                            current_timestamp, updated_at),
                        title = if(values(title) <> title, values(title), title),
                        description = if(values(description) <> description, values(description), description),
                        details = if(values(details) <> details, values(details), details),
                        scraped_at = current_timestamp;
                    """
        cursor.execute(sql_script, (title, description, details, url))
        print(f"Inserted: {title}")
# ------------------------------ SQL - Insert Project Info Function ------------------------------ #


if __name__ == "__main__":
    main()
