# -*- coding: utf-8 -*-
"""
This is a script to determine which PRs have been merges since the last
release, or between two releases on the same branch.
"""
from __future__ import print_function
import argparse
import re
import os
import os.path

from collections import namedtuple

import requests

import yaml

PUBLIC_GITHUB_URL = 'https://github.com'
PUBLIC_GITHUB_API_URL = 'https://api.github.com'
CONFIG_FILE = r'./changelog.yml'
OUTPUT_FILE = r'./CHANGELOG.md'
GitHubConfig = namedtuple('GitHubConfig', ['base_url', 'api_url', 'headers'])

Commit = namedtuple('Commit', ['sha', 'message', 'committer'])

# Merge commits use a double linebreak between the branch name and the title
MERGE_PR_RE = re.compile(r'^Merge pull request #([0-9]+) from .*\n\n(.*)')

# Squash-and-merge commits use the PR title with the number in parentheses
SQUASH_PR_RE = re.compile(r'^(.*) \(#([0-9]+)\).*')

class GitHubError(Exception):
    pass


def get_github_config(github_base_url, github_api_url, token):
    """ Returns a GitHubConfig instance based on the given arguments """
    if token is None:
        token = os.environ.get('GITHUB_API_TOKEN')

    headers = {}
    if token is not None:
        headers['Authorization'] = 'token ' + token
    headers['Accept'] = "application/vnd.github.groot-preview+json"

    return GitHubConfig(base_url=github_base_url, api_url=github_api_url,
                        headers=headers)


def get_commit_for_tag(github_config, owner, repo, tag):
    """ Get the commit sha for a given git tag """
    tag_url = '/'.join([
        github_config.api_url,
        'repos',
        owner, repo,
        'git', 'refs', 'tags', tag
    ])
    tag_json = {}

    while 'object' not in tag_json or tag_json['object']['type'] != 'commit':
        tag_response = requests.get(tag_url, headers=github_config.headers)
        tag_json = tag_response.json()

        if tag_response.status_code != 200:
            raise GitHubError("Unable to get tag {}. {}".format(
                tag, tag_json['message']))

        # If we're given a tag object we have to look up the commit
        try:
            if tag_json['ref'].startswith('refs/tags'):
                tag_url = tag_json['object']['url']
        except:
            tag_json = tag_json[0]
            if tag_json['ref'].startswith('refs/tags'):
                tag_url = tag_json['object']['url']


    return tag_json['object']['sha']


def get_last_commit(github_config, owner, repo, branch='main'):
    """ Get the last commit sha for the given repo and branch """
    commits_url = '/'.join([
        github_config.api_url,
        'repos',
        owner, repo,
        'commits'
    ])
    commits_response = requests.get(commits_url, params={'sha': 'main'},
                                    headers=github_config.headers)
    commits_json = commits_response.json()
    if commits_response.status_code != 200:
        raise GitHubError("Unable to get commits. {}".format(
            commits_json['message']))

    return commits_json[0]['sha']


def get_last_tag(github_config, owner, repo):
    """ Get the last tag for the given repo """
    tags_url = '/'.join([github_config.api_url, 'repos', owner, repo, 'tags'])
    tags_response = requests.get(tags_url, headers=github_config.headers)
    tags_response.raise_for_status()
    tags_json = tags_response.json()
    return tags_json[0]['name']


def get_commits_between(github_config, owner, repo, first_commit, last_commit):
    """ Get a list of commits between two commits """
    commits_url = '/'.join([
        github_config.api_url,
        'repos',
        owner, repo,
        'compare',
        first_commit + '...' + last_commit
    ])
    commits_response = requests.get(commits_url, params={'sha': 'main'},
                                    headers=github_config.headers)
    commits_json = commits_response.json()
    if commits_response.status_code != 200:
        raise GitHubError("Unable to get commits between {} and {}. {}".format(
            first_commit, last_commit, commits_json['message']))

    if 'commits' not in commits_json:
        raise GitHubError("Commits not found between {} and {}.".format(
            first_commit, last_commit))

    commits = [Commit(c['sha'], c['commit']['message'], c['committer']['login'])
               for c in commits_json['commits']]
    return commits


def is_pr(message, committer):
    """ Determine whether or not a commit message is a PR merge """
    """ https://github.com/web-flow - This account is the Git committer for all web commits (merge/revert/edit/etc...) made on GitHub.com. """
    return MERGE_PR_RE.search(message) or SQUASH_PR_RE.search(message) or committer == 'web-flow'

def get_pr(github_config, owner, repo, number):
    pr_url = '/'.join([
        github_config.api_url,
        'repos',
        owner, repo,
        'pulls',
        number
    ])
    pr_response = requests.get(pr_url, params={'sha': 'main'},
                                    headers=github_config.headers)
    pr_json = pr_response.json()
    if pr_response.status_code != 200:
        raise GitHubError("Unable to get PR# {}".format(number))

    return pr_json

def get_pr_from_commit_hash(github_config, owner, repo, commithash):
    pr_url = '/'.join([
        github_config.api_url,
        'repos',
        owner, repo,
        'commits',
        commithash,
        'pulls'
    ])
    pr_response = requests.get(pr_url, params={'sha': 'main'},
                                    headers=github_config.headers)
    pr_json = pr_response.json()
    if pr_response.status_code != 200:
        raise GitHubError("Unable to get PR# of commit {}".format(commithash))

    return pr_json

def extract_pr(github_config, owner, repo, message, commithash):
    """ Given a PR merge commit message, extract the PR number and title """
    merge_match = MERGE_PR_RE.match(message)
    squash_match = SQUASH_PR_RE.match(message)

    if merge_match is not None:
        number, title = merge_match.groups()
        return get_pr(github_config, owner, repo, number)
    elif squash_match is not None:
        title, number = squash_match.groups()
        return get_pr(github_config, owner, repo, number)
    else:
        pr_from_commit = get_pr_from_commit_hash(github_config, owner, repo, commithash)
        if pr_from_commit:
            return pr_from_commit[0]

    return None
    #raise Exception("Commit isn't a PR merge, {}".format(message))


def fetch_changes(github_config, owner, repo, previous_tag=None,
                  current_tag=None, branch='main'):
    if previous_tag is None:
        previous_tag = get_last_tag(github_config, owner, repo)
    previous_commit = get_commit_for_tag(github_config, owner, repo,
                                         previous_tag)

    current_commit = None
    if current_tag is not None:
        current_commit = get_commit_for_tag(github_config, owner, repo,
                                            current_tag)
    else:
        current_commit = get_last_commit(github_config, owner, repo, branch)

    commits_between = get_commits_between(github_config, owner, repo,
                                          previous_commit, current_commit)

    # Process the commit list looking for PR merges
    prs = []
    for c in commits_between:
        if is_pr(c.message, c.committer):
            pr = extract_pr(github_config, owner, repo, c.message, c.sha)
            if pr:
                prs.append(pr)

    if len(prs) == 0 and len(commits_between) > 0:
        raise Exception("Lots of commits and no PRs on branch {}".format(
            branch))

    prs.reverse()
    return prs

def replace_token_with_match(matchobj, replacer):
    if re.search(r'\$\d+', replacer):
        i = 0
        result = matchobj.group(0)
        for g in matchobj.groups():
            i += 1
            replacement_token = r'\$'+ str(i)
            replacer = re.sub(replacement_token, g, replacer)
            result = replacer
        return result
    else:
        return replacer

def replace_content(regex, replacer, content):  
    return re.sub(regex, lambda m: replace_token_with_match(m, replacer), content)

def format_changes(github_config, owner, repo, prs, config_file):
    if os.path.isfile(config_file):
        with open(config_file, encoding="UTF-8") as file:
            config = yaml.full_load(file)
    else:
        config = None

    """ Format the list of prs in markdown """
    lines = []
    LineContent = namedtuple('LineContent', ['type', 'content'])
    for pr in prs:
        labels = [(label['name']) for label in pr['labels']]
        link = pr['url']
        number = '[{number}]({link})'.format(number=pr['number'], link=link)
        """ Adding content by categories in markdown  """
        categories = config['categories'] if config else []
        for item in categories:
            for lab in item['labels']:
                if labels.__contains__(lab) and not config['exclude-labels'].__contains__(lab):
                    lines.append(LineContent(item['title'],'- {title} {number}'.format(title=pr['title'], number=number)))
        if not categories:
            lines.append(LineContent("Changes",'- {title} {number}'.format(title=pr['title'], number=number)))
            categories.append({"title": "Changes"})
    """ Appending categories title in markdown  """
    all_lines = []
    if lines:
        i=0
        for c in categories:
            if i > 0:
                all_lines.append("")
            i=0
            for l in lines:
                if l[0] == c['title']:
                    if i == 0:
                        all_lines.append("## " + c['title'])
                        all_lines.append("")
                    all_lines.append(l[1])
                    i += 1
    md_content = ""
    """ Replacing the configuration template in markdown  """
    if all_lines:
        if config:
            template = config['template']
            md_content = template.replace("$CHANGES", '\n'.join(all_lines))
        else:
            md_content = '\n'.join(all_lines)
    
    """ Replace content by configuration replacers in markdown  """
    if config:
        for r in config['replacers']:
            md_content = replace_content(r['search'], r['replace'], md_content)

    return md_content

def generate_changelog(owner=None, repo=None, previous_tag=None, current_tag=None,
                       config_file=None, output_file=None,
                       github_base_url=None,
                       github_api_url=None, github_token=None):

    github_config = get_github_config(github_base_url, github_api_url,
                                      github_token)

    prs = fetch_changes(github_config, owner, repo, previous_tag, current_tag)
    lines = format_changes(github_config, owner, repo, prs, config_file)

    f = open(OUTPUT_FILE, "w", encoding="utf-8")
    f.write(lines)
    f.close()

    return lines

def main():
    configFileFromEnv =os.environ.get('CONFIG-FILE')
    if configFileFromEnv:
        CONFIG_FILE = configFileFromEnv
    outputFileFromEnv =os.environ.get('OUTPUT-FILE')
    if outputFileFromEnv:
        OUTPUT_FILE = outputFileFromEnv
    print("repo: "+ os.environ.get('GITHUB_REPOSITORY'))
    print("owner: "+ os.environ.get('GITHUB_REPOSITORY_OWNER'))
    # repoFromEnv = os.environ.get('GITHUB_REPOSITORY')
    # if repoFromEnv:
    #     reporepoFromEnv = repoFromEnv.split('/')


    parser = argparse.ArgumentParser(
        description="Generate a CHANGELOG between two git tags based on GitHub"
                    "Pull Request merge commit messages")
    parser.add_argument('--owner', default=os.environ.get('OWNER'),
                        help='owner of the repo on GitHub')
    parser.add_argument('--repo', default=os.environ.get('REPO'),
                        help='name of the repo on GitHub')
    parser.add_argument('previous_tag', metavar='PREVIOUS', nargs='?',
                        help='previous release tag (defaults to last tag)')
    parser.add_argument('current_tag', metavar='CURRENT', nargs='?',
                        help='current release tag (defaults to HEAD)')
    parser.add_argument('--config-file', type=str, action='store',
                        default=CONFIG_FILE, help='Config file name '
                        r'defaults to ./changelog.yml')
    parser.add_argument('--output-file', type=str, action='store',
                        default=OUTPUT_FILE, help='Output file name '
                        r'defaults to ./CHANGELOG.md')
    parser.add_argument('--github-base-url', type=str, action='store',
                        default=PUBLIC_GITHUB_URL, help='Override if you '
                        'are using GitHub Enterprise. e.g. https://github.'
                        'my-company.com')
    parser.add_argument('--github-api-url', type=str, action='store',
                        default=PUBLIC_GITHUB_API_URL, help='Override if you '
                        'are using GitHub Enterprise. e.g. https://github.'
                        'my-company.com/api/v3')
    parser.add_argument('--github-token', type=str, action='store',
                        default=os.environ.get('GITHUB-TOKEN'), help='GitHub oauth token to auth '
                        'your Github requests with')

    args = parser.parse_args()
    changelog = generate_changelog(**vars(args))
    print(changelog)

if __name__ == '__main__':
    main()
