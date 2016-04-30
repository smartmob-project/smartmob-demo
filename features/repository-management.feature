# -*- coding: utf-8 -*-

Feature: Repository management

  Scenario: Create a repository

    Given I create a new "foo" repository
    When I list existing repositories
    Then I should see "foo" in the repository listing
   
