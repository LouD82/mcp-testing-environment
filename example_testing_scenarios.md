# Example Testing Scenarios

This document provides concrete examples of how to test MCP servers using a human-first, functional testing approach. These scenarios demonstrate how to start with user-like interactions rather than code inspection.

## Discord MCP Server Testing Examples

### Scenario 1: General Information Retrieval

**User Query:**
"Has anything been said about Manus and Discord recently?"

**Expected Testing Flow:**
1. Start the MCP Testing Environment
2. Configure the Discord MCP server
3. Use the MCP Client Simulator to send the query
4. Observe the server's response:
   - Does it correctly search for mentions of "Manus" and "Discord"?
   - Does it return relevant messages?
   - Does it provide proper context for the messages?
   - Is the response time reasonable?
5. Only if issues are found, check logs and code

**Example Interaction:**
```
User: "Has anything been said about Manus and Discord recently?"

Expected MCP Server Process:
1. Parse query to identify topics "Manus" and "Discord"
2. Search through Discord channel data for relevant messages
3. Retrieve and format matching messages with context
4. Return a summary of discussions

Expected Response:
"I found several recent mentions of Manus and Discord:
- In #general yesterday, user123 said: 'The Manus team is doing great work on Discord integration'
- In #development 3 days ago, user456 discussed: 'We should look at how Manus handles Discord permissions'
..."
```

### Scenario 2: Channel Activity Summary

**User Query:**
"What were the most active discussions in the development channel last week?"

**Expected Testing Flow:**
1. Start the MCP Testing Environment
2. Configure the Discord MCP server
3. Use the MCP Client Simulator to send the query
4. Observe the server's response:
   - Does it correctly identify the development channel?
   - Does it properly filter for last week's timeframe?
   - Does it identify and summarize active discussion threads?
   - Are the summaries accurate and helpful?
5. Only if issues are found, check logs and code

**Example Interaction:**
```
User: "What were the most active discussions in the development channel last week?"

Expected MCP Server Process:
1. Identify the "development" channel
2. Filter messages from the past week
3. Group messages into conversation threads
4. Identify threads with most activity
5. Generate summaries of top discussions

Expected Response:
"Last week in #development, the most active discussions were:
1. MCP Protocol Updates (23 messages): Discussion about the latest changes to the protocol specification, focusing on new capabilities for resource handling.
2. Docker Integration Issues (18 messages): Troubleshooting session about container networking problems with the Discord integration.
3. Web UI Improvements (15 messages): Ideas for enhancing the channel visualization interface with better filtering options.
..."
```

### Scenario 3: User Contribution Analysis

**User Query:**
"Who are the top contributors in the project channels this month?"

**Expected Testing Flow:**
1. Start the MCP Testing Environment
2. Configure the Discord MCP server
3. Use the MCP Client Simulator to send the query
4. Observe the server's response:
   - Does it correctly identify project-related channels?
   - Does it properly filter for this month's timeframe?
   - Does it accurately count and rank user contributions?
   - Is the presentation of contributors clear and informative?
5. Only if issues are found, check logs and code

**Example Interaction:**
```
User: "Who are the top contributors in the project channels this month?"

Expected MCP Server Process:
1. Identify project-related channels
2. Filter messages from the current month
3. Count messages per user
4. Analyze contribution patterns
5. Rank users by contribution

Expected Response:
"This month's top contributors in project channels are:
1. user123 (45 messages): Most active in #backend-dev and #architecture
2. user456 (37 messages): Primarily contributing to #frontend and #design
3. user789 (29 messages): Leading discussions in #testing and #deployment
..."
```

## Web UI Testing Examples

### Scenario 1: Channel Visualization Testing

**User Action:**
Navigate to the channel visualization page and explore the data for a specific channel

**Expected Testing Flow:**
1. Start the MCP Testing Environment
2. Configure the Discord MCP server and web UI
3. Use the Web UI Testing Component to navigate to the visualization page
4. Test user interactions:
   - Can you select different channels?
   - Does the visualization load correctly?
   - Can you filter by date ranges?
   - Do interactive elements work as expected?
5. Only if issues are found, check logs and code

**Example Interaction:**
```
User Actions:
1. Navigate to http://localhost:3000/visualization
2. Select "#general" from the channel dropdown
3. Set date range to "Last 7 days"
4. Click on "Activity Heatmap" view

Expected Web UI Behavior:
1. Load the visualization page
2. Update channel selection to #general
3. Filter data to show only the last 7 days
4. Display an activity heatmap showing message frequency by hour/day

Expected Result:
A clear heatmap visualization showing when #general was most active during the past week, with interactive tooltips showing message counts when hovering over cells.
```

### Scenario 2: Search Functionality Testing

**User Action:**
Use the search feature to find messages containing specific keywords

**Expected Testing Flow:**
1. Start the MCP Testing Environment
2. Configure the Discord MCP server and web UI
3. Use the Web UI Testing Component to navigate to the search page
4. Test search functionality:
   - Can you enter search terms?
   - Does the search return relevant results?
   - Can you filter results by channel, date, or user?
   - Is the pagination working correctly?
5. Only if issues are found, check logs and code

**Example Interaction:**
```
User Actions:
1. Navigate to http://localhost:3000/search
2. Enter "protocol update" in the search box
3. Filter to only show results from #development channel
4. Sort results by date (newest first)

Expected Web UI Behavior:
1. Load the search page
2. Process the search query "protocol update"
3. Apply the channel filter for #development
4. Sort matching messages by date
5. Display paginated results

Expected Result:
A list of messages containing "protocol update" from the #development channel, sorted with newest messages first, with proper pagination controls and highlighting of the search terms in the results.
```

## MCP Client Simulator Examples

### Example 1: Simple Query Testing

```python
from mcp_client_simulator import MCPClientSimulator

# Initialize the simulator
client = MCPClientSimulator(server_url="http://localhost:8000")

# Connect to the MCP server
client.connect()

# Send a user-like query
response = client.send_query("What were the main topics discussed in the general channel yesterday?")

# Print the response
print(response)

# Analyze the response quality
client.analyze_response(response, expected_topics=["general channel", "yesterday", "discussion topics"])
```

### Example 2: Conversation Flow Testing

```python
from mcp_client_simulator import MCPClientSimulator

# Initialize the simulator
client = MCPClientSimulator(server_url="http://localhost:8000")

# Connect to the MCP server
client.connect()

# Simulate a conversation flow
conversation = [
    "Hello, I'd like to know about recent discussions on the MCP protocol.",
    "Can you tell me more about the changes mentioned by user123?",
    "Were there any objections to those changes?",
    "Thanks, can you summarize the consensus reached?"
]

# Send each message in sequence
for message in conversation:
    print(f"User: {message}")
    response = client.send_query(message)
    print(f"Server: {response}")
    print("---")
    
    # Allow time for context to be maintained
    import time
    time.sleep(1)

# Analyze the conversation quality
client.analyze_conversation_coherence()
```

### Example 3: Comparative Testing

```python
from mcp_client_simulator import MCPClientSimulator

# Initialize simulators for two different server versions
client_v1 = MCPClientSimulator(server_url="http://localhost:8000", version="v1")
client_v2 = MCPClientSimulator(server_url="http://localhost:8001", version="v2")

# Connect to both servers
client_v1.connect()
client_v2.connect()

# Test queries on both servers
test_queries = [
    "What happened in the project meeting yesterday?",
    "Who contributed the most to the frontend code this month?",
    "Can you summarize the discussion about authentication methods?"
]

# Compare responses
for query in test_queries:
    print(f"Query: {query}")
    
    response_v1 = client_v1.send_query(query)
    response_v2 = client_v2.send_query(query)
    
    print(f"V1 Response: {response_v1}")
    print(f"V2 Response: {response_v2}")
    
    # Compare response quality
    comparison = client_v1.compare_responses(response_v1, response_v2)
    print(f"Comparison: {comparison}")
    print("---")
```

## Conclusion

These example scenarios demonstrate how to approach MCP server testing from a human-first, functional perspective. By starting with user-like interactions and focusing on the quality of responses and experiences, you can identify issues that matter most to users before diving into technical details.

Remember to always:
1. Start with realistic user queries and actions
2. Evaluate responses from a user's perspective
3. Only investigate code and logs after identifying functional issues
4. Verify fixes by returning to functional testing

This approach ensures that your testing focuses on what matters most: the actual user experience.
