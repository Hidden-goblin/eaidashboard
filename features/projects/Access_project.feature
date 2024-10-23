Feature: Access project

  Rule: Application administrator accesses all project
    Rule: Project administrator and registered user access only their project

    Scenario: Application administrator accesses all
      Given "Aaron Appleseed" is logged in
      When "Aaron Appleseed" lists projects
      Then "Aaron Appleseed" retrieves the projects
        | project_name        |
        | test is the new way |
        | test                |
        | new way             |

    Scenario: Restricted for PA and User
      Given "Monica Upwarder" is logged in
      When "Monica Upwarder" lists projects
      Then "Monica Upwarder" retrieves the projects
        | project_name        |
        | new way             |
        | test is the new way |
