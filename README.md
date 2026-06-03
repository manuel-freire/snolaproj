# snolaproj

Generates a filterable webpage listing projects based on an input html with one 2-column table per project

## Goals

Research networks sometimes need to showcase their member's network-related projects. A simple way to pool projects together is to open a shared Google Doc, and agree on a simple format:

| project-acronym                              | title    |
|----------------------------------------------|----------|
| project-url  (may include several)           | url      |
| project-name  (may prefix with ES: and EN: ) | name     |
| project-code                                 | code     |
| funding-entity                               | funder   |
| funding-amount                               | amount   |
| dd/mm/yyyy - dd/mm/yyyy                      | period   |
| any comments                                 | comments |

Each project is expected to be **1 table** in the document, grouped by institution under **h2** headers that follow a format similar to *RESEARCH_GROUP_NAME - INSTITUTION_NAME*. 

This can be manually converted into a web-page, but the process is error-prone and labour-intensive. A better option is to automate: enter **snolaproj**.

## How to use

1. Ensure that participants fill in their project information.
2. Use save-as -> zipped html, uncompress to wherever you have placed this python program
3. Run `process.py --html_file INPUT_FILE`. The output will be a webpage with all projects nicely formatted, sorted by name, and searchable by institution and date.
4. Go back to 1. unless you are happy with the result

## How it works

BeatifulSoup4 is a python library for handling html documents. The first step is for `process.py` to rewrite each project-table into a nice `div` with working URLs, classes for each field, and JS-friendly data-attributes. This is then output into an html template, which is in charge of presentation & interactivity.

The html template (`template.html`) includes JS to provide search, filtering, and language-switching (see those ES: EN: optional markers?). It also contains a baked-in CSS.

## Future work

* Additional sorting & filtering options could be made available. Currently, only sort-by-acronym is supported; this could also be used in filters (by substring); additional filters/sorting could be by-start, by-end, by-funding, or by-funder all make sense.
* It is possible to associate images to cells (funding agency, group logo, project logo...). This is currently ignored, but could be displayed.
* Some projects are collaborations; this can be automatically identified by looking at the funding code (they tend to share a long prefix). It may make sense to include such projects only once, with added per-participant information.
