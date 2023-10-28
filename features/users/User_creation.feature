Feature: User creation

  Scenario: Create user
    Given "Aaron Appleseed" is logged in
    When they create "Fileas Utter"
    Then they "succeed"


  Scenario: Update user
    Given "Aaron Appleseed" is logged in
    And the project "test is the new way" exists
    When they add "Fileas Utter" to "test is the new way" as "user"
    Then they "succeed"

