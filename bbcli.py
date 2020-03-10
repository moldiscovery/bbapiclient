# Inspired by:
# article: https://dev.to/ayushsharma/exporting-bitucket-repositories-and-pipelines-with-python-3h5o
# code from: https://github.com/ayush-sharma/infra_helpers/blob/master/bitbucket/report_repos_pipelines.py
# BB API 1.0 reference: https://confluence.atlassian.com/bitbucket/version-1-423626337.html
#
# list repos example: BB_ACCOUNT_ID=id BB_OAUTH_ID=key BB_OAUTH_SECRET=secret python bbcli.py --operation listrepos --filereport 
#
# set repo permission example: 
# BB_ACCOUNT_ID=id BB_OAUTH_ID=key BB_OAUTH_SECRET=secret python bbcli.py  --operation permissions --group foo --grant read
#
# set repos permission example: 
# BB_ACCOUNT_ID=id BB_OAUTH_ID=key BB_OAUTH_SECRET=secret python bbcli.py  --operation permissions --group foo --repo bar --grant read

# SOME QUERIES 
# list users of a group: https://bitbucket.org/api/2.0/groups/{teamname}
# repos info for a group : https://bitbucket.org/api/1.0/group-privileges/{teamname}/{groupowner}/{groupnameslug}
#response = client.BBClient.get("https://bitbucket.org/api/1.0/group-privileges/moldiscovery/moldiscovery/test")

# get repo https://bitbucket.org/api/1.0/group-privileges/{teamname}/{reposlug}/{groupowner}/{groupnameslug}
#response = client.BBClient.get("https://bitbucket.org/api/1.0/group-privileges/moldiscovery/testrepo/moldiscovery/test")


from urllib.parse import urlencode
from urllib.parse import parse_qs, urlsplit, urlunsplit
from requests.exceptions import HTTPError
import csv
import json
import sys
from os.path import join, exists
from os import environ 
from datetime import datetime
import click

from BBclient import AuthClient

# TODO user click groups to configure subcommands menu
@click.command()
@click.option("--filereport/--no-filereport", help="Report to file", default=False, required=False)
@click.option("--operation", help="Operation choose: list_repos, ", type=click.Choice(['listrepos', 'permissions', 'groupinfo', 'userinfo', 'restoregroupsgrant'], case_sensitive=False))
@click.option("--repo", help="apply to a single repo", type=str, required=False)
@click.option("--group", help="grant permissions for this group", type=str, required=False)
@click.option("--user", help="user id", type=str, required=False)
@click.option("--grant", help="type of permission to grant", default='read', type=click.Choice(['read', 'write'], case_sensitive=False))
@click.option("--backupfilepath", help="file containing the backed up user permission", type=str, required=False)
def run(operation, filereport, repo, user, group, grant, backupfilepath):
    click.echo(operation)

    ac = AuthClient()
    #ac.connect()

    if operation == "listrepos":
        print("Options: group, grant, repo skipped")
        ac.connect()
        list_team_repos(ac, filereport)
    if operation == "permissions":
        if group:
            
            if repo:
                ac.connect()
                answer = input("This command will change/create the group '{}' with permission '{}' for repo '{}', are you sure? yes/no    ".format(group, grant,repo))
                if 'yes' in answer: 
                    print("run on repo {}".format(repo))
                    setRepoGroupPermissions(ac, group.lower(), repo, grant)
            else:
                # Single request doesn't not work as expected so I need to iterate over the group repos
                ac.connect()
                answer = input("This command will change/create the group '{}' with permission '{}', are you sure? yes/no    ".format(group, grant))
                if 'yes' in answer: 
                    repos = listgroup_repos(ac, group.lower())
                    for repo in repos: 
                        print("run on repo {}".format(repo))
                        setRepoGroupPermissions(ac, group.lower(), repo, grant)
    if operation == 'groupinfo':
        ac.connect()
        group_info(ac, group.lower(), filereport)
    if user and operation == 'userinfo':
        ac.connect()
        user_info(ac, user, filereport)
    if operation == 'restoregroupsgrant':
        if not group:
            error("missing group name")
        if backupfilepath and exists(backupfilepath):
            ac.connect()
            with open(backupfilepath, 'r') as backup:
                reader = csv.DictReader(backup)
                for item in reader:
                    s_repo = item['repo'].strip()
                    s_grant = item['permission'].strip()
                    print("set {1} on repo {0}".format(s_repo, s_grant))
                    setRepoGroupPermissions(ac, group.lower(), s_repo, s_grant)
        else:
            error("wrong backup file")



def error(msg):
    click.ClickException(msg).show()
    sys.exit(1)


def list_team_repos(client, filereport):

    repo_list = get_repo_page(
        client.BBClient, next_page_url=client.server_base_uri + '2.0/repositories/' + client.account_id)

    repo_data_map = {}

    for repo in repo_list:
        # I only consider a shortdate for 'updated_on' of format YYYY-MM-dd  
        repo_data_map[repo['name']] = repo['updated_on'][:10]

    # sort by date
    ordered_repos = sorted(repo_data_map.items(), key = lambda item:datetime.strptime(item[1], '%Y-%m-%d'), reverse=True)

    if filereport:
        with open('repos.csv', 'w') as csv_file:

            print('> Saving repos report to file...')

            csv_file.write('git_remote , updated_on\n')
            for rname,rtime in ordered_repos:
                csv_file.write(join("git@bitbucket.org:"+client.account_id,rname) + " , " + rtime + '\n')

        print('> Repo report saved. (repos.csv)')
    else:
        print(ordered_repos)

# only works for the caller user id
def user_info(client, user, filereport):
        out = []
        response = client.BBClient.get("https://api.bitbucket.org/2.0/users/{0}/repositories".format(user))
        
        if response.status_code != 200:
            error("API Request error, code {}".format(response.status_code))
            
        body = json.loads(response.content)

        if filereport:
            targetfile = "group_{0}_info.csv".format(group) 
            with open(targetfile, 'w') as csv_file:

                print('> Saving groupinfo report to file...')

                csv_file.write('group , permission\n')
                for item in body:
                    csv_file.write(item['repo'].split('/')[-1] + ", " + item['privilege'] + '\n')

                print("> Repo report saved. (%s)" % targetfile)
        else:
            print(body)
            

        return out



def group_info(client, group, filereport):

    try:
        out = []
        response = client.BBClient.get(join("https://bitbucket.org/api/1.0/group-privileges",client.account_id,client.account_id,group))
        
        if response.status_code != 200:
            error("API Request error, code {}".format(response.status_code))
            
        body = json.loads(response.content)

        if filereport:
            targetfile = "group_{0}_info.csv".format(group) 
            with open(targetfile, 'w') as csv_file:

                print('> Saving groupinfo report to file...')

                csv_file.write('repo,permission\n')
                for item in body:
                    csv_file.write(item['repo'].split('/')[-1] + "," + item['privilege'] + '\n')

                print("> Repo report saved. (%s)" % targetfile)
        else:
            for item in body:
                out.append(item['repo'].split('/')[-1] + ", " + item['privilege'])

            print(out)
            

        return out

    except HTTPError:
        error("BB Endpoint request error")


def listgroup_repos(client, group):

    try:
        out = []
        response = client.BBClient.get(join("https://bitbucket.org/api/1.0/group-privileges",client.account_id,client.account_id,group))
        
        if response.status_code != 200:
            error("API Request error, code {}".format(response.status_code))
            
        body = json.loads(response.content)

        for item in body:
            out.append(item['repo'].split('/')[-1])

        return out

    except HTTPError:
        error("BB Endpoint request error")


# use API v1.0 cause this feature is deprecated on 2.0 
# https://developer.atlassian.com/cloud/bitbucket/deprecation-notice-v1-apis/?_ga=2.232592733.337263193.1581505695-823020582.1566895316
# I'm starting from this page: https://confluence.atlassian.com/bitbucket/group-privileges-endpoint-296093137.html
def setRepoGroupPermissions(client, group, repo, grant):

    try: 
        # change repo perm: PUT https://api.bitbucket.org/1.0/group-privileges/{workspace_id}/{repo_slug}/{group_owner}/{group_slug} data=['read'|'write'|admin']
        response = client.BBClient.put(join("https://bitbucket.org/api/1.0/group-privileges/",client.account_id,repo,client.account_id,group), data=grant)

        if response.status_code != 200:
            error("API Request error, code {}".format(response.status_code))
        
        print("Completed")

    except HTTPError:
        error("BB Endpoint request error")

# TODO FIX , this set permissions on all repos, expected behaviour is to apply to the group repos  
# def setGroupPermissions(client, group, grant):

#     try: 
#         # change repo perm: PUT https://api.bitbucket.org/1.0/group-privileges/{workspace_id}/{repo_slug}/{group_owner}/{group_slug} data=['read'|'write'|admin']
#         response = client.BBClient.put(join("https://api.bitbucket.org/1.0/group-privileges",TEAM,TEAM,group), data=grant)

#         if response.status_code != 200:
#             error("API Request error, code {}".format(response.status_code))
        
#         print(response.content)
#         print("Completed")

#     except HTTPError:
#        error("BB Endpoint request error")


def get_repo_page(BBClient, next_page_url):

    data = []

    response = BBClient.get(next_page_url)

    try:

        response_dict = json.loads(response.content)

    except Exception as e:
        print(str(e))

    if 'values' in response_dict:

        for repo in response_dict['values']:

            data.append({

                'uuid': repo['uuid'],
                'name': repo['name'],
                'pr_url': repo['links']['pullrequests']['href'],
                'lang': repo['language'],
                'updated_on': repo['updated_on'],
                'size': repo['size'],
                'slug': repo['slug']
            })

    if 'next' in response_dict:

        data += get_repo_page(BBClient=BBClient,
                              next_page_url=response_dict['next'])

    return data


def get_all_pipelines(BBClient, next_page_url):

    data = []

    response = BBClient.get(next_page_url)

    try:

        response_dict = json.loads(response.content)

    except Exception as e:

        print(str(e))

    if 'values' in response_dict:

        for repo in response_dict['values']:

            data.append({

                'uuid': repo['uuid'],
                'repo': repo['repository']['name'],
                'state': repo['state']['result']['name'],
                'build_number': repo['build_number'],
                'creator': repo['creator']['display_name'] + '/' + repo['creator']['username'],
                'target_type': repo['target']['ref_type'] if 'ref_type' in repo['target'] else '',
                'target_name': repo['target']['ref_name'] if 'ref_name' in repo['target'] else '',
                'trigger': str(repo['trigger']['name']),
                'duration': repo['duration_in_seconds'],
                'created_on': repo['created_on'],
                'completed_on': repo['completed_on']
            })

    if 'next' in response_dict:

        data += get_all_pipelines(BBClient=BBClient,
                                  next_page_url=response_dict['next'])

    elif 'page' in response_dict and 'pagelen' in response_dict and response_dict['page'] < response_dict['pagelen']:

        """ If next page URL does not exist, assemble next page URL manually.
        """
        scheme, netloc, path, query_string, fragment = urlsplit(next_page_url)
        query_params = parse_qs(query_string)

        query_params['page'] = [response_dict['page'] + 1]
        new_query_string = urlencode(query_params, doseq=True)

        next_page_url = urlunsplit(
            (scheme, netloc, path, new_query_string, fragment))

        data += get_all_pipelines(BBClient=BBClient,
                                  next_page_url=next_page_url)

    return data


if __name__ == '__main__':

    run()

