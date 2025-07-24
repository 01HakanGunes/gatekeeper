# AI Agent Dashboard

A modern, responsive web dashboard for monitoring and interacting with AI agents. Built with React, TypeScript, and Vite.

## Features

### 🤖 Agent Monitoring
- Real-time agent status monitoring
- System logs with different log levels (info, warning, error, debug)
- Connection status and uptime tracking
- Agent version and active connections display

### 💬 Interactive Chat
- Direct communication with your AI agent
- Message history with timestamps
- Real-time message status (sent, delivered, error)
- Character count and input validation

### ⚙️ Configurable Settings
- API endpoint configuration
- Auto-refresh intervals
- Display preferences
- Debug log toggles
- Notification settings

### 🎨 Modern UI
- Clean, responsive design
- Dark/light mode support
- Mobile-friendly interface
- Loading states and error handling

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Your AI agent backend running (default: `http://localhost:8000`)

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
VITE_API_BASE_URL=http://localhost:8000

# UI Settings
VITE_REFRESH_INTERVAL=5000
VITE_MAX_LOG_ENTRIES=1000
VITE_MESSAGE_MAX_LENGTH=500

# Optional
VITE_DEBUG=false
VITE_APP_TITLE="AI Agent Dashboard"
```

### API Endpoints

Your AI agent backend should implement these endpoints:

- `GET /api/status` - Agent status information
- `GET /api/logs?limit=100` - System logs
- `GET /api/messages?limit=50` - Message history
- `POST /api/send-message` - Send message to agent
- `DELETE /api/logs` - Clear logs

### Expected API Response Format

```typescript
// GET /api/status
{
  "data": {
    "online": true,
    "lastSeen": "2024-01-15T10:30:00Z",
    "activeConnections": 3,
    "uptime": 7200,
    "version": "1.0.0"
  },
  "success": true
}

// GET /api/logs
{
  "data": [
    {
      "id": "log-1",
      "timestamp": "2024-01-15T10:30:00Z",
      "level": "info",
      "message": "Agent started successfully",
      "source": "agent-core",
      "metadata": {}
    }
  ],
  "success": true
}

// GET /api/messages
{
  "data": [
    {
      "id": "msg-1",
      "content": "Hello, how can I help you?",
      "timestamp": "2024-01-15T10:30:00Z",
      "sender": "agent",
      "status": "delivered"
    }
  ],
  "success": true
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
- Main interface with logs sidebar and chat area
- Auto-refreshes data every 5 seconds
- Handles message sending and log viewing

**Settings** (`/src/pages/Settings/Settings.tsx`)
- Configuration interface
- API endpoint management
- Display preferences
- Cache management

**useApi Hook** (`/src/hooks/useApi.ts`)
- Centralized API state management
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
docker build -t ai-agent-dashboard .
docker run -p 8080:80 ai-agent-dashboard
```
