#!/usr/bin/env python3

import json
import argparse
import sys
import os
from pathlib import Path

# Simple MCP server for testing
class SimpleMCPServer:
    """
    A simple MCP server for testing the MCP Testing Environment.
    
    This server implements a basic subset of the Model Context Protocol
    for testing purposes. It supports:
    - Capability negotiation
    - Resource listing and retrieval
    - Prompt listing and execution
    - Tool listing and execution
    """
    
    def __init__(self):
        """Initialize the Simple MCP Server."""
        self.request_id = 0
        self.running = True
        
        # Define server capabilities
        self.capabilities = {
            "resources": {
                "list": {},
                "get": {}
            },
            "prompts": {
                "list": {},
                "execute": {}
            },
            "tools": {
                "list": {},
                "execute": {}
            }
        }
        
        # Define resources
        self.resources = {
            "sample_text": {
                "type": "text/plain",
                "content": "This is a sample text resource."
            },
            "sample_image": {
                "type": "image/png",
                "content": "base64encodedimagedatawouldgohere"
            }
        }
        
        # Define prompts
        self.prompts = {
            "echo": {
                "description": "Echo the input text",
                "args": {
                    "text": {
                        "type": "string",
                        "description": "Text to echo"
                    }
                }
            },
            "reverse": {
                "description": "Reverse the input text",
                "args": {
                    "text": {
                        "type": "string",
                        "description": "Text to reverse"
                    }
                }
            }
        }
        
        # Define tools
        self.tools = {
            "add": {
                "description": "Add two numbers",
                "args": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                }
            },
            "multiply": {
                "description": "Multiply two numbers",
                "args": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                }
            }
        }
        
    def handle_request(self, request_str):
        """
        Handle a JSON-RPC request.
        
        Args:
            request_str: JSON-RPC request string
            
        Returns:
            JSON-RPC response string
        """
        try:
            request = json.loads(request_str)
            
            if "method" not in request:
                return self.create_error_response(request.get("id"), -32600, "Invalid Request")
                
            method = request["method"]
            params = request.get("params", {})
            
            # Handle methods
            if method == "initialize":
                return self.handle_initialize(request["id"], params)
            elif method == "shutdown":
                return self.handle_shutdown(request["id"], params)
            elif method == "resources/list":
                return self.handle_resources_list(request["id"], params)
            elif method == "resources/get":
                return self.handle_resources_get(request["id"], params)
            elif method == "prompts/list":
                return self.handle_prompts_list(request["id"], params)
            elif method == "prompts/execute":
                return self.handle_prompts_execute(request["id"], params)
            elif method == "tools/list":
                return self.handle_tools_list(request["id"], params)
            elif method == "tools/execute":
                return self.handle_tools_execute(request["id"], params)
            else:
                return self.create_error_response(request["id"], -32601, f"Method not found: {method}")
        except json.JSONDecodeError:
            return self.create_error_response(None, -32700, "Parse error")
        except Exception as e:
            return self.create_error_response(None, -32603, f"Internal error: {str(e)}")
            
    def handle_initialize(self, id, params):
        """
        Handle initialize request.
        
        Args:
            id: Request ID
            params: Request parameters
            
        Returns:
            JSON-RPC response
        """
        client_capabilities = params.get("capabilities", {})
        client_info = params.get("clientInfo", {})
        
        print(f"Client connected: {client_info.get('name', 'Unknown')} {client_info.get('version', 'Unknown')}")
        print(f"Client capabilities: {json.dumps(client_capabilities, indent=2)}")
        
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "capabilities": self.capabilities,
                "serverInfo": {
                    "name": "Simple MCP Server",
                    "version": "1.0.0"
                }
            }
        })
        
    def handle_shutdown(self, id, params):
        """
        Handle shutdown request.
        
        Args:
            id: Request ID
            params: Request parameters
            
        Returns:
            JSON-RPC response
        """
        self.running = False
        
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "result": {}
        })
        
    def handle_resources_list(self, id, params):
        """
        Handle resources/list request.
        
        Args:
            id: Request ID
            params: Request parameters
            
        Returns:
            JSON-RPC response
        """
        resources_list = []
        
        for uri, resource in self.resources.items():
            resources_list.append({
                "uri": uri,
                "type": resource["type"]
            })
            
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "resources": resources_list
            }
        })
        
    def handle_resources_get(self, id, params):
        """
        Handle resources/get request.
        
        Args:
            id: Request ID
            params: Request parameters
            
        Returns:
            JSON-RPC response
        """
        uri = params.get("uri")
        
        if not uri or uri not in self.resources:
            return self.create_error_response(id, -32602, f"Resource not found: {uri}")
            
        resource = self.resources[uri]
        
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "uri": uri,
                "type": resource["type"],
                "content": resource["content"]
            }
        })
        
    def handle_prompts_list(self, id, params):
        """
        Handle prompts/list request.
        
        Args:
            id: Request ID
            params: Request parameters
            
        Returns:
            JSON-RPC response
        """
        prompts_list = []
        
        for prompt_id, prompt in self.prompts.items():
            prompts_list.append({
                "id": prompt_id,
                "description": prompt["description"],
                "args": prompt["args"]
            })
            
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "prompts": prompts_list
            }
        })
        
    def handle_prompts_execute(self, id, params):
        """
        Handle prompts/execute request.
        
        Args:
            id: Request ID
            params: Request parameters
            
        Returns:
            JSON-RPC response
        """
        prompt_id = params.get("id")
        args = params.get("args", {})
        
        if not prompt_id or prompt_id not in self.prompts:
            return self.create_error_response(id, -32602, f"Prompt not found: {prompt_id}")
            
        prompt = self.prompts[prompt_id]
        
        # Validate args
        for arg_name, arg_spec in prompt["args"].items():
            if arg_name not in args:
                return self.create_error_response(id, -32602, f"Missing argument: {arg_name}")
                
        # Execute prompt
        if prompt_id == "echo":
            result = args["text"]
        elif prompt_id == "reverse":
            result = args["text"][::-1]
        else:
            result = "Unknown prompt"
            
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "result": result
            }
        })
        
    def handle_tools_list(self, id, params):
        """
        Handle tools/list request.
        
        Args:
            id: Request ID
            params: Request parameters
            
        Returns:
            JSON-RPC response
        """
        tools_list = []
        
        for tool_id, tool in self.tools.items():
            tools_list.append({
                "id": tool_id,
                "description": tool["description"],
                "args": tool["args"]
            })
            
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "tools": tools_list
            }
        })
        
    def handle_tools_execute(self, id, params):
        """
        Handle tools/execute request.
        
        Args:
            id: Request ID
            params: Request parameters
            
        Returns:
            JSON-RPC response
        """
        tool_id = params.get("id")
        args = params.get("args", {})
        
        if not tool_id or tool_id not in self.tools:
            return self.create_error_response(id, -32602, f"Tool not found: {tool_id}")
            
        tool = self.tools[tool_id]
        
        # Validate args
        for arg_name, arg_spec in tool["args"].items():
            if arg_name not in args:
                return self.create_error_response(id, -32602, f"Missing argument: {arg_name}")
                
        # Execute tool
        if tool_id == "add":
            result = args["a"] + args["b"]
        elif tool_id == "multiply":
            result = args["a"] * args["b"]
        else:
            result = "Unknown tool"
            
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "result": result
            }
        })
        
    def create_error_response(self, id, code, message):
        """
        Create a JSON-RPC error response.
        
        Args:
            id: Request ID
            code: Error code
            message: Error message
            
        Returns:
            JSON-RPC error response
        """
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "error": {
                "code": code,
                "message": message
            }
        })
        
    def run(self):
        """Run the server."""
        print("Simple MCP Server started")
        print("Waiting for requests...")
        
        while self.running:
            try:
                # Read a line from stdin
                request_str = input()
                
                # Handle the request
                response_str = self.handle_request(request_str)
                
                # Write the response to stdout
                print(response_str, flush=True)
            except EOFError:
                # End of input, exit
                break
            except Exception as e:
                # Handle unexpected errors
                error_response = self.create_error_response(None, -32603, f"Internal error: {str(e)}")
                print(error_response, flush=True)
                
        print("Simple MCP Server stopped")

def main():
    parser = argparse.ArgumentParser(description="Simple MCP Server for testing")
    args = parser.parse_args()
    
    server = SimpleMCPServer()
    server.run()

if __name__ == "__main__":
    main()
