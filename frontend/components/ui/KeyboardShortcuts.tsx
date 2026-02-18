'use client'

import React, { createContext, useContext, useEffect, useCallback } from 'react'

export interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  meta?: boolean
  description: string
  action: () => void
  category?: string
}

interface KeyboardShortcutsContextType {
  registerShortcut: (id: string, shortcut: KeyboardShortcut) => void
  unregisterShortcut: (id: string) => void
  getShortcuts: () => Map<string, KeyboardShortcut>
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextType | undefined>(undefined)

export const useKeyboardShortcuts = () => {
  const context = useContext(KeyboardShortcutsContext)
  if (!context) {
    throw new Error('useKeyboardShortcuts must be used within KeyboardShortcutsProvider')
  }
  return context
}

interface KeyboardShortcutsProviderProps {
  children: React.ReactNode
}

export const KeyboardShortcutsProvider: React.FC<KeyboardShortcutsProviderProps> = ({ children }) => {
  const shortcutsRef = React.useRef<Map<string, KeyboardShortcut>>(new Map())

  const registerShortcut = useCallback((id: string, shortcut: KeyboardShortcut) => {
    shortcutsRef.current.set(id, shortcut)
  }, [])

  const unregisterShortcut = useCallback((id: string) => {
    shortcutsRef.current.delete(id)
  }, [])

  const getShortcuts = useCallback(() => {
    return new Map(shortcutsRef.current)
  }, [])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return
      }

      for (const [, shortcut] of shortcutsRef.current) {
        const matchesKey = event.key.toLowerCase() === shortcut.key.toLowerCase()
        const matchesCtrl = shortcut.ctrl === undefined || shortcut.ctrl === event.ctrlKey
        const matchesShift = shortcut.shift === undefined || shortcut.shift === event.shiftKey
        const matchesAlt = shortcut.alt === undefined || shortcut.alt === event.altKey
        const matchesMeta = shortcut.meta === undefined || shortcut.meta === event.metaKey

        if (matchesKey && matchesCtrl && matchesShift && matchesAlt && matchesMeta) {
          event.preventDefault()
          shortcut.action()
          break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <KeyboardShortcutsContext.Provider value={{ registerShortcut, unregisterShortcut, getShortcuts }}>
      {children}
    </KeyboardShortcutsContext.Provider>
  )
}

export const useShortcut = (id: string, shortcut: KeyboardShortcut) => {
  const { registerShortcut, unregisterShortcut } = useKeyboardShortcuts()

  useEffect(() => {
    registerShortcut(id, shortcut)
    return () => unregisterShortcut(id)
  }, [id, shortcut, registerShortcut, unregisterShortcut])
}

// Keyboard shortcuts help modal
interface ShortcutsHelpModalProps {
  isOpen: boolean
  onClose: () => void
}

export const ShortcutsHelpModal: React.FC<ShortcutsHelpModalProps> = ({ isOpen, onClose }) => {
  const { getShortcuts } = useKeyboardShortcuts()
  
  if (!isOpen) return null

  const shortcuts = Array.from(getShortcuts().values())
  const categories = [...new Set(shortcuts.map(s => s.category || 'General'))]

  const formatShortcut = (shortcut: KeyboardShortcut) => {
    const keys: string[] = []
    if (shortcut.ctrl) keys.push('Ctrl')
    if (shortcut.shift) keys.push('Shift')
    if (shortcut.alt) keys.push('Alt')
    if (shortcut.meta) keys.push('⌘')
    keys.push(shortcut.key.toUpperCase())
    return keys
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fade-in" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full overflow-hidden animate-scale-in" onClick={(e) => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Keyboard Shortcuts</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
          {categories.map(category => (
            <div key={category} className="mb-6 last:mb-0">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">{category}</h3>
              <div className="space-y-2">
                {shortcuts
                  .filter(s => (s.category || 'General') === category)
                  .map((shortcut, index) => (
                    <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <span className="text-sm text-gray-700">{shortcut.description}</span>
                      <div className="flex space-x-1">
                        {formatShortcut(shortcut).map((key, i) => (
                          <kbd
                            key={i}
                            className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded"
                          >
                            {key}
                          </kbd>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
        
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 text-center">
          <p className="text-xs text-gray-600">Press <kbd className="px-2 py-1 text-xs font-semibold bg-gray-100 border border-gray-300 rounded">?</kbd> to toggle this help</p>
        </div>
      </div>
    </div>
  )
}
