# ensure python is install in the PATH environmen variable
# pip install requests
import requests
# pip install beautifulsoup4
from bs4 import BeautifulSoup
import time

# ------------------------------ Obtaining Project URLs ------------------------------ #
# base URL for concantenation purposes
base_url = "https://eecs.engineering.oregonstate.edu/capstone/submission/"
# contains ALL projects (including ones not in just CS 467)
browse_projects_url = base_url + "pages/browseProjects.php"

# HTTP GET request
response = requests.get(browse_projects_url)
# converts response from bitstream into a readable text
html_string = response.text

# parses the response text?
soup = BeautifulSoup(html_string, "html.parser")

""" No filtering for CS 467"""
"""
project_links = []
project_links.clear()
# finds the div class "masonry-brick"/"masontry-brick reqNDA"
for project in soup.select(".masonry-brick"):
    # finds the "a href="
    a_tag = project.select_one("a")

    # if href exists and can be retrieved, append in the project list
    if a_tag and a_tag.get("href"):
        project_links.append(base_url + a_tag.get("href"))

print(*project_links, sep='\n')
print(len(project_links))
"""

""" Filtering for CS 467 Projects Only"""

project_links = []
project_links.clear()

# finds the div class "masonry-brick"/"masontry-brick reqNDA"
for project in soup.select(".masonry-brick"):
    filter = project.select_one(".card-body .text-muted")

    if filter:
        # strip=True removes all excess whitespace (including tab and newlines)
        text = filter.get_text(strip=True)

        if "Courses: CS467" in text:
            a_tag = project.select_one("a")

            if a_tag:
                project_links.append(base_url + a_tag.get("href"))

print(*project_links, sep="\n")
print(len(project_links))
time.sleep(5)

# ------------------------------ Obtaining Individual Project Details ------------------------------ #
# Loop through each project link
for project_link in project_links:
    response = requests.get(project_link)
    html_string = response.text
    soup = BeautifulSoup(html_string, "html.parser")

    filter = soup.select_one(".viewSingleProject")
    if filter:
        text = filter.select_one("h1")
        title = text.get_text(strip=True)

    print(title)
    
