Feature: User creation

  Scenario: Create user
    Given I am "Aaron Appleseed"
    When I create "Fileas Utter"
    Then I "succeed"

  # Todo update via UI
  Scenario: Update user
    Given I am "Aaron Appleseed"
    And the project "test is the new way" exists
    When I add "Fileas Utter" to "test is the new way" as "user"
    Then I "succeed"

