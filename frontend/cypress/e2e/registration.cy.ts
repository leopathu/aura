/**
 * E2E Tests for User Registration
 * 
 * TASK-378: Write E2E test for user registration
 */

describe('User Registration E2E', () => {
  beforeEach(() => {
    cy.visit('/auth/register')
  })

  it('completes full registration flow', () => {
    cy.get('input[name="full_name"]').type('Test User')
    cy.get('input[name="email"]').type('testuser@example.com')
    cy.get('input[name="password"]').type('SecurePassword123!')
    
    cy.get('button[type="submit"]').click()
    
    cy.url().should('include', '/dashboard')
    cy.contains('Welcome')
  })

  it('shows validation errors for invalid email', () => {
    cy.get('input[name="email"]').type('invalid-email')
    cy.get('input[name="email"]').blur()
    
    cy.contains('valid email')
  })

  it('prevents weak passwords', () => {
    cy.get('input[name="password"]').type('weak')
    cy.get('input[name="password"]').blur()
    
    cy.contains('password')
  })

  it('handles duplicate email gracefully', () => {
    // Assuming user already exists
    cy.get('input[name="email"]').type('existing@example.com')
    cy.get('input[name="password"]').type('SecurePassword123!')
    cy.get('button[type="submit"]').click()
    
    cy.contains('already registered')
  })
})
