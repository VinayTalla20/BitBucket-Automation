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
hot_fix_branchname= os.getenv("HOTFIX_BRANCH")
HOTFIX_BRANCH_PIPELINE_VALIDATE = os.getenv("HOTFIX_BRANCH_PIPELINE")

# convert to base64 encoded Auth
BASIC_AUTH_BYTES = BASIC_AUTH.encode("ascii")
BASIC_AUTH_BASE64 = base64.b64encode(BASIC_AUTH_BYTES)
BASIC_AUTH = BASIC_AUTH_BASE64.decode("ascii")

headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {BASIC_AUTH}"
    }




def get_merged_pr(repositories_slug_name):

    
    base_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{repositories_slug_name}/pullrequests/?q=state=\"MERGED\" AND destination.branch.name=\"master\" AND source.branch.name=\"{hot_fix_branchname}\""
    response = requests.request("GET", base_url, headers=headers)
    values = response.json()

    if values["size"] != 0:
        get_tags(tag_repo_name=repositories_slug_name, rep_tag_name=tag_name)


def get_tags(tag_repo_name, rep_tag_name):
    
    base_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{tag_repo_name}/refs/tags/{rep_tag_name}"

    get_tags_response = requests.request("GET", headers=headers, url=base_url)

    if get_tags_response.status_code == 200:
        print("The Repository ", tag_repo_name, " has Tag ", rep_tag_name)
        raise Exception("The Tag",tag_name,"is previous Tag"," makes sure provide new Tag")
        
        


def get_repository_names(modified_date):

    i = 1
    # for first page results
    first_page = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/?q=updated_on>={modified_date} AND project.key=\"XCOP\"&page=1"
    first_page = requests.request("GET", first_page, headers=headers)

    for first_page_repositories in first_page.json()["values"]:
        first_page_repos_slugs = first_page_repositories["slug"]
        if HOTFIX_BRANCH_PIPELINE_VALIDATE == "True":
            get_merged_pr(repositories_slug_name=first_page_repos_slugs)
        else:
            get_tags(tag_repo_name=first_page_repos_slugs,rep_tag_name=tag_name)
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
                
                if HOTFIX_BRANCH_PIPELINE_VALIDATE == "True":
                    get_merged_pr(repositories_slug_name=repositories_slug_name)
                else:
                    get_tags(tag_repo_name=repositories_slug_name,rep_tag_name=tag_name)
                repositories_names.append(repositories_slug_name)
                
                # passing each repo to get merged PR
            i += 1
        else:
            print("No pages left")
            print("Total Repos found", repositories_names, " total count ", len(repositories_names))
            # No pages left exit out of While Loop
            break


if __name__ == "__main__":
    present_data_time = datetime.now()
    present_data_time = present_data_time.strftime("%Y-%m-%d")

    modified_date = datetime.strptime(present_data_time, '%Y-%m-%d') - timedelta(days=30)
    
    modified_date = str(modified_date).split(" ")[0]
    get_repository_names(modified_date)