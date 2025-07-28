# Security Gate Dashboard

A modern, responsive web dashboard for the Security Gate visitor screening system. Built with React, TypeScript, and Vite.

## Features

### 🔒 Visitor Screening
- Session-based visitor screening workflow
- Real-time security agent chat interface
- Visitor profile building and display
- Decision tracking with confidence scores

### 💬 Interactive Chat
- Direct communication with security screening agent
- Message history with timestamps
- Session completion tracking
- Character count and input validation

### 👤 Profile Management
- Visitor information display
- Threat level assessment
- ID verification status
- Contact person tracking

### 📊 Session Monitoring
- Active session tracking
- System health monitoring
- Session completion status
- Real-time updates

### ⚙️ Configurable Settings
- API endpoint configuration
- Auto-refresh intervals
- Display preferences
- Notification settings

### 🎨 Modern UI
- Clean, responsive design
- Dark/light mode support
- Mobile-friendly interface
- Loading states and error handling

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Security Gate backend running (default: `http://localhost:8001`)

### Installation

1. **Clone or navigate to the dashboard directory**
   ```bash
   cd dashboard
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env with your API endpoint
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to `http://localhost:5173`

## Configuration

### Environment Variables

Create a `.env` file in the dashboard directory:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8001

# UI Settings
VITE_REFRESH_INTERVAL=5000
VITE_MESSAGE_MAX_LENGTH=500

# Optional
VITE_DEBUG=false
VITE_APP_TITLE="Security Gate Dashboard"
```

### API Endpoints

Your Security Gate backend should implement these endpoints:

- `POST /start-session` - Start a new visitor screening session
- `POST /chat/{session_id}` - Send message to security agent
- `GET /profile/{session_id}` - Get visitor profile and session status
- `POST /end-session/{session_id}` - End a screening session
- `GET /health` - System health and active sessions

### Expected API Response Format

```typescript
// POST /start-session
{
  "session_id": "uuid-string",
  "status": "success",
  "message": "Session started successfully"
}

// POST /chat/{session_id}
{
  "agent_response": "Welcome! Can you tell me your name and who you're here to see?",
  "session_complete": false
}

// GET /profile/{session_id}
{
  "visitor_profile": {
    "name": "John Doe",
    "purpose": "meeting",
    "contact_person": "Alice Smith",
    "threat_level": "low",
    "affiliation": "Company ABC",
    "id_verified": true
  },
  "decision": "approved",
  "decision_confidence": 0.9,
  "session_active": true
}

// GET /health
{
  "status": "healthy",
  "graph_initialized": true,
  "active_sessions": 2
}
```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Project Structure

```
dashboard/
├── public/                 # Static assets
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── Button/       # Button component
│   │   └── Input/        # Input component
│   ├── hooks/            # Custom React hooks
│   │   └── useApi.ts     # API management hook
│   ├── pages/            # Page components
│   │   ├── Dashboard/    # Main dashboard page
│   │   └── Settings/     # Settings page
│   ├── services/         # API client and services
│   │   └── apiClient.ts  # HTTP client for backend
│   ├── utils/            # Utility functions and constants
│   │   └── constants.ts  # App constants
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # App entry point
│   └── routes.tsx        # Routing configuration
├── .env.example          # Environment variables template
├── package.json          # Dependencies and scripts
└── README.md            # This file
```

### Key Components

**Dashboard** (`/src/pages/Dashboard/Dashboard.tsx`)
- Main interface with session management and chat
- Session status and visitor profile display
- Auto-refreshes data every 5 seconds
- Handles session lifecycle and messaging

**Settings** (`/src/pages/Settings/Settings.tsx`)
- Configuration interface
- API endpoint management
- Display preferences
- System health monitoring

**useApi Hook** (`/src/hooks/useApi.ts`)
- Centralized API state management
- Session lifecycle management
- Automatic error handling
- Loading states for all operations

### Styling

The project uses CSS Modules with custom properties for theming:

- Responsive design with mobile-first approach
- Dark/light mode support through CSS media queries
- Consistent spacing and typography
- Custom component styles in separate `.module.css` files

## Deployment

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Docker Deployment

Create a `Dockerfile` in the dashboard directory:

```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:

```bash
docker build -t security-gate-dashboard .
docker run -p 8080:80 security-gate-dashboard
```
