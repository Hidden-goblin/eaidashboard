# Roles and permissions

<a hx-get="/documentation/index.md"> <img height="20" src="/assets/chevron-left-duo.svg" width="20"/> Back </a> | <a 
hx-get="/documentation/index.md"> Index </a> 

[TOC]

## Roles

The dashboard accepts only four roles:

* Application administrator
* Project administrator
* User
* Anonymous

The application administrator has the `admin` role for `*` special project.

The project administrator has the `admin` role for a specific project and the `user` role for the `*` special project.

Users have the `user` role for the `*` special project and may have the same role for a specific project.

`Anonymous` role is for end-user who is not logged into the application.

## Permissions

Beware! Action result may differ according to role.

| Action                                           | Application administrator | Project administrator | User | Anonymous |
|--------------------------------------------------|:-------------------------:|:---------------------:|:----:|:---------:|
| Documentation                                    |             X             |           X           |  X   |     X     |
|                                                  |                           |                       |      |           |
| Register project                                 |             X             |           -           |  -   |     -     |
| Registered projects                              |             X             |           X           |  X   |     -     |
|                                                  |                           |                       |      |           |
| Dashboard                                        |             X             |           X           |  X   |     X     |
|                                                  |                           |                       |      |           |
| List projects                                    |             X             |           X           |  X   |     -     |
| Project description                              |             X             |           X           |  X   |     -     |
|                                                  |                           |                       |      |           |
| Project's version                                |             X             |           X           |  X   |     -     |
| Create project version                           |             X             |           X           |  -   |     -     |
| Update project version                           |             X             |           X           |  -   |     -     |
|                                                  |                           |                       |      |           |
| Version's tickets                                |             X             |           X           |  X   |     -     |
| Create ticket                                    |             X             |           X           |  -   |     -     |
| Ticket's details                                 |             X             |           X           |  X   |     -     |
| Update ticket                                    |             X             |           X           |  X   |     -     |
|                                                  |                           |                       |      |           |
| Repository epics                                 |             X             |           X           |  X   |     -     |
| Repository features                              |             X             |           X           |  X   |     -     |
| Repository scenarios                             |             X             |           X           |  X   |     -     |
| Update repository                                |             X             |           X           |  -   |     -     |
|                                                  |                           |                       |      |           |
| Create campaign                                  |             X             |           X           |  -   |     -     |
| Retrieve campaigns                               |             X             |           X           |  X   |     -     |
| Fill campaign-occurrence                         |             X             |           X           |  -   |     -     |
| Update campaign-occurrence                       |             X             |           X           |  X   |     -     |
| Retrieve campaign-occurrence                     |             X             |           X           |  X   |     -     |
| Retrieve tickets in c-o                          |             X             |           X           |  X   |     -     |
| Retrieve one ticket in c-o                       |             X             |           X           |  X   |     -     |
| Add scenario to ticket in c-o                    |             X             |           X           |  X   |     -     |
| Retrieve scenario assigned to ticket in c-o      |             X             |           X           |  X   |     -     |
| Update scenario status assigned to ticket in c-o |             X             |           X           |  X   |     -     |
|                                                  |                           |                       |      |           |
| Retrieve bugs in project                         |             X             |           X           |  X   |     -     |
| Retrieve bug                                     |             X             |           X           |  X   |     -     |
| Retrieve all bugs in project-version             |             X             |           X           |  X   |     -     |
| Create bug in project                            |             X             |           X           |  X   |     -     |
| Update bug in project                            |             X             |           X           |  X   |     -     |
|                                                  |                           |                       |      |           |
| Retrieve users                                   |             X             |           X           |  -   |     -     |
| Create user                                      |             X             |           X           |  -   |     -     |
| Update user                                      |             X             |           X           |  -   |     -     |
| Update self password                             |             X             |           X           |  X   |     -     |
|                                                  |                           |                       |      |           |
| Retrieve access token                            |             X             |           X           |  X   |     X     |
| Expire access token                              |             X             |           X           |  X   |     -     |
|                                                  |                           |                       |      |           |
| Push test result for project                     |             X             |           X           |  X   |     -     |
| Export test result for project                   |             X             |           X           |  X   |     -     |
|                                                  |                           |                       |      |           |
| Campaign deliverables                            |             X             |           X           |  X   |     -     |
