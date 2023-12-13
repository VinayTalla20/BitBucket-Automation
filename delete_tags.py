import requests
import json
import os
from datetime import datetime, timezone, timedelta
import base64


repositories_names = []

USER_NAME = os.getenv("USER_NAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")
BASIC_AUTH = USER_NAME + ":" + APP_PASSWORD
WORKSPACE = os.getenv("WORKSPACE")
tag_name = os.getenv("TAG_NAME")
hot_fix_branchname = os.getenv("HOTFIX_BRANCH", "")

# convert to base64 encoded Auth
BASIC_AUTH_BYTES = BASIC_AUTH.encode("ascii")
BASIC_AUTH_BASE64 = base64.b64encode(BASIC_AUTH_BYTES)
BASIC_AUTH = BASIC_AUTH_BASE64.decode("ascii")

headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {BASIC_AUTH}"
    }



def get_repository_names(modified_date):

    print("Getting RepoNames for project XCOP")

    i = 1
    # for first page results
    first_page = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/?q=updated_on>={modified_date} AND project.key=\"XCOP\"&page=1"
    first_page = requests.request("GET", first_page, headers=headers)

    for first_page_repositories in first_page.json()["values"]:
        first_page_repos_slugs = first_page_repositories["slug"]
        delete_tags(tag_name=tag_name, repo_name=first_page_repos_slugs)
        repositories_names.append(first_page_repos_slugs)
    
    # for other Pages
    while True:

        base_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/?q=updated_on>={modified_date} AND project.key=\"XCOP\"&page={i}"
        response = requests.request("GET", base_url, headers=headers)
        repositories_response = response.json()

        next_page = repositories_response.get("next")

        if next_page is not None:
            next_page_response = requests.request("GET", next_page, headers=headers)

            for repositories_slugs in next_page_response.json()["values"]:
                repositories_slug_name = repositories_slugs["slug"]
                delete_tags(tag_name=tag_name, repo_name=repositories_slug_name)
                repositories_names.append(repositories_slug_name)
                
                # passing each repo to get merged PR
            i += 1
        else:
            print("No pages left")
            print("Total Repos found", repositories_names, " total count ", len(repositories_names))
            # No pages left exit out of While Loop
            break

def delete_tags(tag_name, repo_name):
    print("Deleting Tag ", tag_name, " for a Repository ", repo_name)
    delete_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{repo_name}/refs/tags/{tag_name}"

    # to delete tags un comment below code

    deleted_tag_response = requests.request("DELETE", headers=headers, url=delete_url)

    if deleted_tag_response.status_code == 204:
        print("Deleted Tag ", tag_name, " for a Repository ", repo_name)
    else:
        print("Could not able to Delete Tag", tag_name," or the Tag Does not Exists in Repo ", repo_name)
        print(deleted_tag_response)




if __name__ == "__main__":
    present_data_time = datetime.now()
    present_data_time = present_data_time.strftime("%Y-%m-%d")
    print("Present Time", present_data_time)

    modified_date = datetime.strptime(present_data_time, '%Y-%m-%d') - timedelta(days=30)
    print("Modified Date contains Space", modified_date)
    modified_date = str(modified_date).split(" ")[0]
    print(" Modified Date", modified_date)

    get_repository_names(modified_date)