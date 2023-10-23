Feature: Register project

  Rule: Only Application admin can register project
    Rule: Project name could not be more than 62 characters
  Rule: Cannot register a project with an existing name

    Scenario Outline: Register project right
      Given "<user>" is logged in
      When he registers "new project"
      Then he "<result>"

      Examples:
        | user            | result   |
        | Aaron Appleseed | succeeds |
        | Paul Abbot      | fails    |