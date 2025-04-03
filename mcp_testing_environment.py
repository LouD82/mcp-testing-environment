#!/usr/bin/env python3

import asyncio
import json
import logging
import argparse
import sys
import os
import time
import re
import subprocess
import shutil
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import aiohttp
from aiohttp import web
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_testing_environment.log')
    ]
)
logger = logging.getLogger('mcp_testing_environment')

class MCPTestingEnvironment:
    """
    MCP Testing Environment - Main Integration Framework
    
    Integrates all components of the MCP Testing Environment:
    - MCP Client Simulator
    - Log Aggregation System
    - Docker Container Management
    - Web UI Testing Component
    - Configuration Management
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the MCP Testing Environment.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.app = web.Application()
        self.setup_routes()
        
        # Component status
        self.components = {
            "mcp_client": {"running": False, "port": 8079, "process": None},
            "log_aggregator": {"running": False, "port": 8080, "process": None},
            "docker_manager": {"running": False, "port": 8081, "process": None},
            "webui_tester": {"running": False, "port": 8082, "process": None}
        }
        
        # Configuration
        self.config = {
            "mcp_server_config": {},
            "discord_config": {},
            "docker_compose_files": {},
            "web_ui_urls": {}
        }
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
            
    def setup_routes(self):
        """Set up web routes for the API"""
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/api/status', self.handle_get_status)
        self.app.router.add_post('/api/components/start', self.handle_start_component)
        self.app.router.add_post('/api/components/stop', self.handle_stop_component)
        self.app.router.add_post('/api/components/start_all', self.handle_start_all_components)
        self.app.router.add_post('/api/components/stop_all', self.handle_stop_all_components)
        self.app.router.add_get('/api/config', self.handle_get_config)
        self.app.router.add_post('/api/config', self.handle_update_config)
        self.app.router.add_post('/api/config/mcp_server', self.handle_update_mcp_server_config)
        self.app.router.add_post('/api/config/discord', self.handle_update_discord_config)
        self.app.router.add_post('/api/config/docker_compose', self.handle_update_docker_compose_config)
        self.app.router.add_post('/api/config/web_ui', self.handle_update_web_ui_config)
        self.app.router.add_get('/api/logs', self.handle_get_logs)
        
        # Static files
        self.app.router.add_static('/static/', path=str(Path(__file__).parent / 'static'), name='static')
        
    async def handle_index(self, request):
        """Handle GET /"""
        index_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MCP Testing Environment</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                h1 { color: #333; }
                .component { margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
                .running { background-color: #d4edda; }
                .stopped { background-color: #f8d7da; }
                button { padding: 5px 10px; margin-right: 5px; }
                .actions { margin-top: 10px; }
            </style>
        </head>
        <body>
            <h1>MCP Testing Environment</h1>
            <div id="components">
                <div class="component" id="mcp_client">
                    <h2>MCP Client Simulator</h2>
                    <p>Status: <span id="mcp_client_status">Checking...</span></p>
                    <div class="actions">
                        <button onclick="startComponent('mcp_client')">Start</button>
                        <button onclick="stopComponent('mcp_client')">Stop</button>
                    </div>
                </div>
                
                <div class="component" id="log_aggregator">
                    <h2>Log Aggregation System</h2>
                    <p>Status: <span id="log_aggregator_status">Checking...</span></p>
                    <div class="actions">
                        <button onclick="startComponent('log_aggregator')">Start</button>
                        <button onclick="stopComponent('log_aggregator')">Stop</button>
                        <button onclick="openComponent('log_aggregator')">Open UI</button>
                    </div>
                </div>
                
                <div class="component" id="docker_manager">
                    <h2>Docker Container Manager</h2>
                    <p>Status: <span id="docker_manager_status">Checking...</span></p>
                    <div class="actions">
                        <button onclick="startComponent('docker_manager')">Start</button>
                        <button onclick="stopComponent('docker_manager')">Stop</button>
                        <button onclick="openComponent('docker_manager')">Open UI</button>
                    </div>
                </div>
                
                <div class="component" id="webui_tester">
                    <h2>Web UI Testing Component</h2>
                    <p>Status: <span id="webui_tester_status">Checking...</span></p>
                    <div class="actions">
                        <button onclick="startComponent('webui_tester')">Start</button>
                        <button onclick="stopComponent('webui_tester')">Stop</button>
                        <button onclick="openComponent('webui_tester')">Open UI</button>
                    </div>
                </div>
            </div>
            
            <div class="actions">
                <button onclick="startAllComponents()">Start All Components</button>
                <button onclick="stopAllComponents()">Stop All Components</button>
            </div>
            
            <script>
                // Function to update status
                function updateStatus() {
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(data => {
                            for (const component in data.components) {
                                const status = data.components[component].running ? 'Running' : 'Stopped';
                                document.getElementById(component + '_status').textContent = status;
                                document.getElementById(component).className = 'component ' + (data.components[component].running ? 'running' : 'stopped');
                            }
                        });
                }
                
                // Function to start a component
                function startComponent(component) {
                    fetch('/api/components/start', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ component: component })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            updateStatus();
                        } else {
                            alert('Failed to start component: ' + data.error);
                        }
                    });
                }
                
                // Function to stop a component
                function stopComponent(component) {
                    fetch('/api/components/stop', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ component: component })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            updateStatus();
                        } else {
                            alert('Failed to stop component: ' + data.error);
                        }
                    });
                }
                
                // Function to start all components
                function startAllComponents() {
                    fetch('/api/components/start_all', {
                        method: 'POST'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            updateStatus();
                        } else {
                            alert('Failed to start all components: ' + data.error);
                        }
                    });
                }
                
                // Function to stop all components
                function stopAllComponents() {
                    fetch('/api/components/stop_all', {
                        method: 'POST'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            updateStatus();
                        } else {
                            alert('Failed to stop all components: ' + data.error);
                        }
                    });
                }
                
                // Function to open component UI
                function openComponent(component) {
                    let port;
                    switch (component) {
                        case 'log_aggregator':
                            port = 8080;
                            break;
                        case 'docker_manager':
                            port = 8081;
                            break;
                        case 'webui_tester':
                            port = 8082;
                            break;
                        default:
                            return;
                    }
                    window.open('http://localhost:' + port, '_blank');
                }
                
                // Update status on page load
                updateStatus();
                
                // Update status every 5 seconds
                setInterval(updateStatus, 5000);
            </script>
        </body>
        </html>
        """
        return web.Response(text=index_html, content_type='text/html')
        
    async def handle_get_status(self, request):
        """Handle GET /api/status"""
        # Check if components are actually running
        await self.check_component_status()
        
        return web.json_response({
            "components": self.components
        })
        
    async def handle_start_component(self, request):
        """Handle POST /api/components/start"""
        data = await request.json()
        component = data.get('component')
        
        if not component or component not in self.components:
            return web.json_response({"error": f"Invalid component: {component}"}, status=400)
            
        success = await self.start_component(component)
        
        if not success:
            return web.json_response({"error": f"Failed to start component: {component}"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_stop_component(self, request):
        """Handle POST /api/components/stop"""
        data = await request.json()
        component = data.get('component')
        
        if not component or component not in self.components:
            return web.json_response({"error": f"Invalid component: {component}"}, status=400)
            
        success = await self.stop_component(component)
        
        if not success:
            return web.json_response({"error": f"Failed to stop component: {component}"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_start_all_components(self, request):
        """Handle POST /api/components/start_all"""
        success = await self.start_all_components()
        
        if not success:
            return web.json_response({"error": "Failed to start all components"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_stop_all_components(self, request):
        """Handle POST /api/components/stop_all"""
        success = await self.stop_all_components()
        
        if not success:
            return web.json_response({"error": "Failed to stop all components"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_get_config(self, request):
        """Handle GET /api/config"""
        return web.json_response(self.config)
        
    async def handle_update_config(self, request):
        """Handle POST /api/config"""
        data = await request.json()
        
        # Update config with provided data
        for key, value in data.items():
            if key in self.config:
                self.config[key] = value
                
        self.save_config()
        
        return web.json_response({"success": True})
        
    async def handle_update_mcp_server_config(self, request):
        """Handle POST /api/config/mcp_server"""
        data = await request.json()
        self.config["mcp_server_config"] = data
        self.save_config()
        
        return web.json_response({"success": True})
        
    async def handle_update_discord_config(self, request):
        """Handle POST /api/config/discord"""
        data = await request.json()
        self.config["discord_config"] = data
        self.save_config()
        
        return web.json_response({"success": True})
        
    async def handle_update_docker_compose_config(self, request):
        """Handle POST /api/config/docker_compose"""
        data = await request.json()
        self.config["docker_compose_files"] = data
        self.save_config()
        
        return web.json_response({"success": True})
        
    async def handle_update_web_ui_config(self, request):
        """Handle POST /api/config/web_ui"""
        data = await request.json()
        self.config["web_ui_urls"] = data
        self.save_config()
        
        return web.json_response({"success": True})
        
    async def handle_get_logs(self, request):
        """Handle GET /api/logs"""
        component = request.query.get('component')
        limit = int(request.query.get('limit', 100))
        
        if component and component not in self.components:
            return web.json_response({"error": f"Invalid component: {component}"}, status=400)
            
        logs = await self.get_component_logs(component, limit)
        
        return web.json_response({"logs": logs})
        
    def load_config(self, config_path: str):
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Update config with loaded data
            for key, value in config.items():
                if key in self.config:
                    self.config[key] = value
                    
            # Update component ports if specified
            if "components" in config:
                for component, settings in config["components"].items():
                    if component in self.components and "port" in settings:
                        self.components[component]["port"] = settings["port"]
                
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            
    def save_config(self):
        """Save configuration to file."""
        if not self.config_path:
            logger.warning("No config path specified, cannot save configuration")
            return
            
        try:
            # Prepare config for saving
            save_config = dict(self.config)
            
            # Add component settings
            save_config["components"] = {}
            for component, settings in self.components.items():
                save_config["components"][component] = {
                    "port": settings["port"]
                }
                
            with open(self.config_path, 'w') as f:
                json.dump(save_config, f, indent=2)
                
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {self.config_path}: {e}")
            
    async def check_component_status(self):
        """Check if components are actually running."""
        for component, settings in self.components.items():
            if settings["process"] is not None:
                # Check if process is still running
                if settings["process"].poll() is not None:
                    # Process has terminated
                    settings["running"] = False
                    settings["process"] = None
                    logger.warning(f"Component {component} has terminated unexpectedly")
            
            # Double-check with port check
            if settings["running"]:
                port_in_use = await self.is_port_in_use(settings["port"])
                if not port_in_use:
                    settings["running"] = False
                    if settings["process"] is not None:
                        try:
                            settings["process"].terminate()
                        except:
                            pass
                        settings["process"] = None
                    logger.warning(f"Component {component} is not listening on port {settings['port']}")
            
    async def is_port_in_use(self, port: int) -> bool:
        """
        Check if a port is in use.
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is in use, False otherwise
        """
        try:
            # Try to connect to the port
            reader, writer = await asyncio.open_connection('localhost', port)
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
            
    async def start_component(self, component: str) -> bool:
        """
        Start a component.
        
        Args:
            component: Name of the component to start
            
        Returns:
            True if successful, False otherwise
        """
        if component not in self.components:
            logger.error(f"Invalid component: {component}")
            return False
            
        settings = self.components[component]
        
        if settings["running"]:
            logger.info(f"Component {component} is already running")
            return True
            
        # Check if port is already in use
        if await self.is_port_in_use(settings["port"]):
            logger.error(f"Port {settings['port']} is already in use")
            return False
            
        # Get component script path
        script_path = self.get_component_script_path(component)
        if not os.path.exists(script_path):
            logger.error(f"Component script not found: {script_path}")
            return False
            
        # Start the component
        try:
            # Create config directory if it doesn't exist
            config_dir = os.path.join(os.path.expanduser("~"), ".mcp_testing")
            os.makedirs(config_dir, exist_ok=True)
            
            # Prepare command
            cmd = [
                sys.executable,
                script_path,
                "--port", str(settings["port"]),
                "--config", os.path.join(config_dir, f"{component}.json")
            ]
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for the process to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if process.poll() is not None:
                # Process has terminated
                stdout, stderr = process.communicate()
                logger.error(f"Component {component} failed to start: {stderr}")
                return False
                
            # Check if port is now in use
            if not await self.is_port_in_use(settings["port"]):
                # Port is not in use, process might be starting slowly
                # Wait a bit more
                await asyncio.sleep(3)
                
                if not await self.is_port_in_use(settings["port"]):
                    # Still not in use, something is wrong
                    process.terminate()
                    logger.error(f"Component {component} is not listening on port {settings['port']}")
                    return False
                    
            # Update component status
            settings["running"] = True
            settings["process"] = process
            
            logger.info(f"Started component {component} on port {settings['port']}")
            return True
        except Exception as e:
            logger.error(f"Error starting component {component}: {e}")
            return False
            
    async def stop_component(self, component: str) -> bool:
        """
        Stop a component.
        
        Args:
            component: Name of the component to stop
            
        Returns:
            True if successful, False otherwise
        """
        if component not in self.components:
            logger.error(f"Invalid component: {component}")
            return False
            
        settings = self.components[component]
        
        if not settings["running"]:
            logger.info(f"Component {component} is not running")
            return True
            
        # Stop the component
        try:
            if settings["process"] is not None:
                settings["process"].terminate()
                
                # Wait for process to terminate
                try:
                    settings["process"].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    settings["process"].kill()
                    
                settings["process"] = None
                
            # Update component status
            settings["running"] = False
            
            logger.info(f"Stopped component {component}")
            return True
        except Exception as e:
            logger.error(f"Error stopping component {component}: {e}")
            return False
            
    async def start_all_components(self) -> bool:
        """
        Start all components.
        
        Returns:
            True if all components started successfully, False otherwise
        """
        all_success = True
        
        # Start components in order
        components_order = ["log_aggregator", "docker_manager", "webui_tester", "mcp_client"]
        
        for component in components_order:
            success = await self.start_component(component)
            if not success:
                all_success = False
                
        return all_success
        
    async def stop_all_components(self) -> bool:
        """
        Stop all components.
        
        Returns:
            True if all components stopped successfully, False otherwise
        """
        all_success = True
        
        # Stop components in reverse order
        components_order = ["mcp_client", "webui_tester", "docker_manager", "log_aggregator"]
        
        for component in components_order:
            success = await self.stop_component(component)
            if not success:
                all_success = False
                
        return all_success
        
    async def get_component_logs(self, component: str = None, limit: int = 100) -> List[str]:
        """
        Get logs for a component.
        
        Args:
            component: Name of the component to get logs for, or None for all components
            limit: Maximum number of log lines to return
            
        Returns:
            List of log lines
        """
        logs = []
        
        try:
            if component:
                # Get logs for specific component
                log_file = f"{component}.log"
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        logs = f.readlines()[-limit:]
            else:
                # Get logs for all components
                for comp in self.components:
                    log_file = f"{comp}.log"
                    if os.path.exists(log_file):
                        with open(log_file, 'r') as f:
                            comp_logs = f.readlines()[-limit:]
                            logs.extend([f"[{comp}] {line}" for line in comp_logs])
                            
                # Sort logs by timestamp if possible
                logs.sort()
                logs = logs[-limit:]
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            
        return logs
        
    def get_component_script_path(self, component: str) -> str:
        """
        Get the path to a component's script.
        
        Args:
            component: Name of the component
            
        Returns:
            Path to the component's script
        """
        base_dir = Path(__file__).parent
        
        if component == "mcp_client":
            return str(base_dir / "mcp_client_simulator.py")
        elif component == "log_aggregator":
            return str(base_dir / "log_aggregator.py")
        elif component == "docker_manager":
            return str(base_dir / "docker_manager.py")
        elif component == "webui_tester":
            return str(base_dir / "webui_tester.py")
        else:
            return ""
            
    async def start(self, host: str = '0.0.0.0', port: int = 8000):
        """
        Start the MCP Testing Environment server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        # Create static directory if it doesn't exist
        static_dir = Path(__file__).parent / 'static'
        os.makedirs(static_dir, exist_ok=True)
        
        # Start the server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"MCP Testing Environment server started on http://{host}:{port}")
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)
            
    async def stop(self):
        """Stop the MCP Testing Environment server."""
        await self.stop_all_components()
        logger.info("MCP Testing Environment server stopped")

async def main():
    parser = argparse.ArgumentParser(description="MCP Testing Environment")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()
    
    # Create default config if it doesn't exist
    if not args.config:
        config_dir = os.path.join(os.path.expanduser("~"), ".mcp_testing")
        os.makedirs(config_dir, exist_ok=True)
        args.config = os.path.join(config_dir, "mcp_testing_environment.json")
        
        if not os.path.exists(args.config):
            with open(args.config, 'w') as f:
                json.dump({
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
                }, f, indent=2)
    
    environment = MCPTestingEnvironment(config_path=args.config)
    
    try:
        await environment.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        await environment.stop()

if __name__ == "__main__":
    asyncio.run(main())
