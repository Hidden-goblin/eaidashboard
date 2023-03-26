# Workflows

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