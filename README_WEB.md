# Architecture AI Design System - Web Interface

This document provides instructions for setting up and running the web interface for the Architecture AI Design System.

## Overview

The web interface provides a user-friendly way to interact with the Architecture AI Design System, offering:

- Intuitive chat-based interaction
- Visualization of room layouts and constraints
- Stage progression tracking
- Ability to save and resume sessions
- Real-time display of system state

## Prerequisites

- Python 3.7+
- All the dependencies for the main system (see main README.md)
- Flask web framework

## Installation

1. Make sure you have all the required dependencies installed:

```bash
pip install -r requirements.txt
pip install flask  # Add Flask if not included in requirements.txt
```

2. Ensure your directory structure matches the following:

```
project_root/
├── app.py                  # Flask application
├── main.py                 # Your existing main.py file
├── templates/              # HTML templates
│   └── index.html          
├── static/                 # Static files for the web application
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── main.js
├── models/                 # Your existing model files
├── utils/                  # Your existing utility files
├── sessions/               # Session data directory
```

## Running the Web Interface

1. Start the Flask application:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://localhost:5000
```

## Using the Web Interface

### Starting a New Session

1. Click the "New Session" button in the top right.
2. The system will initialize and display the first stage: "Requirement Gathering".
3. Type your building project requirements in the input field and press "Send".

### Resuming a Session

1. Click the "Resume Session" button in the top right.
2. Enter the path to the session you want to resume (e.g., `sessions/20240410_123456`).
3. Click "Resume" to continue where you left off.

### Interacting with the System

- Type messages in the input field and click "Send" (or press Enter) to communicate with the system.
- The progress bar at the top shows your current stage in the design process.
- Use the "Skip Stage" button to advance to the next stage when available.
- Visualizations appear on the right side of the screen as they become available.
- The system state (including your requirements, spatial understanding, and key questions) is displayed in expandable panels at the bottom.

### Visualization Tabs

- **Room Graph**: Shows the room layout and connections.
- **Constraints**: Displays the constraints table.
- **Layout**: Shows the final layout solution when available.

## Troubleshooting

- If visualizations don't appear, check the "sessions" directory to ensure image files are being created.
- If the application fails to start, check that all dependencies are installed and that no other application is using port 5000.
- For error messages in the chat, check the terminal running the Flask application for more detailed error logs.

## Technical Notes

- The web interface uses Flask as the backend web framework.
- Frontend uses Bootstrap 5 for styling and layout.
- Communication between frontend and backend happens via JSON APIs.
- Visualizations (PNG images) are stored in the session directory and served statically.
- The system state is polled periodically to keep the UI in sync.