# MCP Protocol Research

## Overview
The Model Context Protocol (MCP) is an open standard that enables seamless integration between LLM applications and external data sources and tools. It follows a client-host-server architecture where each host can run multiple client instances.

## Core Components

### Architecture
- **Host**: Acts as the container and coordinator, creates and manages multiple client instances
- **Client**: Connectors within the host application that maintain 1:1 connections with servers
- **Server**: Services that provide context and capabilities
- **Local Data Sources**: Computer's files, databases, and services that MCP servers can securely access
- **Remote Services**: External systems available over the internet that MCP servers can connect to

### Communication
- Uses JSON-RPC 2.0 messages to establish communication between hosts, clients, and servers
- Provides stateful connections
- Includes server and client capability negotiation

## Server Features
Servers provide the fundamental building blocks for adding context to language models via MCP:

1. **Prompts**: Pre-defined templates or instructions that guide language model interactions
   - User-controlled
   - Interactive templates invoked by user choice
   - Examples: Slash commands, menu options

2. **Resources**: Structured data or content that provides additional context to the model
   - Application-controlled
   - Contextual data attached and managed by the client
   - Examples: File contents, git history

3. **Tools**: Executable functions that allow models to perform actions or retrieve information
   - Model-controlled
   - Functions exposed to the LLM to take actions
   - Examples: API POST requests, file writing

## Client Features
Clients can implement additional features to enrich connected MCP servers:

1. **Roots**: (Not fully explored in research)

2. **Sampling**: Allows servers to request LLM sampling ("completions" or "generations") from language models via clients
   - Enables agentic behaviors by allowing LLM calls to occur nested inside other MCP server features
   - Clients maintain control over model access, selection, and permissions
   - Servers can request text or image-based interactions
   - For trust & safety, there should always be a human in the loop with the ability to deny sampling requests

## Security and Trust Considerations
- Users must explicitly consent to and understand all data access and operations
- Users must retain control over what data is shared and what actions are taken
- Hosts must obtain explicit user consent before exposing user data to servers
- Tools represent arbitrary code execution and must be treated with appropriate caution
- Users must explicitly approve any LLM sampling requests

## Testing Environment Implications
Based on this research, a comprehensive MCP testing environment would need to simulate:

1. The client-host-server architecture
2. JSON-RPC communication between components
3. Server features (prompts, resources, tools)
4. Client features (sampling)
5. Multiple logging sources (MCP server, Docker containers, web UI)
6. Security and consent mechanisms

This information will guide our investigation into available MCP client options and the design of our testing architecture.
