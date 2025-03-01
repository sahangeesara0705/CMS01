# CMS01
A Content Management System written in Python, HTML, CSS and JavaScript

## CMS API
`GET - /api/cms/welcome` get welcome message

## Page Management
### `GET - /api/cms/pages/list` list all available pages
### `GET - /api/cms/pages/get/{page_name}.html` get page content
### `POST - /api/cms/pages/create/page` creates a new page
- need to pass `page_name`
### `POST - /api/cms/pages/update/{page_name}.html` update an existing page
- need to pass `html_code`
### `DELETE - /api/cms/pages/{page_name}.html` delete a page

