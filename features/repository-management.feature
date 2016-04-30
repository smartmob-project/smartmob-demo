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
