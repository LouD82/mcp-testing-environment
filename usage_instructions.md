# MCP Testing Environment - Usage Instructions for Future Conversations

## Introduction

This document provides instructions on how to use the MCP Testing Environment in future conversations. The environment allows you to test MCP servers, particularly those with Discord integration, by providing tools for simulating MCP clients, managing Docker containers, aggregating logs, and testing web UIs.

## Setup Instructions

To set up the MCP Testing Environment in a future conversation:

1. Clone the repository from the current conversation:
   ```
   git clone https://github.com/yourusername/mcp-testing-environment.git
   cd mcp-testing-environment
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   playwright install
   ```

3. Start the MCP Testing Environment:
   ```
   python mcp_testing_environment.py
   ```

4. Access the web interface at http://localhost:8000

## Testing an MCP Server

To test an MCP server in a future conversation:

1. Start the MCP Testing Environment as described above.

2. Configure the MCP server:
   - Go to the web interface at http://localhost:8000
   - Navigate to the Configuration section
   - Add your MCP server configuration

3. Start all components:
   - Click "Start All Components" in the web interface
   - Alternatively, start individual components as needed

4. Use the MCP Client Simulator to interact with your MCP server:
   - Access the MCP Client Simulator at http://localhost:8079
   - Connect to your MCP server
   - Test resources, prompts, and tools

5. Monitor logs from all components:
   - Access the Log Aggregation System at http://localhost:8080
   - View logs from the MCP server, Docker containers, and web UIs

6. Manage Docker containers:
   - Access the Docker Container Management Interface at http://localhost:8081
   - Start, stop, and restart containers
   - View container logs

7. Test the web UI:
   - Access the Web UI Testing Component at http://localhost:8082
   - Navigate to your web UI
   - Interact with elements, take screenshots, and inspect network traffic

## Common Testing Scenarios

### Testing a Discord MCP Server

1. Configure the Discord MCP server:
   ```json
   {
     "mcp_server_config": {
       "discord_server": {
         "transport": "stdio",
         "command": "node discord_server.js",
         "working_dir": "/path/to/discord_server"
       }
     },
     "discord_config": {
       "api_key": "your-discord-api-key",
       "channel_id": "your-channel-id"
     }
   }
   ```

2. Configure Docker containers for Discord integration:
   ```json
   {
     "docker_compose_files": {
       "discord_integration": "/path/to/docker-compose.yml"
     }
   }
   ```

3. Start the Docker containers:
   - Access the Docker Container Management Interface
   - Start the Discord integration containers

4. Start the MCP Client Simulator and connect to the Discord MCP server.

5. Test Discord-specific functionality:
   - Test channel data export/import
   - Test message sending/receiving
   - Test user interactions

6. Test the web UI for Discord integration:
   - Navigate to the web UI
   - Test channel visualization
   - Test user interactions

### Debugging Issues

1. Check logs from all components:
   - Access the Log Aggregation System
   - Filter logs by component or severity
   - Look for error messages

2. Verify container status:
   - Access the Docker Container Management Interface
   - Check container health and logs

3. Test MCP server connectivity:
   - Use the MCP Client Simulator to test basic connectivity
   - Verify capability negotiation

4. Check web UI functionality:
   - Use the Web UI Testing Component to inspect elements
   - Take screenshots for documentation
   - Test user interactions

## Extending the Environment

To extend the MCP Testing Environment in a future conversation:

1. Add new components:
   - Create a new Python file for your component
   - Implement the component's functionality
   - Add an API for interacting with the component
   - Update the Integration Framework to include your component

2. Customize existing components:
   - Modify the Python file for the component
   - Update the API as needed
   - Update the configuration structure if necessary

3. Add support for new MCP server types:
   - Update the MCP Client Simulator to support new features
   - Add configuration options for the new server type
   - Test with sample servers

## Troubleshooting

If you encounter issues in a future conversation:

1. Check component status:
   - Verify that all components are running
   - Check port availability

2. Review logs:
   - Check logs for each component
   - Look for error messages or warnings

3. Verify configuration:
   - Ensure all configuration settings are correct
   - Check paths and URLs

4. Restart components:
   - Stop and restart individual components
   - If necessary, restart the entire environment

## Quick Reference

- MCP Testing Environment: http://localhost:8000
- MCP Client Simulator: http://localhost:8079
- Log Aggregation System: http://localhost:8080
- Docker Container Management: http://localhost:8081
- Web UI Testing Component: http://localhost:8082

## Conclusion

By following these instructions, you can use the MCP Testing Environment in future conversations to efficiently test and debug MCP servers, particularly those with Discord integration. The environment provides a comprehensive set of tools for simulating clients, managing containers, aggregating logs, and testing web UIs, all integrated into a unified interface.
