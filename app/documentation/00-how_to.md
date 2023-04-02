# How to

<a hx-get="/documentation/index.md"> <img height="20" src="/assets/chevron-left-duo.svg" width="20"/> Back </a> | <a 
hx-get="/documentation/index.md"> Index </a> 

[TOC]

## Create a new project

Currently only via the API with admin rights.

```commandline
curl -X 'POST' \
  '<your_url>/api/v1/settings/projects' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your token here>' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "<the project name>"
}'
```

You can access the API swagger for a graphical interface.

## Create a new project's version

On the GUI, you need to be connected with admin rights.

Select the project.

Then create a new version. The **version** is plain text so that you could enter the version number whatever the 
application versioning system is. 

![](/assets/howto/create_version_HT.png)

![](/assets/howto/create_version_fill_version_HT.png)