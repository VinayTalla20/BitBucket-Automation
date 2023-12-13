import requests
import json
import os
from datetime import datetime, timezone, timedelta
import base64
# from dotenv import load_dotenv


# load_dotenv()

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



def create_repo_tags(repository_slug, full_commit_id, tag_name):
    print("Creating Repo Tags")
    
    base_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{repository_slug}/refs/tags"

    body = {
        "name": tag_name,
        "target": {
            "hash": full_commit_id
        },
        "message": f"Tagged for the Release on {present_data_time} with version {tag_name}"
    }
    # To created tags by pasing body to request
    tags_response = requests.request("POST", base_url, headers=headers, json=body)
    
    if tags_response.status_code == 201:
        print("Successfully Created Tag", tag_name, "for the Repository ", repository_slug, "for the commit id",
          full_commit_id)
    else:
        print("Could not able to create Tag ", tag_name, " for the Repository ", repository_slug, " Error ",tags_response.json() )

def get_full_commitId(commit_id, repository_slug):
    print("Getting Full Commit ID")
    base_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{repository_slug}/commit/{commit_id}"


    get_commit_id = requests.request(url=base_url, method="GET", headers=headers)

    commit_response = get_commit_id.json()

    full_commit_id_for_repo = commit_response["hash"]

    print("The full commit id is ", full_commit_id_for_repo, "date of creation", commit_response["date"])

    if len(hot_fix_branchname.strip()) == 0:
        # execute below code for No Hotfix
        if get_tags(rep_tag_name=tag_name, tag_repo_name=repository_slug) and validate_repo_tags_for_commit_id(commit_id=full_commit_id_for_repo, repository_slug=repository_slug):
            create_repo_tags(repository_slug=repository_slug, full_commit_id=full_commit_id_for_repo, tag_name=tag_name)

    else:
        # below code create Tags for Hotfix
        create_repo_tags(repository_slug=repository_slug, full_commit_id=full_commit_id_for_repo, tag_name=tag_name)


# merged PRs
def get_merged_pr(repositories_slug_name):
    # convert timestamp format to Year-Month-Day format and go back to 3 days
    # modified_pr_date = datetime.strptime(present_data_time, '%Y-%m-%d') - timedelta(days=3)
    # # splitting output date  variable at space
    # modified_pr_date = str(modified_pr_date).split(" ")[0]
    # print("Getting Merged PR's for ", repositories_slug_name)

    # To check whether HotFix varible is empty or not
    if len(hot_fix_branchname.strip()) == 0:
        # To get PRs from the date of creation through passing variable modified_pr_date
        base_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{repositories_slug_name}/pullrequests/?q=state=\"MERGED\" AND destination.branch.name=\"master\" AND source.branch.name=\"stage\""

        print("Hot Fix Branch is Empty so Tagging without Hotfix")
        response = requests.request("GET", base_url, headers=headers)
        values = response.json()

        # To check size of response is not equal to zero, so that PRs exists for the Repo
        if values["size"] != 0:


            merge_commit = values["values"][0]["merge_commit"]["hash"]
            destination_branch = values["values"][0]["destination"]["branch"]["name"]
            source_branch = values["values"][0]["source"]["branch"]["name"]

            if destination_branch == "master" and source_branch == "stage" and len(hot_fix_branchname.strip()) == 0:

                # the merge_commit is just small hash value, to get full commit hash value use below
                get_full_commitId(commit_id=merge_commit, repository_slug=repositories_slug_name)

            else:
                print("The Repository ", repositories_slug_name,
                          " does not have Merged PR for Destination branch ",destination_branch, " from source branch ", source_branch)

        # size of response is equal to zero
        else:
            print("NO Merged PR's for the Repository ", repositories_names)

    # HotFix Branch is not Empty
    else:
        print("Hot Fix branch is present")
        base_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{repositories_slug_name}/pullrequests/?q=state=\"MERGED\" AND destination.branch.name=\"master\" AND source.branch.name=\"{hot_fix_branchname}\""
        response = requests.request("GET", base_url, headers=headers)
        values = response.json()
        print(values)

        if values["size"] != 0:
            merge_commit = values["values"][0]["merge_commit"]["hash"]
            get_full_commitId(commit_id=merge_commit, repository_slug=repositories_slug_name)

        else:
            print("The Repository ", repositories_slug_name, " does not have Merged PR for Destination branch master from source branch", hot_fix_branchname)


def get_repository_names(modified_date):

    print("Getting RepoNames for project XCOP")

    i = 1
    # for first page results
    first_page = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/?q=updated_on>={modified_date} AND project.key=\"XCOP\"&page=1"
    first_page = requests.request("GET", first_page, headers=headers)

    for first_page_repositories in first_page.json()["values"]:
        first_page_repos_slugs = first_page_repositories["slug"]
        get_merged_pr(first_page_repos_slugs)
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

                repositories_names.append(repositories_slug_name)
                
                # passing each repo to get merged PR
                get_merged_pr(repositories_slug_name)
            i += 1
        else:
            print("No pages left")
            print("Total Repos found", repositories_names, " total count ", len(repositories_names))
            # No pages left exit out of While Loop
            break


def get_tags(tag_repo_name, rep_tag_name):
    print("Getting tags for Repository", tag_repo_name, "with Tag", rep_tag_name)
    
    base_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{tag_repo_name}/refs/tags/{rep_tag_name}"

    get_tags_response = requests.request("GET", headers=headers, url=base_url)

    if get_tags_response.status_code != 200:
        print("The Repository ", tag_repo_name, " does not has Tag ", rep_tag_name)
        return True
    else:
        print("The Repository ", tag_repo_name, " has Tag ", rep_tag_name)
        return False


def validate_repo_tags_for_commit_id(commit_id, repository_slug):
    print("Validating Repo Tags")
    
    base_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{repository_slug}/refs/tags"

    values = requests.request("GET", base_url, headers=headers)
    tags_response = values.json()
    
    # To check whether the commit ID has tag before
    print("Length of Tags in the Repository")
    if len(tags_response["values"]) != 0:
        for required_tags in tags_response["values"]:
            if required_tags["target"]["hash"] == commit_id and required_tags["name"] == tag_name:
                print("The Commit ID ", commit_id, " for the repo ", repository_slug, " already has Tag ", tag_name)
                return False
            else:
                print("The commit ID ", commit_id," for the repo ", repository_slug, " doest not has Tag ",tag_name)
                return True
    return True



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
    # print("Successfully deleted tag", tag_name)


# calling First Method

if __name__ == "__main__":
    present_data_time = datetime.now()
    present_data_time = present_data_time.strftime("%Y-%m-%d")
    print("Present Time", present_data_time)

    modified_date = datetime.strptime(present_data_time, '%Y-%m-%d') - timedelta(days=30)
    modified_date = str(modified_date).split(" ")[0]
    print(" Modified Date", modified_date)

    get_repository_names(modified_date)