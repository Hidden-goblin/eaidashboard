Feature: Access project

  Rule: Application administrator accesses all project
    Rule: Project administrator and registered user access only their project

    Scenario: Application administrator accesses all
      Given I am "Aaron Appleseed"
      When I list projects
      Then I retrieve the projects
        | project_name        |
        | test is the new way |
        | test                |
        | new way             |

    Scenario: Restricted for PA and User
      Given I am "Monica Upwarder"
      When I list projexts
      Then I retrieve the projects
        | project_name        |
        | new way             |
        | test is the new way |
