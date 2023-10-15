Feature: Register project

  Rule: Only Application admin can register project
    Rule: Project name could not be more than 62 characters
  Rule: Cannot register a project with an existing name

    Scenario Outline: Register project right
      Given I am "<user>"
      When I register a new project
      Then I "<result>"

      Examples:
        | user            | result  |
        | Aaron Appleseed | succeed |
        | Paul Abbot      | fail    |