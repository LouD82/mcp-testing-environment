#!/usr/bin/env python3

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

def create_requirements_file(output_dir):
    """Create requirements.txt file with all dependencies."""
    requirements = [
        "aiohttp==3.8.5",
        "aiofiles==23.2.1",
        "docker==6.1.3",
        "playwright==1.40.0",
        "pyyaml==6.0.1"
    ]
    
    with open(os.path.join(output_dir, "requirements.txt"), "w") as f:
        f.write("\n".join(requirements))
    
    print(f"Created requirements.txt in {output_dir}")

def create_readme(output_dir):
    """Create README.md file with installation and usage instructions."""
    readme_content = """# MCP Testing Environment

A comprehensive testing environment for MCP (Model Context Protocol) servers, with a particular focus on Discord integration.

## Features

- MCP Client Simulator for testing MCP servers without requiring an actual MCP client
- Log Aggregation System for collecting and displaying logs from multiple sources
- Docker Container Management Interface for managing containers used in Discord integration
- Web UI Testing Component for testing and debugging web interfaces
- Integration Framework for tying all components together

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   playwright install
   ```

3. Start the MCP Testing Environment:
   ```bash
   python mcp_testing_environment.py
   ```

4. Access the web interface at http://localhost:8000

## Documentation

See the following files for detailed documentation:

- `documentation.md`: Comprehensive documentation for the MCP Testing Environment
- `usage_instructions.md`: Instructions for using the environment in future conversations

## Testing

A simple MCP server is included for testing purposes:

```bash
python simple_mcp_server.py
```

You can use this server to test the MCP Client Simulator and other components of the testing environment.

## License

MIT
"""
    
    with open(os.path.join(output_dir, "README.md"), "w") as f:
        f.write(readme_content)
    
    print(f"Created README.md in {output_dir}")

def create_setup_script(output_dir):
    """Create setup.py script for easy installation."""
    setup_content = """#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="mcp-testing-environment",
    version="1.0.0",
    description="A comprehensive testing environment for MCP servers",
    author="Manus",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.5",
        "aiofiles>=23.2.1",
        "docker>=6.1.3",
        "playwright>=1.40.0",
        "pyyaml>=6.0.1"
    ],
    entry_points={
        'console_scripts': [
            'mcp-testing-environment=mcp_testing_environment:main',
        ],
    },
    python_requires='>=3.8',
)
"""
    
    with open(os.path.join(output_dir, "setup.py"), "w") as f:
        f.write(setup_content)
    
    print(f"Created setup.py in {output_dir}")

def create_docker_compose(output_dir):
    """Create docker-compose.yml for containerized deployment."""
    docker_compose_content = """version: '3'

services:
  mcp-testing-environment:
    build: .
    ports:
      - "8000:8000"
      - "8079:8079"
      - "8080:8080"
      - "8081:8081"
      - "8082:8082"
    volumes:
      - ~/.mcp_testing:/root/.mcp_testing
      - /var/run/docker.sock:/var/run/docker.sock
    restart: unless-stopped
"""
    
    with open(os.path.join(output_dir, "docker-compose.yml"), "w") as f:
        f.write(docker_compose_content)
    
    print(f"Created docker-compose.yml in {output_dir}")

def create_dockerfile(output_dir):
    """Create Dockerfile for containerized deployment."""
    dockerfile_content = """FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    gnupg \\
    lsb-release \\
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \\
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \\
    && apt-get update \\
    && apt-get install -y docker-ce-cli docker-compose-plugin \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \\
    libglib2.0-0 \\
    libnss3 \\
    libnspr4 \\
    libatk1.0-0 \\
    libatk-bridge2.0-0 \\
    libcups2 \\
    libdrm2 \\
    libdbus-1-3 \\
    libxcb1 \\
    libxkbcommon0 \\
    libx11-6 \\
    libxcomposite1 \\
    libxdamage1 \\
    libxext6 \\
    libxfixes3 \\
    libxrandr2 \\
    libgbm1 \\
    libpango-1.0-0 \\
    libcairo2 \\
    libasound2 \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN pip install playwright && playwright install

# Copy application files
COPY . .

# Create config directory
RUN mkdir -p /root/.mcp_testing

# Expose ports
EXPOSE 8000 8079 8080 8081 8082

# Run the application
CMD ["python", "mcp_testing_environment.py"]
"""
    
    with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)
    
    print(f"Created Dockerfile in {output_dir}")

def create_init_file(output_dir):
    """Create __init__.py file to make the directory a package."""
    init_content = """#!/usr/bin/env python3

import asyncio
import argparse
import sys
import os
from pathlib import Path

def main():
    from mcp_testing_environment import MCPTestingEnvironment
    
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
                import json
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
        asyncio.run(environment.start(host=args.host, port=args.port))
    except KeyboardInterrupt:
        asyncio.run(environment.stop())

if __name__ == "__main__":
    main()
"""
    
    with open(os.path.join(output_dir, "__init__.py"), "w") as f:
        f.write(init_content)
    
    print(f"Created __init__.py in {output_dir}")

def create_static_directory(output_dir):
    """Create static directory for web assets."""
    static_dir = os.path.join(output_dir, "static")
    os.makedirs(static_dir, exist_ok=True)
    
    # Create a simple CSS file
    css_content = """body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}

h1 {
    color: #333;
}

.component {
    margin-bottom: 20px;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.running {
    background-color: #d4edda;
}

.stopped {
    background-color: #f8d7da;
}

button {
    padding: 5px 10px;
    margin-right: 5px;
}

.actions {
    margin-top: 10px;
}
"""
    
    with open(os.path.join(static_dir, "style.css"), "w") as f:
        f.write(css_content)
    
    print(f"Created static directory with assets in {output_dir}")

def package_solution(source_dir, output_dir):
    """Package the solution for easy deployment."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy Python files
    for py_file in ["mcp_client_simulator.py", "log_aggregator.py", "docker_manager.py", 
                   "webui_tester.py", "mcp_testing_environment.py", "simple_mcp_server.py"]:
        shutil.copy2(os.path.join(source_dir, py_file), os.path.join(output_dir, py_file))
    
    # Copy documentation files
    for md_file in ["documentation.md", "usage_instructions.md"]:
        shutil.copy2(os.path.join(source_dir, md_file), os.path.join(output_dir, md_file))
    
    # Copy architecture diagram
    for diagram_file in ["architecture.png", "architecture.svg"]:
        if os.path.exists(os.path.join(source_dir, diagram_file)):
            shutil.copy2(os.path.join(source_dir, diagram_file), os.path.join(output_dir, diagram_file))
    
    # Create additional files
    create_requirements_file(output_dir)
    create_readme(output_dir)
    create_setup_script(output_dir)
    create_docker_compose(output_dir)
    create_dockerfile(output_dir)
    create_init_file(output_dir)
    create_static_directory(output_dir)
    
    print(f"Solution packaged successfully in {output_dir}")
    
    # Create a zip file
    zip_file = f"{output_dir}.zip"
    shutil.make_archive(output_dir, 'zip', output_dir)
    print(f"Created zip archive at {zip_file}")
    
    return zip_file

def main():
    parser = argparse.ArgumentParser(description="Package MCP Testing Environment for deployment")
    parser.add_argument("--source", default="/home/ubuntu/mcp_testing", help="Source directory containing MCP Testing Environment files")
    parser.add_argument("--output", default="/home/ubuntu/mcp_testing_package", help="Output directory for packaged solution")
    args = parser.parse_args()
    
    zip_file = package_solution(args.source, args.output)
    print(f"Packaging complete. The solution is available at {args.output} and as a zip file at {zip_file}")

if __name__ == "__main__":
    main()
