#!/usr/bin/env python3

import asyncio
import json
import logging
import argparse
import sys
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_client_simulator.log')
    ]
)
logger = logging.getLogger('mcp_client_simulator')

class MCPClientSimulator:
    """
    MCP Client Simulator for testing MCP servers.
    
    This simulator implements the client side of the Model Context Protocol,
    allowing testing of MCP servers without requiring an actual MCP client.
    """
    
    def __init__(self, server_url: str = None, transport: str = "stdio"):
        """
        Initialize the MCP Client Simulator.
        
        Args:
            server_url: URL of the MCP server (for HTTP/SSE transport)
            transport: Transport method ("stdio" or "http")
        """
        self.server_url = server_url
        self.transport = transport
        self.request_id = 0
        self.capabilities = {
            "resources": {},
            "prompts": {},
            "tools": {},
            "sampling": {}
        }
        self.connected = False
        logger.info(f"Initialized MCP Client Simulator with transport: {transport}")
        
    async def connect(self):
        """Establish connection to the MCP server."""
        if self.transport == "stdio":
            logger.info("Using stdio transport")
            # For stdio, we'll read from stdin and write to stdout
            self.reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self.reader)
            await asyncio.get_event_loop().connect_read_pipe(
                lambda: protocol, sys.stdin)
            
            w_transport, w_protocol = await asyncio.get_event_loop().connect_write_pipe(
                asyncio.streams.FlowControlMixin, sys.stdout)
            self.writer = asyncio.StreamWriter(w_transport, w_protocol, None, asyncio.get_event_loop())
        else:
            # HTTP/SSE transport would be implemented here
            logger.info(f"Using HTTP transport with server URL: {self.server_url}")
            # This would require implementing HTTP client with SSE support
            raise NotImplementedError("HTTP/SSE transport not yet implemented")
        
        # Send initialize request
        await self.initialize()
        
    async def initialize(self):
        """Send initialize request to the server."""
        initialize_request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "initialize",
            "params": {
                "capabilities": self.capabilities,
                "clientInfo": {
                    "name": "MCP Client Simulator",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self.send_request(initialize_request)
        if response and "result" in response:
            self.server_capabilities = response["result"]["capabilities"]
            self.connected = True
            logger.info(f"Connected to MCP server with capabilities: {self.server_capabilities}")
            return True
        return False
    
    def next_id(self) -> int:
        """Generate the next request ID."""
        self.request_id += 1
        return self.request_id
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request to the MCP server and wait for response.
        
        Args:
            request: The JSON-RPC request to send
            
        Returns:
            The JSON-RPC response from the server
        """
        request_str = json.dumps(request) + "\n"
        logger.debug(f"Sending request: {request_str}")
        
        if self.transport == "stdio":
            self.writer.write(request_str.encode())
            await self.writer.drain()
            
            response_line = await self.reader.readline()
            if not response_line:
                logger.error("No response received from server")
                return None
                
            try:
                response = json.loads(response_line.decode())
                logger.debug(f"Received response: {response}")
                return response
            except json.JSONDecodeError:
                logger.error(f"Failed to parse response: {response_line}")
                return None
        else:
            # HTTP/SSE implementation would go here
            raise NotImplementedError("HTTP/SSE transport not yet implemented")
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the server."""
        if not self.connected:
            logger.error("Not connected to server")
            return []
            
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "resources/list",
            "params": {}
        }
        
        response = await self.send_request(request)
        if response and "result" in response:
            resources = response["result"]["resources"]
            logger.info(f"Retrieved {len(resources)} resources")
            return resources
        return []
    
    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """
        Get a specific resource from the server.
        
        Args:
            uri: URI of the resource to retrieve
            
        Returns:
            The resource content
        """
        if not self.connected:
            logger.error("Not connected to server")
            return None
            
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "resources/get",
            "params": {
                "uri": uri
            }
        }
        
        response = await self.send_request(request)
        if response and "result" in response:
            resource = response["result"]
            logger.info(f"Retrieved resource: {uri}")
            return resource
        return None
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List available prompts from the server."""
        if not self.connected:
            logger.error("Not connected to server")
            return []
            
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "prompts/list",
            "params": {}
        }
        
        response = await self.send_request(request)
        if response and "result" in response:
            prompts = response["result"]["prompts"]
            logger.info(f"Retrieved {len(prompts)} prompts")
            return prompts
        return []
    
    async def execute_prompt(self, id: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a prompt on the server.
        
        Args:
            id: ID of the prompt to execute
            args: Arguments for the prompt
            
        Returns:
            The prompt execution result
        """
        if not self.connected:
            logger.error("Not connected to server")
            return None
            
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "prompts/execute",
            "params": {
                "id": id,
                "args": args or {}
            }
        }
        
        response = await self.send_request(request)
        if response and "result" in response:
            result = response["result"]
            logger.info(f"Executed prompt: {id}")
            return result
        return None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the server."""
        if not self.connected:
            logger.error("Not connected to server")
            return []
            
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "tools/list",
            "params": {}
        }
        
        response = await self.send_request(request)
        if response and "result" in response:
            tools = response["result"]["tools"]
            logger.info(f"Retrieved {len(tools)} tools")
            return tools
        return []
    
    async def execute_tool(self, id: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a tool on the server.
        
        Args:
            id: ID of the tool to execute
            args: Arguments for the tool
            
        Returns:
            The tool execution result
        """
        if not self.connected:
            logger.error("Not connected to server")
            return None
            
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "tools/execute",
            "params": {
                "id": id,
                "args": args or {}
            }
        }
        
        response = await self.send_request(request)
        if response and "result" in response:
            result = response["result"]
            logger.info(f"Executed tool: {id}")
            return result
        return None
    
    async def shutdown(self):
        """Send shutdown request to the server."""
        if not self.connected:
            return
            
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "shutdown",
            "params": {}
        }
        
        await self.send_request(request)
        logger.info("Sent shutdown request to server")
        self.connected = False

async def interactive_session(client: MCPClientSimulator):
    """
    Run an interactive session with the MCP server.
    
    Args:
        client: The MCP client simulator instance
    """
    print("MCP Client Simulator Interactive Mode")
    print("=====================================")
    print("Available commands:")
    print("  list resources - List available resources")
    print("  get resource <uri> - Get a specific resource")
    print("  list prompts - List available prompts")
    print("  execute prompt <id> [args] - Execute a prompt")
    print("  list tools - List available tools")
    print("  execute tool <id> [args] - Execute a tool")
    print("  exit - Exit the interactive session")
    print()
    
    while True:
        try:
            command = input("> ").strip()
            if command == "exit":
                break
                
            parts = command.split()
            if len(parts) < 2:
                print("Invalid command")
                continue
                
            if parts[0] == "list" and parts[1] == "resources":
                resources = await client.list_resources()
                print(json.dumps(resources, indent=2))
            elif parts[0] == "get" and parts[1] == "resource" and len(parts) > 2:
                uri = parts[2]
                resource = await client.get_resource(uri)
                print(json.dumps(resource, indent=2))
            elif parts[0] == "list" and parts[1] == "prompts":
                prompts = await client.list_prompts()
                print(json.dumps(prompts, indent=2))
            elif parts[0] == "execute" and parts[1] == "prompt" and len(parts) > 2:
                id = parts[2]
                args = {}
                if len(parts) > 3:
                    try:
                        args = json.loads(" ".join(parts[3:]))
                    except json.JSONDecodeError:
                        print("Invalid JSON for args")
                        continue
                result = await client.execute_prompt(id, args)
                print(json.dumps(result, indent=2))
            elif parts[0] == "list" and parts[1] == "tools":
                tools = await client.list_tools()
                print(json.dumps(tools, indent=2))
            elif parts[0] == "execute" and parts[1] == "tool" and len(parts) > 2:
                id = parts[2]
                args = {}
                if len(parts) > 3:
                    try:
                        args = json.loads(" ".join(parts[3:]))
                    except json.JSONDecodeError:
                        print("Invalid JSON for args")
                        continue
                result = await client.execute_tool(id, args)
                print(json.dumps(result, indent=2))
            else:
                print("Unknown command")
        except Exception as e:
            print(f"Error: {e}")

async def main():
    parser = argparse.ArgumentParser(description="MCP Client Simulator")
    parser.add_argument("--server", help="Server URL (for HTTP transport)")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio",
                      help="Transport method (stdio or http)")
    parser.add_argument("--interactive", action="store_true",
                      help="Run in interactive mode")
    args = parser.parse_args()
    
    client = MCPClientSimulator(server_url=args.server, transport=args.transport)
    
    try:
        await client.connect()
        
        if args.interactive:
            await interactive_session(client)
        else:
            # In non-interactive mode, just list the available resources, prompts, and tools
            resources = await client.list_resources()
            print("Resources:")
            print(json.dumps(resources, indent=2))
            
            prompts = await client.list_prompts()
            print("\nPrompts:")
            print(json.dumps(prompts, indent=2))
            
            tools = await client.list_tools()
            print("\nTools:")
            print(json.dumps(tools, indent=2))
    finally:
        await client.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
