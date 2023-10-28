Feature: Access project

  Rule: Application administrator accesses all project
    Rule: Project administrator and registered user access only their project

    Scenario: Application administrator accesses all
      Given "Aaron Appleseed" is logged in
      When he lists projects
      Then he retrieves the projects
        | project_name        |
        | test is the new way |
        | test                |
        | new way             |

    Scenario: Restricted for PA and User
      Given "Monica Upwarder" is logged in
      When he lists projexts
      Then he retrieves the projects
        | project_name        |
        | new way             |
        | test is the new way |
