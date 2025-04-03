#!/usr/bin/env python3

import os

# Create a DOT file for Graphviz
dot_content = """
digraph MCP_Testing_Environment {
    rankdir=TB;
    node [shape=box, style=filled, fontname="Arial", fontsize=12];
    edge [fontname="Arial", fontsize=10];
    
    subgraph cluster_testing_environment {
        label="MCP Testing Environment";
        style=filled;
        color=lightgrey;
        
        // Core Components
        TestingUI [label="Testing Environment UI", fillcolor=lightblue];
        ClientSim [label="MCP Client Simulator", fillcolor=lightgreen];
        LogAggregator [label="Log Aggregation System", fillcolor=lightyellow];
        DockerManager [label="Docker Container Manager", fillcolor=lightpink];
        WebUITester [label="Web UI Testing Component", fillcolor=lightcyan];
        ConfigManager [label="Configuration Manager", fillcolor=lavender];
        
        // Discord-specific components
        DiscordSim [label="Discord API Simulator", fillcolor=palegreen];
        ChannelData [label="Channel Data Manager", fillcolor=peachpuff];
        
        // Connections between components
        TestingUI -> ClientSim;
        TestingUI -> LogAggregator;
        TestingUI -> DockerManager;
        TestingUI -> WebUITester;
        TestingUI -> ConfigManager;
        TestingUI -> DiscordSim;
        TestingUI -> ChannelData;
        
        ClientSim -> LogAggregator [label="Logs"];
        DockerManager -> LogAggregator [label="Container Logs"];
        WebUITester -> LogAggregator [label="Web UI Logs"];
        DiscordSim -> LogAggregator [label="API Logs"];
        
        ConfigManager -> ClientSim [label="Client Config"];
        ConfigManager -> DockerManager [label="Container Config"];
        ConfigManager -> DiscordSim [label="API Config"];
        
        DiscordSim -> ChannelData [dir=both, label="Channel Data"];
        DockerManager -> ChannelData [label="Storage Access"];
    }
    
    // External Components
    MCP_Server [label="MCP Server\n(Discord Integration)", fillcolor=coral];
    Docker_Containers [label="Docker Containers", fillcolor=skyblue];
    Web_UI [label="Web UI", fillcolor=gold];
    
    // Connections to external components
    ClientSim -> MCP_Server [dir=both, label="JSON-RPC"];
    DockerManager -> Docker_Containers [dir=both, label="Docker API"];
    WebUITester -> Web_UI [dir=both, label="Browser Automation"];
    MCP_Server -> Docker_Containers [dir=both, label="Container API"];
    Docker_Containers -> Web_UI [label="Serves"];
}
"""

# Write the DOT file
with open('/home/ubuntu/mcp_testing/architecture.dot', 'w') as f:
    f.write(dot_content)

# Generate the diagram as PNG
os.system('dot -Tpng /home/ubuntu/mcp_testing/architecture.dot -o /home/ubuntu/mcp_testing/architecture.png')

# Generate the diagram as SVG for better quality
os.system('dot -Tsvg /home/ubuntu/mcp_testing/architecture.dot -o /home/ubuntu/mcp_testing/architecture.svg')

print("Architecture diagram generated as architecture.png and architecture.svg")
