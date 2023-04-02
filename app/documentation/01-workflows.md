# Workflows

<a hx-get="/documentation/00-workflows.md"> <img height="20" src="/assets/chevron-left-duo.svg" width="20"/> Back </a> 
| <a 
hx-get="/documentation/index.md"> Index </a> | <a 
hx-get="/documentation/02-workflows.md"> Next <img height="20" src="/assets/chevron-right-duo.svg" width="20"/> </a>

[TOC]

## Main flow

The main flow is a very basic way to monitor the (test) project advancement.

Given you have a project (application under test or AUT) and a new version will be produced when the implementation 
start then your test starts.

You will record all tickets in the version. You will estimate the workload to test each ticket and, you will be able 
to foresee an end date. With this work, you will also check that each ticket is really testable and highlight 
reasons a ticket is not testable.

You can then send a first test plan with the scope, the impediments and, the estimations. 

You can monitor each ticket status from recorded to done and check bugs (if you have no bug tracking tool) on the 
version.

<img alt="A basic workflow for managing test campaign." src="/assets/documentation/simple_workflow.svg" 
title="simple_workflow" width="1200"/>


## Using one campaign occurrence

An enhanced flow is to use campaign and campaign occurrence. The starting point is the same: new version in the AUT.

You will record all tickets in the version. You will then record a test campaign and a new occurrence. You will link 
the recorded tickets to the campaign. If some tickets are not in the test scope, you might exclude them from the 
campaign.

At this point, you can pick scenarios from the test repository and link to the tickets.

You can then send a first test plan with the campaign scope, the impediments, the estimations and, the campaign details.

You might reissue the test plan when any of its content updates.

Daily you can snapshot the test advancement and issue a graphical view of the campaign status. 

<img alt="A single occurrence campaign workflow for managing test campaign." 
src="/assets/documentation/one_occurrence_campaign.svg" 
title="one_occurrence_campaign" width="1200"/>

The tool is design to help managing campaign occurrence: 

- create a basic test plan
- create an evidence template for each ticket
- create a basic test exit report

## Using multiple campaign occurrence

Multiple campaign occurrence is there where you need to capture 

- The scope evolution, mainly in the _add_ to the scope
- The different test activity
  - functional test
  - non-functional test
  - regression etc.

<img alt="A multi occurrence campaign workflow for managing test campaign." 
src="/assets/documentation/multiple_occurrence_campaign.svg" 
title="multiple_occurrence_campaign"/>