# Generate changelog from tags GitHub Action

## Available inputs

```yaml
owner:
  description: 'Username of the owner of target GitHub repo (default: extracted from $GITHUB_REPOSITORY)'
  required: true
repo:
  description: 'Name of project on GitHub (default: extracted from $GITHUB_REPOSITORY)'
  required: true
output-file:
  description: 'Output file path. (default: CHANGELOG.md)'
  required: false
  default: 'CHANGELOG.md'
config-file:
  description: 'Configuration file path (default: changelog.yml)'
  required: false
  default: changelog.yml
github-token:
  description: 'To make more than 50 requests per hour your GitHub token is required. You can generate it at: https://github.com/settings/tokens/new<Paste>'
  required: false
previous-tag:
  description: 'Changelog will start after specified tag.'
  required: false
current-tag:
  description: 'Changelog will end before specified tag.'
  required: false
github-site:
  description: 'The Enterprise GitHub site where your project is hosted if using GitHub Enterprise.'
  required: false
github-api:
  description: 'The enterprise endpoint to use for your GitHub API if using GitHub Enterprise.'
  required: false
```
## Configuration file

```yaml
categories:
  - title: '🚀 Features'
    labels:
      - 'feature'
  - title: '🐛 Bug Fixes'
    labels:
      - 'bugfix'
  - title: '🧰 Maintenance'
    labels: 
      - 'chore'
  - title: '🔝 Dependencies'
    labels: 
      - 'dependencies'
      - 'dependency'
replacers:
  - search: '([A-Z]+-\d+)'
    replace: '[$1](https://company.atlassian.net/browse/$1)'
exclude-labels:
  - 'skip-changelog'
template: |
  ## Changes

  $CHANGES
```

## Configuration Options

You can configure changelog using the following key in your `.changelog.yml` file:

| Key                    | Required | Description                                                                                                                                                                |
| ---------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `template`             | Required | The template for the body of the draft release. Use [template variables](#template-variables) to insert values.                                                            |
| `categories`           | Optional | Categorize pull requests using labels. Refer to [Categorize Pull Requests](#categorize-pull-requests) to learn more about this option.                                     |
| `exclude-labels`       | Optional | Exclude pull requests using labels. Refer to [Exclude Pull Requests](#exclude-pull-requests) to learn more about this option.                                              |
| `include-labels`       | Optional | Include only the specified pull requests using labels. Refer to [Include Pull Requests](#include-pull-requests) to learn more about this option.                           |
| `replacers`            | Optional | Search and replace content in the generated changelog body. Refer to [Replacers](#replacers) to learn more about this option.                                              |
|


## Template Variables

You must use the following variable in your `template`:

| Variable        | Description                                                                                                           |
| --------------- | --------------------------------------------------------------------------------------------------------------------- |
| `$CHANGES`      | The markdown list of pull requests that have been merged.                                                             |


## Categorize Pull Requests

With the `categories` option you can categorize pull requests in release notes using labels. For example, append the following to your `.changelog.yml` file:

```yml
categories:
  - title: '🚀 Features'
    label: 'feature'
  - title: '🐛 Bug Fixes'
    labels:
      - 'fix'
      - 'bugfix'
      - 'bug'
```

Pull requests with the label "feature" or "fix" will now be grouped together:
```md
## Changes

## 🚀 Features

- Bugfix/testing [7](https://api.github.com/repos/owner/repo/pulls/7)
- configuring the actions [2](https://api.github.com/repos/owner/repo/pulls/2)

## 🐛 Bug Fixes

- fixing changelog config [8](https://api.github.com/repos/owner/repo/pulls/8)
- Adding another line [6](https://api.github.com/repos/owner/repo/pulls/6)
- fixing the configurations [5](https://api.github.com/repos/owner/repo/pulls/5)
- configuring the actions [4](https://api.github.com/repos/owner/repo/pulls/4)
- Adding line [1](https://api.github.com/repos/owner/repo/pulls/1)
```

## Exclude Pull Requests

With the `exclude-labels` option you can exclude pull requests from the release notes using labels. For example, append the following to your `.changelog.yml` file:

```yml
exclude-labels:
  - 'skip-changelog'
```

Pull requests with the label "skip-changelog" will now be excluded from the release draft.

## Replacers

You can search and replace content in the generated changelog body, using regular expressions, with the `replacers` option. Each replacer is applied in order.
You can use the `$1`, `$2`...`$N` to replace the content with the regex group. 

```yml
replacers:
  - search: '([A-Z]+-\d+)'
    replace: '[$1](https://company.atlassian.net/browse/$1)'
  - search: 'myname'
    replace: 'My Name'
```


# Example

```yaml
name: Changelog from tags

on:
  workflow_dispatch:
    inputs:
      last:
        description: 'Since Tag'
        required: true
      current:
        description: 'Current Tag'
        required: false

jobs:
  generate_changelog:
    runs-on: ubuntu-latest
    name: Generate changelog
    steps:
      - name: Create Changelog
        id: generate-changelog
        uses: mzalves/changelog-from-tags-action@v1.0.0
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          previous-tag: ${{github.event.inputs.last}}
          current-tag: ${{github.event.inputs.current}}
      - name: View Changelog
        run: cat CHANGELOG.md

```
