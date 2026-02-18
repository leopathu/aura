# Aura Design System

**Version:** 1.0  
**Last Updated:** February 19, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Color Palette](#color-palette)
3. [Typography](#typography)
4. [Spacing System](#spacing-system)
5. [Components](#components)
6. [Animations & Transitions](#animations--transitions)
7. [Responsive Design](#responsive-design)
8. [Accessibility](#accessibility)
9. [Best Practices](#best-practices)

---

## Overview

The Aura Design System provides a consistent, accessible, and delightful user experience across the entire platform. Built on **Tailwind CSS**, our design system emphasizes:

- **Clarity**: Clean, readable interfaces with clear information hierarchy
- **Consistency**: Predictable patterns and reusable components
- **Accessibility**: WCAG 2.1 AA compliant with keyboard navigation
- **Performance**: Optimized for fast loading and smooth interactions
- **Responsiveness**: Mobile-first design that works on all devices

---

## Color Palette

### Primary Colors

Our primary color palette uses purple as the main brand color, with blue for accents and actions.

```css
/* Purple - Primary Brand Color */
purple-50:  #faf5ff
purple-100: #f3e8ff
purple-200: #e9d5ff
purple-300: #d8b4fe
purple-400: #c084fc
purple-500: #a855f7
purple-600: #9333ea  /* Primary */
purple-700: #7e22ce
purple-800: #6b21a8
purple-900: #581c87

/* Blue - Accent & Actions */
blue-50:  #eff6ff
blue-100: #dbeafe
blue-200: #bfdbfe
blue-300: #93c5fd
blue-400: #60a5fa
blue-500: #3b82f6   /* Primary Blue */
blue-600: #2563eb
blue-700: #1d4ed8
blue-800: #1e40af
blue-900: #1e3a8a
```

### Semantic Colors

```css
/* Success - Green */
success:     #10b981  (green-500)
success-light: #d1fae5  (green-100)
success-dark:  #047857  (green-700)

/* Warning - Amber */
warning:     #f59e0b  (amber-500)
warning-light: #fef3c7  (amber-100)
warning-dark:  #b45309  (amber-700)

/* Error - Red */
error:       #ef4444  (red-500)
error-light:   #fee2e2  (red-100)
error-dark:    #b91c1c  (red-700)

/* Info - Blue */
info:        #3b82f6  (blue-500)
info-light:    #dbeafe  (blue-100)
info-dark:     #1d4ed8  (blue-700)
```

### Neutral Colors

```css
/* Grays for text, backgrounds, borders */
gray-50:  #f9fafb
gray-100: #f3f4f6
gray-200: #e5e7eb
gray-300: #d1d5db
gray-400: #9ca3af
gray-500: #6b7280
gray-600: #4b5563
gray-700: #374151
gray-800: #1f2937
gray-900: #111827

/* Special */
white: #ffffff
black: #000000
transparent: transparent
```

### Usage Guidelines

#### Text Colors
- **Primary text**: `text-gray-900` (dark mode: `text-gray-100`)
- **Secondary text**: `text-gray-600` (dark mode: `text-gray-400`)
- **Muted text**: `text-gray-500` (dark mode: `text-gray-500`)
- **Disabled text**: `text-gray-400` (dark mode: `text-gray-600`)

#### Background Colors
- **Page background**: `bg-gray-50` (dark mode: `bg-gray-900`)
- **Card background**: `bg-white` (dark mode: `bg-gray-800`)
- **Hover states**: `hover:bg-gray-100` (dark mode: `hover:bg-gray-700`)

#### Border Colors
- **Default borders**: `border-gray-200` (dark mode: `border-gray-700`)
- **Focus borders**: `focus:border-purple-500`
- **Error borders**: `border-red-500`

---

## Typography

### Font Families

```css
/* Sans-serif - Primary */
font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 
           "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif

/* Monospace - Code */
font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, 
           "Cascadia Code", "Courier New", monospace
```

### Font Sizes

```css
text-xs:   0.75rem   (12px)  - Captions, labels
text-sm:   0.875rem  (14px)  - Small text, secondary info
text-base: 1rem      (16px)  - Body text (default)
text-lg:   1.125rem  (18px)  - Emphasized text
text-xl:   1.25rem   (20px)  - Small headings
text-2xl:  1.5rem    (24px)  - Section headings
text-3xl:  1.875rem  (30px)  - Page headings
text-4xl:  2.25rem   (36px)  - Hero headings
text-5xl:  3rem      (48px)  - Marketing headings
text-6xl:  3.75rem   (60px)  - Extra large headings
```

### Font Weights

```css
font-thin:       100
font-extralight: 200
font-light:      300
font-normal:     400  (default)
font-medium:     500  (emphasized text)
font-semibold:   600  (headings)
font-bold:       700  (strong emphasis)
font-extrabold:  800
font-black:      900
```

### Line Heights

```css
leading-none:   1      - Tight, for headings
leading-tight:  1.25   - Headings
leading-snug:   1.375  - Dense content
leading-normal: 1.5    - Body text (default)
leading-relaxed: 1.625 - Comfortable reading
leading-loose:  2      - Very spacious
```

### Typography Scale Examples

```tsx
// Page Title
<h1 className="text-3xl font-bold text-gray-900">Page Title</h1>

// Section Heading
<h2 className="text-2xl font-semibold text-gray-800">Section Heading</h2>

// Subsection Heading
<h3 className="text-xl font-semibold text-gray-800">Subsection</h3>

// Body Text
<p className="text-base text-gray-700 leading-normal">Body paragraph...</p>

// Small Text
<span className="text-sm text-gray-600">Helper text or metadata</span>

// Caption
<span className="text-xs text-gray-500">Caption or label</span>
```

---

## Spacing System

### Base Unit: 4px (0.25rem)

Our spacing system uses a **4px base unit** for consistent rhythm throughout the UI.

```css
0:    0px
0.5:  2px    (0.125rem)
1:    4px    (0.25rem)
1.5:  6px    (0.375rem)
2:    8px    (0.5rem)
2.5:  10px   (0.625rem)
3:    12px   (0.75rem)
3.5:  14px   (0.875rem)
4:    16px   (1rem)
5:    20px   (1.25rem)
6:    24px   (1.5rem)
7:    28px   (1.75rem)
8:    32px   (2rem)
10:   40px   (2.5rem)
12:   48px   (3rem)
14:   56px   (3.5rem)
16:   64px   (4rem)
20:   80px   (5rem)
24:   96px   (6rem)
```

### Common Spacing Patterns

#### Padding
```tsx
// Card padding
<div className="p-6">Content</div>  // 24px all sides

// Section padding
<section className="px-8 py-12">Content</section>  // 32px horizontal, 48px vertical

// Button padding
<button className="px-4 py-2">Button</button>  // 16px horizontal, 8px vertical
```

#### Margin
```tsx
// Stack elements vertically
<div className="space-y-4">  // 16px gap between children
  <div>Item 1</div>
  <div>Item 2</div>
</div>

// Horizontal spacing
<div className="space-x-2">  // 8px gap
  <button>Cancel</button>
  <button>Save</button>
</div>
```

#### Gap (Flexbox/Grid)
```tsx
// Grid gap
<div className="grid grid-cols-3 gap-4">...</div>  // 16px gap

// Flex gap
<div className="flex gap-6">...</div>  // 24px gap
```

---

## Components

### Button

#### Variants

**Primary Button**
```tsx
<button className="px-4 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
  Primary Action
</button>
```

**Secondary Button**
```tsx
<button className="px-4 py-2 bg-white text-gray-700 font-medium border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors">
  Secondary Action
</button>
```

**Danger Button**
```tsx
<button className="px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors">
  Delete
</button>
```

**Ghost Button**
```tsx
<button className="px-4 py-2 text-purple-600 font-medium rounded-lg hover:bg-purple-50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors">
  Text Only
</button>
```

#### Sizes
- **Small**: `px-3 py-1.5 text-sm`
- **Medium (default)**: `px-4 py-2 text-base`
- **Large**: `px-6 py-3 text-lg`

### Input

```tsx
<input
  type="text"
  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
  placeholder="Enter text..."
/>

// With error state
<input
  className="w-full px-4 py-2 border border-red-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
/>
```

### Card

```tsx
<div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
  <h3 className="text-lg font-semibold text-gray-900 mb-2">Card Title</h3>
  <p className="text-gray-600">Card content goes here...</p>
</div>
```

### Modal

```tsx
{/* Overlay */}
<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
  {/* Modal */}
  <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
    {/* Header */}
    <div className="px-6 py-4 border-b border-gray-200">
      <h2 className="text-xl font-semibold text-gray-900">Modal Title</h2>
    </div>
    
    {/* Body */}
    <div className="px-6 py-4">
      <p className="text-gray-700">Modal content...</p>
    </div>
    
    {/* Footer */}
    <div className="px-6 py-4 bg-gray-50 flex justify-end space-x-2">
      <button className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
        Cancel
      </button>
      <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
        Confirm
      </button>
    </div>
  </div>
</div>
```

### Badge

```tsx
{/* Status badges */}
<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
  Active
</span>

<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
  Inactive
</span>

<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
  Error
</span>
```

### Alert

```tsx
{/* Success Alert */}
<div className="p-4 rounded-lg bg-green-50 border border-green-200">
  <div className="flex">
    <div className="flex-shrink-0">
      {/* Icon */}
    </div>
    <div className="ml-3">
      <h3 className="text-sm font-medium text-green-800">Success</h3>
      <p className="mt-1 text-sm text-green-700">Your changes have been saved.</p>
    </div>
  </div>
</div>

{/* Error Alert */}
<div className="p-4 rounded-lg bg-red-50 border border-red-200">
  <div className="flex">
    <div className="flex-shrink-0">
      {/* Icon */}
    </div>
    <div className="ml-3">
      <h3 className="text-sm font-medium text-red-800">Error</h3>
      <p className="mt-1 text-sm text-red-700">Something went wrong.</p>
    </div>
  </div>
</div>
```

### Toast Notification

```tsx
<div className="fixed bottom-4 right-4 z-50 max-w-sm w-full">
  <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4 animate-slide-in">
    <div className="flex items-start">
      <div className="flex-shrink-0">
        {/* Icon */}
      </div>
      <div className="ml-3 flex-1">
        <p className="text-sm font-medium text-gray-900">Notification</p>
        <p className="mt-1 text-sm text-gray-600">Message content...</p>
      </div>
      <button className="ml-4 flex-shrink-0">
        {/* Close icon */}
      </button>
    </div>
  </div>
</div>
```

### Skeleton Loader

```tsx
{/* Text skeleton */}
<div className="animate-pulse">
  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
</div>

{/* Card skeleton */}
<div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
  <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
  <div className="space-y-2">
    <div className="h-4 bg-gray-200 rounded"></div>
    <div className="h-4 bg-gray-200 rounded w-5/6"></div>
  </div>
</div>
```

### Loading Spinner

```tsx
{/* Small spinner */}
<div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-purple-600"></div>

{/* Medium spinner */}
<div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-purple-600"></div>

{/* Large spinner */}
<div className="animate-spin rounded-full h-12 w-12 border-3 border-gray-300 border-t-purple-600"></div>
```

### Progress Bar

```tsx
<div className="w-full bg-gray-200 rounded-full h-2">
  <div className="bg-purple-600 h-2 rounded-full transition-all duration-300" style={{ width: '60%' }}></div>
</div>

{/* With label */}
<div>
  <div className="flex justify-between mb-1">
    <span className="text-sm font-medium text-gray-700">Progress</span>
    <span className="text-sm font-medium text-gray-700">60%</span>
  </div>
  <div className="w-full bg-gray-200 rounded-full h-2">
    <div className="bg-purple-600 h-2 rounded-full" style={{ width: '60%' }}></div>
  </div>
</div>
```

### Empty State

```tsx
<div className="text-center py-12">
  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
    {/* Icon */}
  </div>
  <h3 className="text-lg font-semibold text-gray-900 mb-2">No items yet</h3>
  <p className="text-gray-600 mb-4">Get started by creating your first item.</p>
  <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
    Create Item
  </button>
</div>
```

### Tooltip

```tsx
{/* Tooltip container (simplified - use a library like Radix UI or Headless UI) */}
<div className="relative group">
  <button className="px-4 py-2 bg-purple-600 text-white rounded-lg">
    Hover me
  </button>
  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
    Tooltip text
    <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
  </div>
</div>
```

---

## Animations & Transitions

### Transition Durations

```css
transition-none:    0ms
transition-75:      75ms
transition-100:     100ms
transition-150:     150ms   (default for most interactions)
transition-200:     200ms   (hover states)
transition-300:     300ms   (moderate animations)
transition-500:     500ms   (slower animations)
transition-700:     700ms
transition-1000:    1000ms
```

### Common Transitions

```tsx
// Color transitions (buttons, links)
className="transition-colors duration-200"

// All properties
className="transition-all duration-300"

// Opacity (fade in/out)
className="transition-opacity duration-200"

// Transform (scale, translate)
className="transition-transform duration-200"

// Shadow (elevation change)
className="transition-shadow duration-200"
```

### Animations

```css
/* Defined in tailwind.config.js */
@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .5; }
}

@keyframes bounce {
  0%, 100% { transform: translateY(-25%); }
  50% { transform: translateY(0); }
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slide-in {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

@keyframes scale-in {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
```

### Usage Examples

```tsx
// Spinning loader
<div className="animate-spin">...</div>

// Pulsing indicator
<div className="animate-pulse">...</div>

// Fade in on mount
<div className="animate-fade-in">...</div>

// Slide in notification
<div className="animate-slide-in">...</div>

// Scale in modal
<div className="animate-scale-in">...</div>

// Hover scale
<button className="hover:scale-105 transform transition-transform">...</button>

// Hover lift (shadow + translate)
<div className="hover:-translate-y-1 hover:shadow-lg transition-all">...</div>
```

---

## Responsive Design

### Breakpoints

```css
sm:   640px   (Small devices - phones in landscape)
md:   768px   (Medium devices - tablets)
lg:   1024px  (Large devices - desktops)
xl:   1280px  (Extra large - wide desktops)
2xl:  1536px  (2XL - very wide screens)
```

### Mobile-First Approach

All styles are mobile-first. Use breakpoint prefixes to apply styles at larger sizes:

```tsx
// Stack on mobile, grid on tablet+
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  ...
</div>

// Full width on mobile, contained on desktop
<div className="w-full lg:w-1/2 lg:mx-auto">
  ...
</div>

// Hide on mobile, show on desktop
<div className="hidden lg:block">
  Desktop only content
</div>

// Show on mobile, hide on desktop
<div className="block lg:hidden">
  Mobile only content
</div>
```

### Responsive Typography

```tsx
<h1 className="text-2xl md:text-3xl lg:text-4xl font-bold">
  Responsive Heading
</h1>

<p className="text-sm md:text-base lg:text-lg">
  Responsive body text
</p>
```

### Responsive Spacing

```tsx
// Less padding on mobile, more on desktop
<div className="p-4 md:p-6 lg:p-8">
  ...
</div>

// Tighter spacing on mobile
<div className="space-y-2 md:space-y-4 lg:space-y-6">
  ...
</div>
```

---

## Accessibility

### Focus States

Always provide visible focus indicators:

```tsx
// Button focus
<button className="focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2">
  ...
</button>

// Input focus
<input className="focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent" />
```

### ARIA Labels

```tsx
// Button with icon only
<button aria-label="Close modal">
  <XIcon className="w-5 h-5" />
</button>

// Loading state
<button disabled aria-busy="true">
  <Spinner className="animate-spin" />
  <span className="sr-only">Loading...</span>
</button>

// Screen reader only text
<span className="sr-only">For screen readers only</span>
```

### Keyboard Navigation

- All interactive elements must be keyboard accessible
- Use semantic HTML (`<button>`, `<a>`, `<input>`)
- Support Tab, Enter, Escape, Arrow keys where appropriate
- Trap focus in modals

### Color Contrast

Minimum contrast ratios (WCAG AA):
- **Normal text**: 4.5:1
- **Large text** (18px+ or 14px+ bold): 3:1
- **UI components**: 3:1

Our color palette meets these requirements:
- `text-gray-900` on `bg-white`: 16.8:1 ✅
- `text-gray-600` on `bg-white`: 5.7:1 ✅
- `text-purple-600` on `bg-white`: 5.5:1 ✅

---

## Best Practices

### Component Development

1. **Use Semantic HTML**: Use proper HTML elements (`<button>`, `<nav>`, `<main>`, etc.)
2. **Composable Components**: Build small, reusable components
3. **Consistent Props**: Use consistent prop naming across components
4. **TypeScript**: Always type component props
5. **Accessibility First**: Include ARIA labels, keyboard support, focus management

### Styling Conventions

1. **Tailwind Over Custom CSS**: Prefer Tailwind utilities over custom CSS
2. **Component Classes**: Extract repeated patterns into components, not CSS classes
3. **Responsive First**: Always consider mobile experience first
4. **Consistent Spacing**: Use spacing scale (4px increments)
5. **State Variants**: Use Tailwind variants (`hover:`, `focus:`, `disabled:`)

### Performance

1. **Lazy Load Images**: Use Next.js Image component with lazy loading
2. **Code Splitting**: Use dynamic imports for large components
3. **Memoization**: Use `React.memo` for expensive components
4. **Optimize Animations**: Use `transform` and `opacity` (GPU-accelerated)
5. **Reduce Bundle Size**: Import only what you need

### Dark Mode (Future)

Prepare for dark mode using Tailwind's `dark:` variant:

```tsx
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  Content
</div>
```

---

## Quick Reference

### Common Patterns

```tsx
// Page container
<div className="min-h-screen bg-gray-50">
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    {/* Content */}
  </div>
</div>

// Card grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <div className="bg-white rounded-xl shadow-sm p-6">Card</div>
</div>

// Form group
<div className="space-y-4">
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">
      Label
    </label>
    <input className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500" />
  </div>
</div>

// Button group
<div className="flex space-x-2">
  <button className="px-4 py-2 bg-white border border-gray-300 rounded-lg">Cancel</button>
  <button className="px-4 py-2 bg-purple-600 text-white rounded-lg">Save</button>
</div>

// Loading state
<div className="flex items-center justify-center py-12">
  <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-purple-600"></div>
</div>

// Error message
<p className="text-sm text-red-600 mt-1">This field is required</p>

// Success message
<p className="text-sm text-green-600 mt-1">Changes saved successfully</p>
```

---

## Resources

- **Tailwind CSS Documentation**: https://tailwindcss.com/docs
- **Headless UI (accessible components)**: https://headlessui.com
- **Radix UI (primitive components)**: https://www.radix-ui.com
- **Hero Icons**: https://heroicons.com
- **WCAG Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/

---

**Maintained by the Aura Design Team**  
For questions or suggestions, create an issue in the repository.
