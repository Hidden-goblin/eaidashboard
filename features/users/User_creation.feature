Feature: User creation

  @in_dev
  Scenario: Create user
    Given "Aaron Appleseed" is logged in
    And the following projects exist
      | project_name        |
      | test is the new way |
    When "Aaron Appleseed" creates "Fileas Utter"
    Then "Aaron Appleseed" "succeed"


  Scenario: Update user
    Given "Aaron Appleseed" is logged in
    And the following projects exist
      | project_name |
      | new way      |
    When "Aaron Appleseed" adds "Fileas Utter" to "test is the new way" as "user"
    Then "Aaron Appleseed" "succeed"

