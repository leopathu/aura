/**
 * Performance Optimization Utilities
 * 
 * This file contains utilities for optimizing perceived and actual performance
 * in the Aura frontend application.
 */

import { useEffect, useRef, useState, useCallback } from 'react'

/**
 * Debounce hook - delays execution of a function until after a delay
 * Useful for search inputs, resize handlers, etc.
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * Throttle hook - limits how often a function can be called
 * Useful for scroll handlers, mouse move handlers, etc.
 */
export function useThrottle<T>(value: T, delay: number = 500): T {
  const [throttledValue, setThrottledValue] = useState<T>(value)
  const lastRan = useRef(Date.now())

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= delay) {
        setThrottledValue(value)
        lastRan.current = Date.now()
      }
    }, delay - (Date.now() - lastRan.current))

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return throttledValue
}

/**
 * Intersection Observer hook for lazy loading
 * Useful for images, infinite scroll, etc.
 */
export function useIntersectionObserver(
  elementRef: React.RefObject<Element>,
  options?: IntersectionObserverInit
): boolean {
  const [isIntersecting, setIsIntersecting] = useState(false)

  useEffect(() => {
    if (!elementRef.current) return

    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting)
    }, options)

    observer.observe(elementRef.current)

    return () => {
      observer.disconnect()
    }
  }, [elementRef, options])

  return isIntersecting
}

/**
 * Prefetch data for smoother navigation
 */
export function usePrefetch<T>(
  fetchFn: () => Promise<T>,
  deps: any[] = []
): void {
  useEffect(() => {
    const prefetch = async () => {
      try {
        await fetchFn()
      } catch (error) {
        // Silently fail - prefetch is a nice-to-have
        console.debug('Prefetch failed:', error)
      }
    }

    prefetch()
  }, deps)
}

/**
 * Optimistic update hook
 * Updates UI immediately while waiting for server response
 */
export function useOptimisticUpdate<T>(
  initialValue: T,
  updateFn: (value: T) => Promise<T>
) {
  const [value, setValue] = useState<T>(initialValue)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const optimisticUpdate = useCallback(
    async (newValue: T) => {
      const previousValue = value
      setValue(newValue) // Optimistic update
      setIsLoading(true)
      setError(null)

      try {
        const result = await updateFn(newValue)
        setValue(result) // Update with server response
      } catch (err) {
        setValue(previousValue) // Rollback on error
        setError(err as Error)
      } finally {
        setIsLoading(false)
      }
    },
    [value, updateFn]
  )

  return { value, isLoading, error, optimisticUpdate }
}

/**
 * Measure component render time (development only)
 */
export function useRenderTime(componentName: string): void {
  const renderCount = useRef(0)
  const startTime = useRef(performance.now())

  useEffect(() => {
    renderCount.current += 1
    const endTime = performance.now()
    const renderTime = endTime - startTime.current

    if (process.env.NODE_ENV === 'development') {
      console.debug(
        `[${componentName}] Render #${renderCount.current}: ${renderTime.toFixed(2)}ms`
      )
    }

    startTime.current = performance.now()
  })
}

/**
 * Virtual scrolling helper for large lists
 */
export function useVirtualScroll<T>(
  items: T[],
  itemHeight: number,
  containerHeight: number
) {
  const [scrollTop, setScrollTop] = useState(0)

  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - 2)
  const endIndex = Math.min(
    items.length,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + 2
  )

  const visibleItems = items.slice(startIndex, endIndex)
  const offsetY = startIndex * itemHeight

  const handleScroll = (e: React.UIEvent<HTMLElement>) => {
    setScrollTop(e.currentTarget.scrollTop)
  }

  return {
    visibleItems,
    offsetY,
    totalHeight: items.length * itemHeight,
    handleScroll,
  }
}

/**
 * Image preloader
 */
export function preloadImage(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve()
    img.onerror = reject
    img.src = src
  })
}

/**
 * Preload multiple images
 */
export function preloadImages(srcs: string[]): Promise<void[]> {
  return Promise.all(srcs.map(preloadImage))
}

/**
 * Local storage with expiration
 */
export function setLocalStorageWithExpiry(
  key: string,
  value: any,
  expiryMs: number
): void {
  const item = {
    value,
    expiry: Date.now() + expiryMs,
  }
  localStorage.setItem(key, JSON.stringify(item))
}

export function getLocalStorageWithExpiry<T>(key: string): T | null {
  const itemStr = localStorage.getItem(key)
  if (!itemStr) return null

  try {
    const item = JSON.parse(itemStr)
    if (Date.now() > item.expiry) {
      localStorage.removeItem(key)
      return null
    }
    return item.value as T
  } catch {
    return null
  }
}

/**
 * Request Animation Frame hook for smooth animations
 */
export function useAnimationFrame(callback: (deltaTime: number) => void) {
  const requestRef = useRef<number>()
  const previousTimeRef = useRef<number>()

  useEffect(() => {
    const animate = (time: number) => {
      if (previousTimeRef.current !== undefined) {
        const deltaTime = time - previousTimeRef.current
        callback(deltaTime)
      }
      previousTimeRef.current = time
      requestRef.current = requestAnimationFrame(animate)
    }

    requestRef.current = requestAnimationFrame(animate)
    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current)
      }
    }
  }, [callback])
}

/**
 * Idle detection - run expensive operations when user is idle
 */
export function useIdleDetection(idleTime: number = 3000): boolean {
  const [isIdle, setIsIdle] = useState(false)
  const timeoutId = useRef<NodeJS.Timeout>()

  useEffect(() => {
    const handleActivity = () => {
      setIsIdle(false)
      if (timeoutId.current) {
        clearTimeout(timeoutId.current)
      }
      timeoutId.current = setTimeout(() => setIsIdle(true), idleTime)
    }

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart']
    events.forEach(event => {
      document.addEventListener(event, handleActivity)
    })

    handleActivity() // Initialize

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity)
      })
      if (timeoutId.current) {
        clearTimeout(timeoutId.current)
      }
    }
  }, [idleTime])

  return isIdle
}

/**
 * Network status detection
 */
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  )

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return isOnline
}

/**
 * Batch state updates to reduce re-renders
 */
export function useBatchedState<T>(initialValue: T) {
  const [state, setState] = useState<T>(initialValue)
  const pendingUpdates = useRef<Partial<T>[]>([])
  const timeoutRef = useRef<NodeJS.Timeout>()

  const batchUpdate = useCallback((updates: Partial<T>) => {
    pendingUpdates.current.push(updates)

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      setState(prevState => {
        const mergedUpdates = pendingUpdates.current.reduce(
          (acc, update) => ({ ...acc, ...update }),
          {}
        )
        pendingUpdates.current = []
        return { ...prevState, ...mergedUpdates }
      })
    }, 16) // ~60fps
  }, [])

  return [state, batchUpdate] as const
}
