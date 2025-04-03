#!/usr/bin/env python3

import asyncio
import json
import logging
import argparse
import sys
import os
import time
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import aiohttp
from aiohttp import web
import docker
import yaml
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('docker_manager.log')
    ]
)
logger = logging.getLogger('docker_manager')

class DockerContainerManager:
    """
    Docker Container Manager for MCP Testing Environment.
    
    Manages Docker containers used for Discord integration:
    - Start, stop, and restart containers
    - View container status and health
    - Access container logs
    - Configure container settings
    - Support for Docker Compose for multi-container setups
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Docker Container Manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.docker_client = docker.from_env()
        self.containers = {}
        self.compose_projects = {}
        self.config_path = config_path
        self.app = web.Application()
        self.setup_routes()
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
            
    def setup_routes(self):
        """Set up web routes for the API"""
        self.app.router.add_get('/api/containers', self.handle_get_containers)
        self.app.router.add_get('/api/containers/{id}', self.handle_get_container)
        self.app.router.add_post('/api/containers/{id}/start', self.handle_start_container)
        self.app.router.add_post('/api/containers/{id}/stop', self.handle_stop_container)
        self.app.router.add_post('/api/containers/{id}/restart', self.handle_restart_container)
        self.app.router.add_get('/api/containers/{id}/logs', self.handle_get_container_logs)
        
        self.app.router.add_get('/api/compose', self.handle_get_compose_projects)
        self.app.router.add_get('/api/compose/{name}', self.handle_get_compose_project)
        self.app.router.add_post('/api/compose/{name}/up', self.handle_compose_up)
        self.app.router.add_post('/api/compose/{name}/down', self.handle_compose_down)
        self.app.router.add_post('/api/compose/{name}/restart', self.handle_compose_restart)
        
        self.app.router.add_post('/api/compose', self.handle_add_compose_project)
        self.app.router.add_delete('/api/compose/{name}', self.handle_remove_compose_project)
        
    async def handle_get_containers(self, request):
        """Handle GET /api/containers"""
        containers = await self.get_all_containers()
        return web.json_response(containers)
        
    async def handle_get_container(self, request):
        """Handle GET /api/containers/{id}"""
        container_id = request.match_info['id']
        container = await self.get_container(container_id)
        
        if not container:
            return web.json_response({"error": f"Container {container_id} not found"}, status=404)
            
        return web.json_response(container)
        
    async def handle_start_container(self, request):
        """Handle POST /api/containers/{id}/start"""
        container_id = request.match_info['id']
        success = await self.start_container(container_id)
        
        if not success:
            return web.json_response({"error": f"Failed to start container {container_id}"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_stop_container(self, request):
        """Handle POST /api/containers/{id}/stop"""
        container_id = request.match_info['id']
        success = await self.stop_container(container_id)
        
        if not success:
            return web.json_response({"error": f"Failed to stop container {container_id}"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_restart_container(self, request):
        """Handle POST /api/containers/{id}/restart"""
        container_id = request.match_info['id']
        success = await self.restart_container(container_id)
        
        if not success:
            return web.json_response({"error": f"Failed to restart container {container_id}"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_get_container_logs(self, request):
        """Handle GET /api/containers/{id}/logs"""
        container_id = request.match_info['id']
        limit = int(request.query.get('limit', 100))
        logs = await self.get_container_logs(container_id, limit)
        
        if logs is None:
            return web.json_response({"error": f"Failed to get logs for container {container_id}"}, status=500)
            
        return web.json_response({"logs": logs})
        
    async def handle_get_compose_projects(self, request):
        """Handle GET /api/compose"""
        projects = []
        for name, project in self.compose_projects.items():
            projects.append({
                "name": name,
                "path": project["path"],
                "status": await self.get_compose_status(name)
            })
        return web.json_response(projects)
        
    async def handle_get_compose_project(self, request):
        """Handle GET /api/compose/{name}"""
        name = request.match_info['name']
        
        if name not in self.compose_projects:
            return web.json_response({"error": f"Compose project {name} not found"}, status=404)
            
        project = self.compose_projects[name]
        project_info = {
            "name": name,
            "path": project["path"],
            "status": await self.get_compose_status(name),
            "containers": await self.get_compose_containers(name)
        }
        
        return web.json_response(project_info)
        
    async def handle_compose_up(self, request):
        """Handle POST /api/compose/{name}/up"""
        name = request.match_info['name']
        
        if name not in self.compose_projects:
            return web.json_response({"error": f"Compose project {name} not found"}, status=404)
            
        success = await self.compose_up(name)
        
        if not success:
            return web.json_response({"error": f"Failed to start compose project {name}"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_compose_down(self, request):
        """Handle POST /api/compose/{name}/down"""
        name = request.match_info['name']
        
        if name not in self.compose_projects:
            return web.json_response({"error": f"Compose project {name} not found"}, status=404)
            
        success = await self.compose_down(name)
        
        if not success:
            return web.json_response({"error": f"Failed to stop compose project {name}"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_compose_restart(self, request):
        """Handle POST /api/compose/{name}/restart"""
        name = request.match_info['name']
        
        if name not in self.compose_projects:
            return web.json_response({"error": f"Compose project {name} not found"}, status=404)
            
        success = await self.compose_restart(name)
        
        if not success:
            return web.json_response({"error": f"Failed to restart compose project {name}"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_add_compose_project(self, request):
        """Handle POST /api/compose"""
        data = await request.json()
        name = data.get('name')
        path = data.get('path')
        
        if not name or not path:
            return web.json_response({"error": "Missing name or path"}, status=400)
            
        if name in self.compose_projects:
            return web.json_response({"error": f"Compose project {name} already exists"}, status=400)
            
        if not os.path.exists(path) or not os.path.isfile(path):
            return web.json_response({"error": f"Compose file {path} does not exist"}, status=400)
            
        self.compose_projects[name] = {
            "path": path
        }
        
        self.save_config()
        
        return web.json_response({"success": True})
        
    async def handle_remove_compose_project(self, request):
        """Handle DELETE /api/compose/{name}"""
        name = request.match_info['name']
        
        if name not in self.compose_projects:
            return web.json_response({"error": f"Compose project {name} not found"}, status=404)
            
        # Stop the compose project first
        await self.compose_down(name)
        
        del self.compose_projects[name]
        self.save_config()
        
        return web.json_response({"success": True})
        
    def load_config(self, config_path: str):
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Load compose projects
            self.compose_projects = config.get('compose_projects', {})
                
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            
    def save_config(self):
        """Save configuration to file."""
        if not self.config_path:
            logger.warning("No config path specified, cannot save configuration")
            return
            
        try:
            config = {
                "compose_projects": self.compose_projects
            }
                
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {self.config_path}: {e}")
            
    async def get_all_containers(self) -> List[Dict[str, Any]]:
        """
        Get all Docker containers.
        
        Returns:
            List of container information
        """
        containers = []
        
        try:
            for container in self.docker_client.containers.list(all=True):
                containers.append({
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else container.image.id,
                    "created": container.attrs["Created"],
                    "ports": self._format_ports(container),
                    "labels": container.labels
                })
        except Exception as e:
            logger.error(f"Error getting containers: {e}")
            
        return containers
        
    async def get_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Container information or None if not found
        """
        try:
            container = self.docker_client.containers.get(container_id)
            
            # Get more detailed information
            container.reload()
            
            return {
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else container.image.id,
                "created": container.attrs["Created"],
                "ports": self._format_ports(container),
                "labels": container.labels,
                "network_settings": container.attrs["NetworkSettings"],
                "mounts": container.attrs["Mounts"],
                "config": container.attrs["Config"]
            }
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting container {container_id}: {e}")
            return None
            
    async def start_container(self, container_id: str) -> bool:
        """
        Start a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.start()
            logger.info(f"Started container {container_id}")
            return True
        except Exception as e:
            logger.error(f"Error starting container {container_id}: {e}")
            return False
            
    async def stop_container(self, container_id: str) -> bool:
        """
        Stop a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop()
            logger.info(f"Stopped container {container_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping container {container_id}: {e}")
            return False
            
    async def restart_container(self, container_id: str) -> bool:
        """
        Restart a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.restart()
            logger.info(f"Restarted container {container_id}")
            return True
        except Exception as e:
            logger.error(f"Error restarting container {container_id}: {e}")
            return False
            
    async def get_container_logs(self, container_id: str, limit: int = 100) -> Optional[List[str]]:
        """
        Get logs from a container.
        
        Args:
            container_id: Container ID or name
            limit: Maximum number of log lines to return
            
        Returns:
            List of log lines or None if error
        """
        try:
            container = self.docker_client.containers.get(container_id)
            logs = container.logs(tail=limit, timestamps=True).decode('utf-8').strip().split('\n')
            return logs
        except Exception as e:
            logger.error(f"Error getting logs for container {container_id}: {e}")
            return None
            
    async def get_compose_status(self, name: str) -> str:
        """
        Get status of a Docker Compose project.
        
        Args:
            name: Name of the compose project
            
        Returns:
            Status string (up, partially_up, down, or unknown)
        """
        if name not in self.compose_projects:
            return "unknown"
            
        path = self.compose_projects[name]["path"]
        
        try:
            # Use docker-compose ps to check status
            result = subprocess.run(
                ["docker-compose", "-f", path, "ps", "--quiet"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Error checking compose project {name} status: {result.stderr}")
                return "unknown"
                
            container_ids = result.stdout.strip().split('\n')
            container_ids = [cid for cid in container_ids if cid]
            
            if not container_ids:
                return "down"
                
            # Check if all containers are running
            all_running = True
            any_running = False
            
            for container_id in container_ids:
                try:
                    container = self.docker_client.containers.get(container_id)
                    if container.status == "running":
                        any_running = True
                    else:
                        all_running = False
                except:
                    all_running = False
                    
            if all_running:
                return "up"
            elif any_running:
                return "partially_up"
            else:
                return "down"
        except Exception as e:
            logger.error(f"Error checking compose project {name} status: {e}")
            return "unknown"
            
    async def get_compose_containers(self, name: str) -> List[Dict[str, Any]]:
        """
        Get containers in a Docker Compose project.
        
        Args:
            name: Name of the compose project
            
        Returns:
            List of container information
        """
        if name not in self.compose_projects:
            return []
            
        path = self.compose_projects[name]["path"]
        
        try:
            # Use docker-compose ps to get containers
            result = subprocess.run(
                ["docker-compose", "-f", path, "ps", "--quiet"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Error getting compose project {name} containers: {result.stderr}")
                return []
                
            container_ids = result.stdout.strip().split('\n')
            container_ids = [cid for cid in container_ids if cid]
            
            containers = []
            for container_id in container_ids:
                container_info = await self.get_container(container_id)
                if container_info:
                    containers.append(container_info)
                    
            return containers
        except Exception as e:
            logger.error(f"Error getting compose project {name} containers: {e}")
            return []
            
    async def compose_up(self, name: str) -> bool:
        """
        Start a Docker Compose project.
        
        Args:
            name: Name of the compose project
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.compose_projects:
            logger.error(f"Compose project {name} not found")
            return False
            
        path = self.compose_projects[name]["path"]
        
        try:
            # Use docker-compose up to start the project
            process = await asyncio.create_subprocess_exec(
                "docker-compose", "-f", path, "up", "-d",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Error starting compose project {name}: {stderr.decode()}")
                return False
                
            logger.info(f"Started compose project {name}")
            return True
        except Exception as e:
            logger.error(f"Error starting compose project {name}: {e}")
            return False
            
    async def compose_down(self, name: str) -> bool:
        """
        Stop a Docker Compose project.
        
        Args:
            name: Name of the compose project
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.compose_projects:
            logger.error(f"Compose project {name} not found")
            return False
            
        path = self.compose_projects[name]["path"]
        
        try:
            # Use docker-compose down to stop the project
            process = await asyncio.create_subprocess_exec(
                "docker-compose", "-f", path, "down",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Error stopping compose project {name}: {stderr.decode()}")
                return False
                
            logger.info(f"Stopped compose project {name}")
            return True
        except Exception as e:
            logger.error(f"Error stopping compose project {name}: {e}")
            return False
            
    async def compose_restart(self, name: str) -> bool:
        """
        Restart a Docker Compose project.
        
        Args:
            name: Name of the compose project
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.compose_projects:
            logger.error(f"Compose project {name} not found")
            return False
            
        path = self.compose_projects[name]["path"]
        
        try:
            # Use docker-compose restart to restart the project
            process = await asyncio.create_subprocess_exec(
                "docker-compose", "-f", path, "restart",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Error restarting compose project {name}: {stderr.decode()}")
                return False
                
            logger.info(f"Restarted compose project {name}")
            return True
        except Exception as e:
            logger.error(f"Error restarting compose project {name}: {e}")
            return False
            
    def _format_ports(self, container) -> Dict[str, List[Dict[str, Any]]]:
        """
        Format container ports information.
        
        Args:
            container: Docker container object
            
        Returns:
            Formatted ports information
        """
        ports = {}
        
        try:
            for port, bindings in container.attrs["NetworkSettings"]["Ports"].items():
                if bindings:
                    ports[port] = [
                        {
                            "host_ip": binding["HostIp"],
                            "host_port": binding["HostPort"]
                        }
                        for binding in bindings
                    ]
                else:
                    ports[port] = []
        except:
            pass
            
        return ports
            
    async def start(self, host: str = '0.0.0.0', port: int = 8081):
        """
        Start the Docker Container Manager server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Docker Container Manager server started on http://{host}:{port}")
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)
            
    async def stop(self):
        """Stop the Docker Container Manager server."""
        logger.info("Docker Container Manager server stopped")

async def main():
    parser = argparse.ArgumentParser(description="MCP Testing Environment Docker Container Manager")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    args = parser.parse_args()
    
    # Create default config if it doesn't exist
    if not args.config:
        config_dir = os.path.join(os.path.expanduser("~"), ".mcp_testing")
        os.makedirs(config_dir, exist_ok=True)
        args.config = os.path.join(config_dir, "docker_manager.json")
        
        if not os.path.exists(args.config):
            with open(args.config, 'w') as f:
                json.dump({
                    "compose_projects": {}
                }, f, indent=2)
    
    manager = DockerContainerManager(config_path=args.config)
    
    try:
        await manager.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
