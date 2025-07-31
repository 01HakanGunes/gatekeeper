# Security Gate System

## 🚀 Quick Start

### Installation

```bash
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

### Running the Application

```bash
# Run
python main.py
```

### Docker Compose Setup

Build and run the container:

```bash
docker build -t gatekeeper-main:latest .
```

```bash
sudo docker-compose up --build -d
```

Interact with the active session:

```bash
docker attach gatekeeper-main
```
