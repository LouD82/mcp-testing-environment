# MCP Testing Environment Documentation

## Overview

The MCP Testing Environment is a comprehensive solution for testing MCP (Model Context Protocol) servers, with a particular focus on Discord integration. It provides tools for simulating MCP clients, managing Docker containers, aggregating logs from multiple sources, and testing web UIs.

This documentation covers the architecture, components, installation, configuration, and usage of the MCP Testing Environment.

## Architecture

The MCP Testing Environment consists of the following components:

1. **MCP Client Simulator**: Simulates MCP client behavior to test MCP servers without requiring an actual MCP client like Claude Code.
2. **Log Aggregation System**: Collects, displays, and analyzes logs from multiple sources in a unified interface.
3. **Docker Container Management Interface**: Simplifies the management of Docker containers used for Discord integration.
4. **Web UI Testing Component**: Provides tools for testing and debugging web interfaces associated with MCP servers.
5. **Integration Framework**: Ties all components together into a cohesive testing environment with a unified web interface.

The components communicate with each other through HTTP APIs and share configuration through a common configuration system.

## Installation

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Node.js 14 or higher (for some MCP servers)
- Playwright (for web UI testing)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mcp-testing-environment.git
   cd mcp-testing-environment
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install
   ```

4. Install Docker and Docker Compose if not already installed:
   ```bash
   # For Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install docker.io docker-compose
   ```

5. Start the MCP Testing Environment:
   ```bash
   python mcp_testing_environment.py
   ```

## Components

### MCP Client Simulator

The MCP Client Simulator implements the client side of the Model Context Protocol, allowing testing of MCP servers without requiring an actual MCP client.

#### Features:
- Support for JSON-RPC over stdio or HTTP/SSE
- Capability negotiation with MCP servers
- Resource listing and retrieval
- Prompt listing and execution
- Tool listing and execution
- Interactive mode for manual testing

#### Usage:
```bash
python mcp_client_simulator.py --transport stdio --interactive
```

### Log Aggregation System

The Log Aggregation System collects and displays logs from multiple sources in a unified interface.

#### Features:
- Collect logs from MCP servers
- Collect logs from Docker containers
- Collect logs from web UIs
- Provide filtering and search capabilities
- Support real-time log viewing
- Enable log persistence for later analysis

#### Usage:
```bash
python log_aggregator.py --port 8080
```

### Docker Container Management Interface

The Docker Container Management Interface simplifies the management of Docker containers used for Discord integration.

#### Features:
- Start, stop, and restart containers
- View container status and health
- Access container logs
- Configure container settings
- Support for Docker Compose for multi-container setups

#### Usage:
```bash
python docker_manager.py --port 8081
```

### Web UI Testing Component

The Web UI Testing Component provides tools for testing and debugging web interfaces associated with MCP servers.

#### Features:
- View web UI elements
- Interact with web UI
- Capture screenshots
- Inspect network traffic
- Test responsive behavior

#### Usage:
```bash
python webui_tester.py --port 8082
```

### Integration Framework

The Integration Framework ties all components together into a cohesive testing environment with a unified web interface.

#### Features:
- Start and stop individual components
- Configure all components from a central location
- View logs from all components
- Manage MCP server configurations
- Manage Discord integration configurations

#### Usage:
```bash
python mcp_testing_environment.py --port 8000
```

## Configuration

The MCP Testing Environment uses a JSON configuration file to store settings for all components. The default configuration file is located at `~/.mcp_testing/mcp_testing_environment.json`.

### Configuration Structure

```json
{
  "components": {
    "mcp_client": {"port": 8079},
    "log_aggregator": {"port": 8080},
    "docker_manager": {"port": 8081},
    "webui_tester": {"port": 8082}
  },
  "mcp_server_config": {},
  "discord_config": {},
  "docker_compose_files": {},
  "web_ui_urls": {}
}
```

### MCP Server Configuration

The `mcp_server_config` section contains configuration for MCP servers:

```json
{
  "mcp_server_config": {
    "server_name": {
      "transport": "stdio",
      "command": "node server.js",
      "working_dir": "/path/to/server"
    }
  }
}
```

### Discord Configuration

The `discord_config` section contains configuration for Discord integration:

```json
{
  "discord_config": {
    "api_key": "your-discord-api-key",
    "channel_id": "your-channel-id"
  }
}
```

### Docker Compose Configuration

The `docker_compose_files` section contains paths to Docker Compose files:

```json
{
  "docker_compose_files": {
    "discord_integration": "/path/to/docker-compose.yml"
  }
}
```

### Web UI Configuration

The `web_ui_urls` section contains URLs for web UIs:

```json
{
  "web_ui_urls": {
    "discord_ui": "http://localhost:3000"
  }
}
```

## Usage

### Starting the Environment

1. Start the MCP Testing Environment:
   ```bash
   python mcp_testing_environment.py
   ```

2. Open the web interface in your browser:
   ```
   http://localhost:8000
   ```

3. Start all components from the web interface, or start individual components as needed.

### Testing an MCP Server

1. Configure the MCP server in the web interface.
2. Start the Log Aggregation System to collect logs.
3. Start the Docker Container Management Interface if using Docker containers.
4. Start the Web UI Testing Component if testing a web UI.
5. Start the MCP Client Simulator.
6. Use the MCP Client Simulator to interact with the MCP server.
7. View logs from all components in the Log Aggregation System.
8. Test the web UI using the Web UI Testing Component.

### Troubleshooting

If you encounter issues:

1. Check the logs for each component in the Log Aggregation System.
2. Verify that all components are running and accessible.
3. Check the configuration for each component.
4. Restart components if necessary.

## API Reference

### MCP Testing Environment API

- `GET /api/status`: Get status of all components
- `POST /api/components/start`: Start a component
- `POST /api/components/stop`: Stop a component
- `POST /api/components/start_all`: Start all components
- `POST /api/components/stop_all`: Stop all components
- `GET /api/config`: Get configuration
- `POST /api/config`: Update configuration
- `GET /api/logs`: Get logs

### MCP Client Simulator API

- `GET /api/status`: Get client status
- `POST /api/connect`: Connect to an MCP server
- `POST /api/disconnect`: Disconnect from an MCP server
- `GET /api/resources`: List resources
- `GET /api/resources/{uri}`: Get a resource
- `GET /api/prompts`: List prompts
- `POST /api/prompts/{id}/execute`: Execute a prompt
- `GET /api/tools`: List tools
- `POST /api/tools/{id}/execute`: Execute a tool

### Log Aggregation System API

- `GET /api/logs`: Get logs
- `GET /api/sources`: Get log sources
- `POST /api/sources`: Add a log source
- `DELETE /api/sources/{name}`: Remove a log source
- `POST /api/logs`: Add a log entry

### Docker Container Management API

- `GET /api/containers`: Get all containers
- `GET /api/containers/{id}`: Get a container
- `POST /api/containers/{id}/start`: Start a container
- `POST /api/containers/{id}/stop`: Stop a container
- `POST /api/containers/{id}/restart`: Restart a container
- `GET /api/containers/{id}/logs`: Get container logs
- `GET /api/compose`: Get all compose projects
- `GET /api/compose/{name}`: Get a compose project
- `POST /api/compose/{name}/up`: Start a compose project
- `POST /api/compose/{name}/down`: Stop a compose project
- `POST /api/compose/{name}/restart`: Restart a compose project

### Web UI Testing API

- `GET /api/status`: Get browser status
- `POST /api/browser/launch`: Launch browser
- `POST /api/browser/close`: Close browser
- `POST /api/browser/navigate`: Navigate to URL
- `GET /api/browser/screenshot`: Take screenshot
- `GET /api/browser/content`: Get page content
- `GET /api/browser/elements`: Get page elements
- `POST /api/browser/click`: Click element
- `POST /api/browser/type`: Type text
- `POST /api/browser/select`: Select option
- `GET /api/browser/network`: Get network info

## Extending the Environment

The MCP Testing Environment is designed to be extensible. You can add new components or modify existing ones to suit your specific needs.

### Adding a New Component

1. Create a new Python file for your component.
2. Implement the component's functionality.
3. Add an API for interacting with the component.
4. Update the Integration Framework to include your component.
5. Update the configuration structure to include settings for your component.

### Customizing Existing Components

1. Modify the Python file for the component you want to customize.
2. Update the API as needed.
3. Update the configuration structure if necessary.
4. Test your changes to ensure they work as expected.

## Conclusion

The MCP Testing Environment provides a comprehensive solution for testing MCP servers, with a particular focus on Discord integration. By using this environment, you can efficiently test and debug MCP servers without the need for complex manual setup and configuration.
