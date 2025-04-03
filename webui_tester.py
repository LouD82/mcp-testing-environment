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
from pathlib import Path
import base64
from playwright.async_api import async_playwright, Browser, Page, ElementHandle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('webui_tester.log')
    ]
)
logger = logging.getLogger('webui_tester')

class WebUITester:
    """
    Web UI Testing Component for MCP Testing Environment.
    
    Provides tools for testing and debugging web interfaces:
    - View web UI elements
    - Interact with web UI
    - Capture screenshots
    - Inspect network traffic
    - Test responsive behavior
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Web UI Tester.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.app = web.Application()
        self.setup_routes()
        self.browser = None
        self.page = None
        self.browser_context = None
        self.headless = True
        self.playwright = None
        self.log_aggregator_url = None
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
            
    def setup_routes(self):
        """Set up web routes for the API"""
        self.app.router.add_get('/api/status', self.handle_get_status)
        self.app.router.add_post('/api/browser/launch', self.handle_launch_browser)
        self.app.router.add_post('/api/browser/close', self.handle_close_browser)
        self.app.router.add_post('/api/browser/navigate', self.handle_navigate)
        self.app.router.add_get('/api/browser/screenshot', self.handle_screenshot)
        self.app.router.add_get('/api/browser/content', self.handle_get_content)
        self.app.router.add_get('/api/browser/elements', self.handle_get_elements)
        self.app.router.add_post('/api/browser/click', self.handle_click)
        self.app.router.add_post('/api/browser/type', self.handle_type)
        self.app.router.add_post('/api/browser/select', self.handle_select)
        self.app.router.add_get('/api/browser/network', self.handle_get_network)
        self.app.router.add_post('/api/config', self.handle_update_config)
        
    async def handle_get_status(self, request):
        """Handle GET /api/status"""
        status = {
            "browser_running": self.browser is not None,
            "current_url": await self.get_current_url() if self.page else None,
            "headless": self.headless,
            "log_aggregator_url": self.log_aggregator_url
        }
        return web.json_response(status)
        
    async def handle_launch_browser(self, request):
        """Handle POST /api/browser/launch"""
        data = await request.json()
        self.headless = data.get('headless', True)
        
        success = await self.launch_browser()
        
        if not success:
            return web.json_response({"error": "Failed to launch browser"}, status=500)
            
        return web.json_response({"success": True})
        
    async def handle_close_browser(self, request):
        """Handle POST /api/browser/close"""
        await self.close_browser()
        return web.json_response({"success": True})
        
    async def handle_navigate(self, request):
        """Handle POST /api/browser/navigate"""
        data = await request.json()
        url = data.get('url')
        
        if not url:
            return web.json_response({"error": "Missing URL"}, status=400)
            
        if not self.page:
            return web.json_response({"error": "Browser not launched"}, status=400)
            
        try:
            await self.page.goto(url)
            return web.json_response({"success": True, "url": url})
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return web.json_response({"error": f"Failed to navigate to {url}: {str(e)}"}, status=500)
        
    async def handle_screenshot(self, request):
        """Handle GET /api/browser/screenshot"""
        if not self.page:
            return web.json_response({"error": "Browser not launched"}, status=400)
            
        try:
            screenshot_path = f"/tmp/screenshot_{int(time.time())}.png"
            await self.page.screenshot(path=screenshot_path)
            
            with open(screenshot_path, 'rb') as f:
                screenshot_data = f.read()
                
            os.remove(screenshot_path)
            
            return web.json_response({
                "success": True,
                "screenshot": base64.b64encode(screenshot_data).decode('utf-8')
            })
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return web.json_response({"error": f"Failed to take screenshot: {str(e)}"}, status=500)
        
    async def handle_get_content(self, request):
        """Handle GET /api/browser/content"""
        if not self.page:
            return web.json_response({"error": "Browser not launched"}, status=400)
            
        try:
            content = await self.page.content()
            title = await self.page.title()
            url = self.page.url
            
            return web.json_response({
                "success": True,
                "title": title,
                "url": url,
                "content": content
            })
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return web.json_response({"error": f"Failed to get page content: {str(e)}"}, status=500)
        
    async def handle_get_elements(self, request):
        """Handle GET /api/browser/elements"""
        if not self.page:
            return web.json_response({"error": "Browser not launched"}, status=400)
            
        selector = request.query.get('selector', '*')
        
        try:
            elements = await self.page.query_selector_all(selector)
            
            element_data = []
            for i, element in enumerate(elements):
                tag_name = await element.evaluate('el => el.tagName')
                text = await element.evaluate('el => el.textContent')
                attributes = await element.evaluate('el => {const attrs = {}; for (const attr of el.attributes) { attrs[attr.name] = attr.value; } return attrs; }')
                
                element_data.append({
                    "index": i,
                    "tag": tag_name,
                    "text": text,
                    "attributes": attributes
                })
                
            return web.json_response({
                "success": True,
                "elements": element_data
            })
        except Exception as e:
            logger.error(f"Error getting elements: {e}")
            return web.json_response({"error": f"Failed to get elements: {str(e)}"}, status=500)
        
    async def handle_click(self, request):
        """Handle POST /api/browser/click"""
        if not self.page:
            return web.json_response({"error": "Browser not launched"}, status=400)
            
        data = await request.json()
        selector = data.get('selector')
        index = data.get('index')
        x = data.get('x')
        y = data.get('y')
        
        try:
            if selector and index is not None:
                elements = await self.page.query_selector_all(selector)
                if index >= len(elements):
                    return web.json_response({"error": f"Element index {index} out of range"}, status=400)
                    
                await elements[index].click()
            elif selector:
                await self.page.click(selector)
            elif x is not None and y is not None:
                await self.page.mouse.click(x, y)
            else:
                return web.json_response({"error": "Missing selector or coordinates"}, status=400)
                
            return web.json_response({"success": True})
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return web.json_response({"error": f"Failed to click element: {str(e)}"}, status=500)
        
    async def handle_type(self, request):
        """Handle POST /api/browser/type"""
        if not self.page:
            return web.json_response({"error": "Browser not launched"}, status=400)
            
        data = await request.json()
        selector = data.get('selector')
        text = data.get('text')
        
        if not selector or text is None:
            return web.json_response({"error": "Missing selector or text"}, status=400)
            
        try:
            await self.page.fill(selector, text)
            return web.json_response({"success": True})
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return web.json_response({"error": f"Failed to type text: {str(e)}"}, status=500)
        
    async def handle_select(self, request):
        """Handle POST /api/browser/select"""
        if not self.page:
            return web.json_response({"error": "Browser not launched"}, status=400)
            
        data = await request.json()
        selector = data.get('selector')
        value = data.get('value')
        
        if not selector or value is None:
            return web.json_response({"error": "Missing selector or value"}, status=400)
            
        try:
            await self.page.select_option(selector, value)
            return web.json_response({"success": True})
        except Exception as e:
            logger.error(f"Error selecting option: {e}")
            return web.json_response({"error": f"Failed to select option: {str(e)}"}, status=500)
        
    async def handle_get_network(self, request):
        """Handle GET /api/browser/network"""
        if not self.page:
            return web.json_response({"error": "Browser not launched"}, status=400)
            
        try:
            # This is a simplified version - in a real implementation, you would
            # set up network request monitoring when the page is created
            network_info = await self.page.evaluate('''() => {
                const performance = window.performance;
                if (!performance) {
                    return { error: "Performance API not available" };
                }
                
                const resources = performance.getEntriesByType('resource');
                return resources.map(resource => ({
                    name: resource.name,
                    initiatorType: resource.initiatorType,
                    startTime: resource.startTime,
                    duration: resource.duration,
                    transferSize: resource.transferSize,
                    decodedBodySize: resource.decodedBodySize
                }));
            }''')
            
            return web.json_response({
                "success": True,
                "network": network_info
            })
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return web.json_response({"error": f"Failed to get network info: {str(e)}"}, status=500)
        
    async def handle_update_config(self, request):
        """Handle POST /api/config"""
        data = await request.json()
        
        if 'headless' in data:
            self.headless = data['headless']
            
        if 'log_aggregator_url' in data:
            self.log_aggregator_url = data['log_aggregator_url']
            
        self.save_config()
        
        return web.json_response({
            "success": True,
            "config": {
                "headless": self.headless,
                "log_aggregator_url": self.log_aggregator_url
            }
        })
        
    def load_config(self, config_path: str):
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            if 'headless' in config:
                self.headless = config['headless']
                
            if 'log_aggregator_url' in config:
                self.log_aggregator_url = config['log_aggregator_url']
                
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
                "headless": self.headless,
                "log_aggregator_url": self.log_aggregator_url
            }
                
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {self.config_path}: {e}")
            
    async def launch_browser(self) -> bool:
        """
        Launch the browser.
        
        Returns:
            True if successful, False otherwise
        """
        if self.browser:
            await self.close_browser()
            
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.browser_context = await self.browser.new_context()
            self.page = await self.browser_context.new_page()
            
            # Set up logging
            if self.log_aggregator_url:
                await self.setup_logging()
                
            logger.info("Browser launched")
            return True
        except Exception as e:
            logger.error(f"Error launching browser: {e}")
            return False
            
    async def close_browser(self):
        """Close the browser."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.browser_context:
                await self.browser_context.close()
                self.browser_context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            
    async def setup_logging(self):
        """Set up logging to the log aggregator."""
        if not self.log_aggregator_url or not self.page:
            return
            
        try:
            # Set up console logging
            await self.page.evaluate('''() => {
                const originalConsoleLog = console.log;
                const originalConsoleError = console.error;
                const originalConsoleWarn = console.warn;
                const originalConsoleInfo = console.info;
                
                const logAggregatorUrl = arguments[0];
                
                function sendLog(level, args) {
                    const message = Array.from(args).map(arg => {
                        if (typeof arg === 'object') {
                            try {
                                return JSON.stringify(arg);
                            } catch (e) {
                                return String(arg);
                            }
                        }
                        return String(arg);
                    }).join(' ');
                    
                    fetch(logAggregatorUrl + '/api/logs', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            source: 'webui',
                            type: 'console',
                            level: level,
                            message: message,
                            timestamp: new Date().toISOString()
                        })
                    }).catch(e => {
                        // Avoid infinite loops by not logging fetch errors
                    });
                    
                    return message;
                }
                
                console.log = function() {
                    const message = sendLog('info', arguments);
                    originalConsoleLog.apply(console, arguments);
                };
                
                console.error = function() {
                    const message = sendLog('error', arguments);
                    originalConsoleError.apply(console, arguments);
                };
                
                console.warn = function() {
                    const message = sendLog('warn', arguments);
                    originalConsoleWarn.apply(console, arguments);
                };
                
                console.info = function() {
                    const message = sendLog('info', arguments);
                    originalConsoleInfo.apply(console, arguments);
                };
            }''', self.log_aggregator_url)
            
            logger.info(f"Set up logging to {self.log_aggregator_url}")
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")
            
    async def get_current_url(self) -> Optional[str]:
        """
        Get the current URL.
        
        Returns:
            Current URL or None if browser not launched
        """
        if not self.page:
            return None
            
        return self.page.url
            
    async def start(self, host: str = '0.0.0.0', port: int = 8082):
        """
        Start the Web UI Tester server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Web UI Tester server started on http://{host}:{port}")
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)
            
    async def stop(self):
        """Stop the Web UI Tester server."""
        await self.close_browser()
        logger.info("Web UI Tester server stopped")

async def main():
    parser = argparse.ArgumentParser(description="MCP Testing Environment Web UI Tester")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8082, help="Port to bind to")
    args = parser.parse_args()
    
    # Create default config if it doesn't exist
    if not args.config:
        config_dir = os.path.join(os.path.expanduser("~"), ".mcp_testing")
        os.makedirs(config_dir, exist_ok=True)
        args.config = os.path.join(config_dir, "webui_tester.json")
        
        if not os.path.exists(args.config):
            with open(args.config, 'w') as f:
                json.dump({
                    "headless": True,
                    "log_aggregator_url": "http://localhost:8080"
                }, f, indent=2)
    
    tester = WebUITester(config_path=args.config)
    
    try:
        await tester.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        await tester.stop()

if __name__ == "__main__":
    asyncio.run(main())
