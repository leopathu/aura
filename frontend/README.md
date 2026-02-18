# Aura Frontend

Next.js 14 frontend for the Aura Personal AI Assistant Platform.

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Authentication pages (login, register)
│   ├── (dashboard)/       # Protected dashboard pages
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ui/               # Reusable UI components
│   └── layout/           # Layout components
├── lib/                  # Utilities and helpers
│   └── api.ts           # API client (axios)
├── store/               # Zustand state management
│   └── authStore.ts     # Authentication store
├── types/               # TypeScript type definitions
│   └── index.ts         # Shared types
├── public/              # Static assets
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── tailwind.config.js   # Tailwind CSS config
├── next.config.js       # Next.js config
└── Dockerfile          # Docker configuration
```

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.4
- **State Management**: Zustand 4.4
- **HTTP Client**: Axios 1.6
- **Markdown**: react-markdown 9.0
- **Date Utilities**: date-fns 3.2

## Setup

### Prerequisites

- Node.js 20+
- npm or yarn

### Installation

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Set up environment variables**
```bash
cp .env.local.example .env.local
# Edit .env.local with your values
```

3. **Run development server**
```bash
npm run dev
```

The app will be available at `http://localhost:3001`

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8001)
- `NEXT_PUBLIC_APP_NAME`: Application name
- `NEXT_PUBLIC_APP_VERSION`: Version number

## Development

### Available Scripts

- `npm run dev` - Start development server on port 3001
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Check TypeScript types

### Running with Docker

```bash
# From the root directory
docker compose up frontend
```

## Features

### Current
- ✅ Next.js 14 with App Router
- ✅ TypeScript configuration
- ✅ Tailwind CSS styling
- ✅ Zustand state management
- ✅ Axios API client with interceptors
- ✅ Authentication store
- ✅ Type definitions
- ✅ Responsive design

### Planned
- Authentication pages (login, register)
- Protected route middleware
- Dashboard layout
- Organization management UI
- Agent creation and chat interface
- Credentials management
- App connection UI
- Automation builder
- Real-time streaming UI

## Design System

### Colors

**Primary (Purple)**
- 50-900 scale from light to dark
- Main: `primary-600` (#9333ea)
- Hover: `primary-700` (#7c3aed)

**Accent (Blue)**
- 50-900 scale
- Main: `accent-500` (#3b82f6)
- Hover: `accent-600` (#2563eb)

### Components

All UI components follow:
- Clean, modern design
- Smooth transitions (200-300ms)
- Consistent spacing (4px/8px grid)
- Subtle shadows for depth
- Responsive and accessible

## State Management

Using Zustand for lightweight state management:

```typescript
import { useAuthStore } from '@/store/authStore'

// In component
const { user, isAuthenticated, logout } = useAuthStore()
```

## API Integration

Using Axios with automatic token injection:

```typescript
import api from '@/lib/api'

// API calls automatically include auth token
const response = await api.get('/agents')
const data = await api.post('/chat', { message: 'Hello' })
```

## Contributing

1. Follow the TypeScript strict mode
2. Use Tailwind CSS for styling (no inline styles)
3. Create reusable components
4. Write type-safe code
5. Test on multiple screen sizes

## License

Open source - see LICENSE file
