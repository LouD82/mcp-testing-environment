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
import aiofiles
import aiohttp
from aiohttp import web
import docker
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('log_aggregator.log')
    ]
)
logger = logging.getLogger('log_aggregator')

class LogSource:
    """Base class for log sources"""
    def __init__(self, name: str, source_type: str):
        self.name = name
        self.source_type = source_type
        self.enabled = True
        
    async def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from this source"""
        raise NotImplementedError("Subclasses must implement get_logs")
        
    async def start_monitoring(self):
        """Start monitoring this log source"""
        raise NotImplementedError("Subclasses must implement start_monitoring")
        
    async def stop_monitoring(self):
        """Stop monitoring this log source"""
        raise NotImplementedError("Subclasses must implement stop_monitoring")

class FileLogSource(LogSource):
    """Log source that reads from a file"""
    def __init__(self, name: str, file_path: str):
        super().__init__(name, "file")
        self.file_path = file_path
        self.file_position = 0
        self.monitoring = False
        self.monitor_task = None
        
    async def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from the file"""
        logs = []
        
        if not os.path.exists(self.file_path):
            logger.warning(f"Log file does not exist: {self.file_path}")
            return logs
            
        try:
            async with aiofiles.open(self.file_path, 'r') as f:
                await f.seek(self.file_position)
                lines = await f.readlines()
                self.file_position = await f.tell()
                
                for line in lines[-limit:]:
                    timestamp = datetime.now().isoformat()
                    # Try to extract timestamp from the line
                    timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(0)
                        
                    logs.append({
                        "timestamp": timestamp,
                        "source": self.name,
                        "type": self.source_type,
                        "message": line.strip()
                    })
        except Exception as e:
            logger.error(f"Error reading log file {self.file_path}: {e}")
            
        return logs
        
    async def _monitor_loop(self):
        """Monitor the log file for changes"""
        while self.monitoring:
            logs = await self.get_logs()
            if logs:
                for log in logs:
                    await self.log_callback(log)
            await asyncio.sleep(1)
        
    async def start_monitoring(self, callback):
        """Start monitoring this log file"""
        self.log_callback = callback
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started monitoring log file: {self.file_path}")
        
    async def stop_monitoring(self):
        """Stop monitoring this log file"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            logger.info(f"Stopped monitoring log file: {self.file_path}")

class DockerLogSource(LogSource):
    """Log source that reads from a Docker container"""
    def __init__(self, name: str, container_id: str):
        super().__init__(name, "docker")
        self.container_id = container_id
        self.docker_client = docker.from_env()
        self.monitoring = False
        self.monitor_task = None
        self.last_log_time = datetime.now().timestamp()
        
    async def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from the Docker container"""
        logs = []
        
        try:
            container = self.docker_client.containers.get(self.container_id)
            # Get logs since last check
            docker_logs = container.logs(
                since=int(self.last_log_time),
                timestamps=True,
                stream=False
            ).decode('utf-8').strip().split('\n')
            
            self.last_log_time = datetime.now().timestamp()
            
            for line in docker_logs[-limit:]:
                if not line:
                    continue
                    
                # Docker logs format: 2021-01-01T00:00:00.000000000Z log message
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    timestamp, message = parts
                    # Convert Docker timestamp format to ISO
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp = dt.isoformat()
                    except ValueError:
                        pass
                else:
                    timestamp = datetime.now().isoformat()
                    message = line
                    
                logs.append({
                    "timestamp": timestamp,
                    "source": self.name,
                    "type": self.source_type,
                    "message": message.strip()
                })
        except Exception as e:
            logger.error(f"Error reading Docker logs for container {self.container_id}: {e}")
            
        return logs
        
    async def _monitor_loop(self):
        """Monitor the Docker container for logs"""
        while self.monitoring:
            logs = await self.get_logs()
            if logs:
                for log in logs:
                    await self.log_callback(log)
            await asyncio.sleep(1)
        
    async def start_monitoring(self, callback):
        """Start monitoring this Docker container"""
        self.log_callback = callback
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started monitoring Docker container: {self.container_id}")
        
    async def stop_monitoring(self):
        """Stop monitoring this Docker container"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            logger.info(f"Stopped monitoring Docker container: {self.container_id}")

class MCPLogSource(LogSource):
    """Log source that reads from an MCP server"""
    def __init__(self, name: str, server_url: str = None, transport: str = "stdio"):
        super().__init__(name, "mcp")
        self.server_url = server_url
        self.transport = transport
        self.monitoring = False
        self.monitor_task = None
        self.logs = []
        
    async def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from the MCP server"""
        return self.logs[-limit:]
        
    async def add_log(self, log: Dict[str, Any]):
        """Add a log entry from the MCP server"""
        self.logs.append(log)
        if self.monitoring:
            await self.log_callback(log)
        
    async def start_monitoring(self, callback):
        """Start monitoring this MCP server"""
        self.log_callback = callback
        self.monitoring = True
        logger.info(f"Started monitoring MCP server: {self.name}")
        
    async def stop_monitoring(self):
        """Stop monitoring this MCP server"""
        self.monitoring = False
        logger.info(f"Stopped monitoring MCP server: {self.name}")

class WebUILogSource(LogSource):
    """Log source that reads from a web UI"""
    def __init__(self, name: str, url: str):
        super().__init__(name, "webui")
        self.url = url
        self.monitoring = False
        self.monitor_task = None
        self.logs = []
        
    async def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from the web UI"""
        return self.logs[-limit:]
        
    async def add_log(self, log: Dict[str, Any]):
        """Add a log entry from the web UI"""
        self.logs.append(log)
        if self.monitoring:
            await self.log_callback(log)
        
    async def start_monitoring(self, callback):
        """Start monitoring this web UI"""
        self.log_callback = callback
        self.monitoring = True
        logger.info(f"Started monitoring web UI: {self.url}")
        
    async def stop_monitoring(self):
        """Stop monitoring this web UI"""
        self.monitoring = False
        logger.info(f"Stopped monitoring web UI: {self.url}")

class LogAggregator:
    """
    Log Aggregation System for MCP Testing Environment.
    
    Collects and aggregates logs from multiple sources:
    - MCP servers
    - Docker containers
    - Web UIs
    - Log files
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Log Aggregator.
        
        Args:
            config_path: Path to configuration file
        """
        self.log_sources = {}
        self.logs = []
        self.max_logs = 10000  # Maximum number of logs to keep in memory
        self.config_path = config_path
        self.app = web.Application()
        self.setup_routes()
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
            
    def setup_routes(self):
        """Set up web routes for the API"""
        self.app.router.add_get('/api/logs', self.handle_get_logs)
        self.app.router.add_get('/api/sources', self.handle_get_sources)
        self.app.router.add_post('/api/sources', self.handle_add_source)
        self.app.router.add_delete('/api/sources/{name}', self.handle_remove_source)
        self.app.router.add_post('/api/logs', self.handle_add_log)
        
    async def handle_get_logs(self, request):
        """Handle GET /api/logs"""
        limit = int(request.query.get('limit', 100))
        source = request.query.get('source')
        source_type = request.query.get('type')
        
        logs = self.get_filtered_logs(limit, source, source_type)
        return web.json_response(logs)
        
    async def handle_get_sources(self, request):
        """Handle GET /api/sources"""
        sources = [{
            "name": source.name,
            "type": source.source_type,
            "enabled": source.enabled
        } for source in self.log_sources.values()]
        return web.json_response(sources)
        
    async def handle_add_source(self, request):
        """Handle POST /api/sources"""
        data = await request.json()
        name = data.get('name')
        source_type = data.get('type')
        
        if not name or not source_type:
            return web.json_response({"error": "Missing name or type"}, status=400)
            
        if name in self.log_sources:
            return web.json_response({"error": f"Source {name} already exists"}, status=400)
            
        if source_type == 'file':
            file_path = data.get('file_path')
            if not file_path:
                return web.json_response({"error": "Missing file_path"}, status=400)
            await self.add_file_source(name, file_path)
        elif source_type == 'docker':
            container_id = data.get('container_id')
            if not container_id:
                return web.json_response({"error": "Missing container_id"}, status=400)
            await self.add_docker_source(name, container_id)
        elif source_type == 'mcp':
            server_url = data.get('server_url')
            transport = data.get('transport', 'stdio')
            await self.add_mcp_source(name, server_url, transport)
        elif source_type == 'webui':
            url = data.get('url')
            if not url:
                return web.json_response({"error": "Missing url"}, status=400)
            await self.add_webui_source(name, url)
        else:
            return web.json_response({"error": f"Unknown source type: {source_type}"}, status=400)
            
        return web.json_response({"success": True})
        
    async def handle_remove_source(self, request):
        """Handle DELETE /api/sources/{name}"""
        name = request.match_info['name']
        
        if name not in self.log_sources:
            return web.json_response({"error": f"Source {name} not found"}, status=404)
            
        await self.remove_source(name)
        return web.json_response({"success": True})
        
    async def handle_add_log(self, request):
        """Handle POST /api/logs"""
        log = await request.json()
        
        if 'source' not in log or 'message' not in log:
            return web.json_response({"error": "Missing source or message"}, status=400)
            
        source_name = log['source']
        if source_name in self.log_sources:
            source = self.log_sources[source_name]
            if isinstance(source, MCPLogSource) or isinstance(source, WebUILogSource):
                await source.add_log(log)
                
        await self.add_log(log)
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
                
            # Load log sources
            for source in config.get('sources', []):
                name = source.get('name')
                source_type = source.get('type')
                
                if not name or not source_type:
                    logger.warning(f"Skipping source with missing name or type: {source}")
                    continue
                    
                if source_type == 'file':
                    file_path = source.get('file_path')
                    if file_path:
                        asyncio.create_task(self.add_file_source(name, file_path))
                elif source_type == 'docker':
                    container_id = source.get('container_id')
                    if container_id:
                        asyncio.create_task(self.add_docker_source(name, container_id))
                elif source_type == 'mcp':
                    server_url = source.get('server_url')
                    transport = source.get('transport', 'stdio')
                    asyncio.create_task(self.add_mcp_source(name, server_url, transport))
                elif source_type == 'webui':
                    url = source.get('url')
                    if url:
                        asyncio.create_task(self.add_webui_source(name, url))
                        
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
                "sources": []
            }
            
            for name, source in self.log_sources.items():
                source_config = {
                    "name": name,
                    "type": source.source_type,
                    "enabled": source.enabled
                }
                
                if isinstance(source, FileLogSource):
                    source_config["file_path"] = source.file_path
                elif isinstance(source, DockerLogSource):
                    source_config["container_id"] = source.container_id
                elif isinstance(source, MCPLogSource):
                    source_config["server_url"] = source.server_url
                    source_config["transport"] = source.transport
                elif isinstance(source, WebUILogSource):
                    source_config["url"] = source.url
                    
                config["sources"].append(source_config)
                
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {self.config_path}: {e}")
            
    async def add_log(self, log: Dict[str, Any]):
        """
        Add a log entry to the aggregator.
        
        Args:
            log: Log entry to add
        """
        if 'timestamp' not in log:
            log['timestamp'] = datetime.now().isoformat()
            
        self.logs.append(log)
        
        # Trim logs if we have too many
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
            
    def get_filtered_logs(self, limit: int = 100, source: str = None, source_type: str = None) -> List[Dict[str, Any]]:
        """
        Get filtered logs from the aggregator.
        
        Args:
            limit: Maximum number of logs to return
            source: Filter by source name
            source_type: Filter by source type
            
        Returns:
            List of log entries
        """
        filtered_logs = self.logs
        
        if source:
            filtered_logs = [log for log in filtered_logs if log.get('source') == source]
            
        if source_type:
            filtered_logs = [log for log in filtered_logs if log.get('type') == source_type]
            
        return filtered_logs[-limit:]
        
    async def add_file_source(self, name: str, file_path: str):
        """
        Add a file log source.
        
        Args:
            name: Name of the source
            file_path: Path to the log file
        """
        if name in self.log_sources:
            await self.remove_source(name)
            
        source = FileLogSource(name, file_path)
        self.log_sources[name] = source
        await source.start_monitoring(self.add_log)
        logger.info(f"Added file log source: {name} ({file_path})")
        
    async def add_docker_source(self, name: str, container_id: str):
        """
        Add a Docker log source.
        
        Args:
            name: Name of the source
            container_id: Docker container ID
        """
        if name in self.log_sources:
            await self.remove_source(name)
            
        source = DockerLogSource(name, container_id)
        self.log_sources[name] = source
        await source.start_monitoring(self.add_log)
        logger.info(f"Added Docker log source: {name} ({container_id})")
        
    async def add_mcp_source(self, name: str, server_url: str = None, transport: str = "stdio"):
        """
        Add an MCP log source.
        
        Args:
            name: Name of the source
            server_url: URL of the MCP server (for HTTP transport)
            transport: Transport method (stdio or http)
        """
        if name in self.log_sources:
            await self.remove_source(name)
            
        source = MCPLogSource(name, server_url, transport)
        self.log_sources[name] = source
        await source.start_monitoring(self.add_log)
        logger.info(f"Added MCP log source: {name}")
        
    async def add_webui_source(self, name: str, url: str):
        """
        Add a web UI log source.
        
        Args:
            name: Name of the source
            url: URL of the web UI
        """
        if name in self.log_sources:
            await self.remove_source(name)
            
        source = WebUILogSource(name, url)
        self.log_sources[name] = source
        await source.start_monitoring(self.add_log)
        logger.info(f"Added web UI log source: {name} ({url})")
        
    async def remove_source(self, name: str):
        """
        Remove a log source.
        
        Args:
            name: Name of the source to remove
        """
        if name in self.log_sources:
            source = self.log_sources[name]
            await source.stop_monitoring()
            del self.log_sources[name]
            logger.info(f"Removed log source: {name}")
            
    async def start(self, host: str = '0.0.0.0', port: int = 8080):
        """
        Start the log aggregator server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Log aggregator server started on http://{host}:{port}")
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)
            
    async def stop(self):
        """Stop the log aggregator server."""
        for name in list(self.log_sources.keys()):
            await self.remove_source(name)
            
        logger.info("Log aggregator server stopped")

async def main():
    parser = argparse.ArgumentParser(description="MCP Testing Environment Log Aggregator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    args = parser.parse_args()
    
    # Create default config if it doesn't exist
    if not args.config:
        config_dir = os.path.join(os.path.expanduser("~"), ".mcp_testing")
        os.makedirs(config_dir, exist_ok=True)
        args.config = os.path.join(config_dir, "log_aggregator.json")
        
        if not os.path.exists(args.config):
            with open(args.config, 'w') as f:
                json.dump({
                    "sources": []
                }, f, indent=2)
    
    aggregator = LogAggregator(config_path=args.config)
    
    try:
        await aggregator.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        await aggregator.stop()

if __name__ == "__main__":
    asyncio.run(main())
