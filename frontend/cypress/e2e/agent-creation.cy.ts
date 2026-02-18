/**
 * E2E Tests for Agent Creation
 * 
 * TASK-379: Write E2E test for agent creation
 */

describe('Agent Creation E2E', () => {
  beforeEach(() => {
    // Login first
    cy.visit('/auth/login')
    cy.get('input[name="email"]').type('testuser@example.com')
    cy.get('input[name="password"]').type('SecurePassword123!')
    cy.get('button[type="submit"]').click()
    
    // Navigate to agents page
    cy.visit('/agents/create')
  })

  it('creates a new agent successfully', () => {
    cy.get('input[name="name"]').type('My Test Agent')
    cy.get('textarea[name="description"]').type('An agent for testing')
    cy.get('textarea[name="system_prompt"]').type('You are a helpful assistant')
    
    cy.get('button[type="submit"]').click()
    
    cy.url().should('include', '/agents')
    cy.contains('My Test Agent')
  })

  it('validates required fields', () => {
    cy.get('button[type="submit"]').click()
    
    cy.contains('name is required')
  })

  it('allows selecting different models', () => {
    cy.get('select[name="model"]').select('gpt-4')
    cy.get('select[name="model"]').should('have.value', 'gpt-4')
  })
})
