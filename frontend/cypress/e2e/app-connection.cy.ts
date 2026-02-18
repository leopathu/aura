/**
 * E2E Tests for App Connection
 * 
 * TASK-380: Write E2E test for app connection
 */

describe('App Connection E2E', () => {
  beforeEach(() => {
    // Login
    cy.visit('/auth/login')
    cy.get('input[name="email"]').type('testuser@example.com')
    cy.get('input[name="password"]').type('SecurePassword123!')
    cy.get('button[type="submit"]').click()
    
    // Navigate to integrations
    cy.visit('/integrations')
  })

  it('displays available apps', () => {
    cy.contains('Gmail')
    cy.contains('Slack')
    cy.contains('Jira')
  })

  it('initiates OAuth connection for Gmail', () => {
    cy.contains('Gmail').parent().find('button').click()
    
    // Should redirect to OAuth or show auth modal
    cy.url().should('match', /oauth|connect/)
  })

  it('connects app with API key', () => {
    cy.contains('Slack').parent().find('button').click()
    
    cy.get('input[name="api_key"]').type('test-api-key')
    cy.get('button[type="submit"]').click()
    
    cy.contains('Connected')
  })

  it('disconnects an app', () => {
    cy.contains('Connected').parent().find('button[aria-label="Disconnect"]').click()
    cy.contains('Confirm').click()
    
    cy.contains('Disconnected')
  })
})
