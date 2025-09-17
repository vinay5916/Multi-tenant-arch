aviation_agents/
├── main.py                      # Main application entry point
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py             # Global configuration
│   └── tenant_config.py        # Tenant-specific configurations
├── base_agent/
│   ├── __init__.py
│   ├── coordinator.py          # Master coordination agent
│   └── models.py               # Base models
├── mcp_servers/
│   ├── __init__.py
│   ├── hr_server/              # HR Helper MCP Server
│   ├── supply_chain_server/    # Supply Chain MCP Server
│   ├── security_server/        # Secure Coding MCP Server
│   ├── hire_chat_server/       # Hire Chat MCP Server
│   ├── meeting_server/         # Meeting Room MCP Server
│   ├── maintenance_server/     # Aircraft Maintenance MCP Server
│   ├── flight_ops_server/      # Flight Operations MCP Server
│   └── compliance_server/      # Aviation Compliance MCP Server
├── agents/
│   ├── __init__.py
│   ├── hr_agent/              # HR Assistant Agent
│   ├── supply_chain_agent/    # Supply Chain Agent
│   ├── security_agent/        # Security Coding Agent
│   ├── hire_chat_agent/       # Hiring Assistant Agent
│   ├── meeting_agent/         # Meeting Room Agent
│   ├── maintenance_agent/     # Maintenance Agent
│   ├── flight_ops_agent/      # Flight Operations Agent
│   └── compliance_agent/      # Compliance Agent
├── shared/
│   ├── __init__.py
│   ├── database.py            # Database connections
│   ├── auth.py                # Authentication utilities
│   └── utils.py               # Common utilities
└── web/
    ├── __init__.py
    ├── api.py                 # FastAPI endpoints
    └── static/                # Web assets