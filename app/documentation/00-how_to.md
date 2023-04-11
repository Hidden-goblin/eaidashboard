# How to

<a hx-get="/documentation/index.md"> <img height="20" src="/assets/chevron-left-duo.svg" width="20"/> Back </a> | <a 
hx-get="/documentation/index.md"> Index </a> 

[TOC]

## Create a new project

Via the API with admin rights.

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

Via the GUI once logged in as administrator, select the `New project` entry in the `Projects` menu and then submit 
the form.

<img alt="Location of the new project button" src="/assets/howto/create_project_button_HT.png" title="Create project" width="800"/>

<img alt="The create project form" src="/assets/howto/create_project_form_HT.png" title="Create project 
form" width="400"/>

## Create a new project's version

On the GUI, you need to be connected with admin rights.

Select the project.

Then create a new version. The **version** is plain text so that you could enter the version number whatever the 
application versioning system is.

<img src="/assets/howto/create_version_HT.png" title="Create a version UI" width="800"/>

<img alt="Form to fill a version" src="/assets/howto/create_version_fill_version_HT.png" title="Fill version UI" width="800"/>