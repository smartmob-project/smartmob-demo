# -*- coding: utf-8 -*-

Feature: Repository management

  Scenario: Create a repository

    Given There are no repositories
    When I create a new "foo" repository
    Then I should see "foo" in the repository listing

  Scenario: Delete a repository

    Given Repository "foo" exists
    And Repository "bar" exists
    When I delete repository "foo"
    Then I should see "bar" in the repository listing
    But I should not see "foo" in the repository listing

  Scenario: List repositories

    Given Repository "foo" exists
    And Repository "bar" exists
    And Repository "meh" exists
    When I check the repository listing
    Then I should see "foo" in the repository listing
    And I should see "foo" in the repository listing
    And I should see "foo" in the repository listing
