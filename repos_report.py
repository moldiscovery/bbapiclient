# article: https://dev.to/ayushsharma/exporting-bitucket-repositories-and-pipelines-with-python-3h5o
# code from: https://github.com/ayush-sharma/infra_helpers/blob/master/bitbucket/report_repos_pipelines.py
# requires python >= 3 
# usage example: BB_ACCOUNT_ID=id BB_OAUTH_ID=key BB_OAUTH_SECRET=secret python repos_report.py


from urllib.parse import urlencode
from urllib.parse import parse_qs, urlsplit, urlunsplit
import csv
import json
import sys
from os.path import join
from os import environ 
from datetime import datetime
import click

from BBclient import AuthClient


@click.command()
@click.option("--filereport/--no-filereport", help="Report to file", default=False, required=False)
@click.option("--operation", help="Operation choose: list_repos, ", type=click.Choice(['listrepos', 'set-readonly'], case_sensitive=False))
def run(operation, filereport):
    click.echo(operation)

    ac = AuthClient()
    ac.connect()

    if operation == "listrepos":
        list_team_repos(ac, filereport)


def list_team_repos(client, filereport):

    repo_list = get_all_repos(
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


def get_all_repos(BBClient, next_page_url):

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

        data += get_all_repos(BBClient=BBClient,
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

