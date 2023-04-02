# Workflows

<a hx-get="/documentation/index.md"> <img height="20" src="/assets/chevron-left-duo.svg" width="20"/> Back </a> | <a 
hx-get="/documentation/index.md"> Index </a> | <a 
hx-get="/documentation/01-workflows.md"> Next <img height="20" src="/assets/chevron-right-duo.svg" width="20"/> </a>

[TOC]


Which work process could you use with this tool? In this section, I will provide some thoughts on how you could work 
when you want to make both manual and automated testing campaign using open or used by development team tools.

I heavily rely on concept like epic, feature, scenarios which might have different acceptation. As I use as test 
automation framework `Behave`, most of the work is built related to what could produce this framework in terms of 
extract.

Lets start!

## Some definitions

These are my definitions of the terms. To be complete, I'll give you the ChatGPT ones.

### Epic

I call **epic** a business unit the application (under test) handle. It might be Contract, Customer, Application 
Version etc.

One epic embraces multiples business rules which could be broken in smaller part.

ChatGPT defines epic as: 

```
A large, high-level requirement or user story that describes a significant feature or functionality of a software application.
In Agile development, Epics are broken down into smaller, more manageable user stories that can be completed in a single sprint.
In Waterfall development, Epics may be broken down into phases or stages of the project, each with its own set of requirements and deliverables.
```

### Feature

I call **feature** a functionality linked to an epic. It might be "create a Contract", "update a Customer", "deliver an 
Application Version" etc. 

The feature describes all rules applicable to the action for this specific topic (epic).

ChatGPT defines feature as:

```
A specific function or characteristic of a software application that is designed to provide value to the end user.
In Agile development, Features are broken down into user stories that can be completed in a single sprint.
In Waterfall development, Features may be described in detail in the requirements gathering phase, and implemented and tested in later stages of the project.
```

### Scenario

I call **scenario** an illustration on how a specific rule behaves with the application.

I would define in prerequisite, action, post conditions.

- prerequisite: the complete application state description which matter on the action
- action: the feature which is used. I am fan of "only one action"
- post condition: the application expected resulting state

ChatGPT defines scenario as:

```
In the context of software development, a "Scenario" typically refers to a specific use case or sequence of steps that describe 
how a user interacts with a software application to accomplish a task or achieve a goal.

Scenarios are often used as part of the requirements gathering and user experience design process to ensure 
that the software application meets the needs and expectations of its users.
Scenarios may include detailed descriptions of the user's actions, as well as any inputs, outputs, or system 
responses that occur as a result of those actions.

Scenarios can be written in various formats, such as user stories, flowcharts, or diagrams.
They are often used to guide the development process and ensure that the software application is designed and implemented in a way
that supports the user's needs and goals. Scenarios may also be used to define 
and validate acceptance criteria for software testing and quality assurance purposes.

Overall, scenarios are an important tool in software development to ensure that the software application is developed 
with the end user in mind and meets their specific needs and requirements.
```

### Project

A project is the application under test. 

Currently, the project is a way to sandbox items. There is no specific workflow management, nor user right management.

I use the name of the application as the project's name. You can use nearly any name.

### Version

A version is an increment of the application under test. The application versioning is free and should be the 
versioning convention used on the project. 

I use the version as way to track test work.

### Ticket

The ticket is anything describing work onto the project-version. I only record a reference and a title for each 
ticket as this tool is not currently a ticket management tool. 

A good process is, in my humble opinion, to have one version per ticket. If the ticket release is postponed then the 
ticket release version is updated.


### Campaign

A campaign is a set of ticket which need to be validated through executing (manually or automatically) scenarios.

The campaign tracks tickets and bugs.

### Occurrence

Occurrence is a way to divide workload into phases. It can be used to record regression test results from automated 
tests.

It may be useful if the campaign scope as frequent updates.  
