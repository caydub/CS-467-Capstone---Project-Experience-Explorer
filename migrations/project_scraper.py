# Dependencies: requests, beautifulsoup4, pymysql, python-dotenv
# pip install requests beautifulsoup4 pymysql python-dotenv
import copy
import os
import time
from urllib.parse import urljoin

import pymysql
import requests
from bs4 import BeautifulSoup
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

    base_url = "https://eecs.engineering.oregonstate.edu/capstone/submission/"
    browse_projects_url = base_url + "pages/browseProjects.php"

    project_urls = get_urls(base_url, browse_projects_url)

    for project_url in project_urls:
        try:
            title, description, details, image_url = scrape(project_url)
            if title is None:
                print(f"Skipping {project_url}: could not extract title")
                continue
            insert_project(connection, title, description, details, image_url, project_url)
            connection.commit()
        except Exception as e:
            print(f"Failed to process {project_url}: {e}")
        time.sleep(1)

    connection.close()
    print("Done")


def get_urls(base_url, browse_projects_url):
    """Fetch and return a list of CS467 project URLs from the Capstone portal."""
    response = requests.get(browse_projects_url)
    soup = BeautifulSoup(response.text, "html.parser")

    project_urls = []

    # filter for CS 467 projects only; each card lives in a .masonry-brick div
    for project in soup.select(".masonry-brick"):
        course_filter = project.select_one(".card-body .text-muted")

        if course_filter and "Courses: CS467" in course_filter.get_text(strip=True):
            a_tag = project.select_one("a")
            if a_tag:
                project_urls.append(base_url + a_tag.get("href"))

    return project_urls


# Tags to keep when sanitizing scraped HTML; everything else is unwrapped (text preserved).
_ALLOWED_TAGS = {'h3', 'h4', 'h5', 'p', 'ul', 'ol', 'li', 'strong', 'em', 'b', 'i', 'br'}


def _clean_html(element):
    """Return sanitized inner HTML for a BeautifulSoup element.

    Keeps structural tags (headings, paragraphs, lists) and strips all attributes.
    Non-allowed tags (div, a, span, script, …) are unwrapped so their text survives.
    Processes leaves first so unwrapping never invalidates a parent reference.
    """
    el = copy.deepcopy(element)
    for tag in reversed(el.find_all(True)):
        if tag.name not in _ALLOWED_TAGS:
            tag.unwrap()
        else:
            tag.attrs = {}
    return el.decode_contents().strip()


def scrape(url):
    """Scrape title, description, details, and thumbnail image from a single project page."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    title_el = soup.select_one(".viewSingleProject h1")
    title = title_el.get_text(strip=True) if title_el else None

    # The intro copy lives in the hero banner (<p class="lead mb-5">).
    # The structured sections (Objectives, Motivations, Qualifications) are in .col-md-8.mb-5.
    # Combine both so the full description is shown on our page.
    lead_el = soup.select_one("p.lead.mb-5")
    sections_el = soup.select_one(".col-md-8.mb-5")
    lead_html = ('<h4>Overview</h4>\n' + _clean_html(lead_el)) if lead_el else None
    sections_html = _clean_html(sections_el) if sections_el else None
    parts = [p for p in (lead_html, sections_html) if p]
    description = '\n'.join(parts) if parts else None

    details_el = soup.select_one(".col-md-4.mb-5")
    details = _clean_html(details_el) if details_el else None

    # grab the project thumbnail — skip the generic fallback image.
    # images/ is relative to the submission root, not the pages/ subdirectory,
    # so resolve against base_url rather than the page URL.
    image_url = None
    img_el = soup.select_one(".viewSingleProject img")
    if img_el and img_el.get("src"):
        src = img_el["src"]
        if "capstone_test" not in src:
            base_url = "https://eecs.engineering.oregonstate.edu/capstone/submission/"
            image_url = urljoin(base_url, src)

    return title, description, details, image_url


def insert_project(connection, title, description, details, image_url, url):
    """Insert a project into the database, updating fields if content has changed."""
    with connection.cursor() as cursor:
        sql_script = """
            INSERT INTO projects (title, description, details, image_url, url, scraped_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP) AS new_row
            ON DUPLICATE KEY UPDATE
                updated_at = IF(
                    new_row.title <> projects.title
                    OR new_row.description <> projects.description
                    OR new_row.details <> projects.details,
                    CURRENT_TIMESTAMP, projects.updated_at),
                title = IF(new_row.title <> projects.title, new_row.title, projects.title),
                description = IF(
                    new_row.description <> projects.description,
                    new_row.description, projects.description),
                details = IF(
                    new_row.details <> projects.details, new_row.details, projects.details),
                image_url = IF(
                    new_row.image_url IS NOT NULL, new_row.image_url, projects.image_url),
                scraped_at = CURRENT_TIMESTAMP
        """
        cursor.execute(sql_script, (title, description, details, image_url, url))
        print(f"Inserted: {title}")


if __name__ == "__main__":
    main()
