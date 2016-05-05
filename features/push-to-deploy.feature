# -*- coding: utf-8 -*-

Feature: Push to deploy

  Scenario: Deploy

    Given Repository "foo" exists
    And Application "foo" exists
    And I clone repository "foo"
    And I submit the "hello-world" sample
    When I push
    Then Application "foo" should be deployed
