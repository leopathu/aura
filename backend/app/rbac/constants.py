SYSTEM_PERMISSIONS = [
    # Data Sources
    {"code": "source.read", "name": "Read Data Sources", "category": "source", "description": "View configured data sources and schemas"},
    {"code": "source.create", "name": "Create Data Sources", "category": "source", "description": "Add new data sources"},
    {"code": "source.update", "name": "Update Data Sources", "category": "source", "description": "Edit data source configurations"},
    {"code": "source.delete", "name": "Delete Data Sources", "category": "source", "description": "Remove data sources"},

    # Documents & Knowledge
    {"code": "document.read", "name": "Read Documents", "category": "document", "description": "View and search uploaded documents"},
    {"code": "document.upload", "name": "Upload Documents", "category": "document", "description": "Upload and index new documents"},
    {"code": "document.delete", "name": "Delete Documents", "category": "document", "description": "Remove indexed documents"},

    # Database
    {"code": "database.read", "name": "Inspect Database Schema", "category": "database", "description": "View database tables and columns"},
    {"code": "database.query", "name": "Execute Read-Only Queries", "category": "database", "description": "Execute approved SELECT queries"},

    # Reports
    {"code": "report.view", "name": "View Reports", "category": "report", "description": "View generated reports and exports"},
    {"code": "report.create", "name": "Create Reports", "category": "report", "description": "Generate new reports and artifacts"},

    # MCP
    {"code": "mcp.use", "name": "Use MCP Tools", "category": "mcp", "description": "Invoke approved MCP server tools"},
    {"code": "mcp.manage", "name": "Manage MCP Servers", "category": "mcp", "description": "Register and approve MCP tools"},

    # Web
    {"code": "web.search", "name": "Web Search", "category": "web", "description": "Perform web lookups and crawl sites"},

    # Agent
    {"code": "agent.execute", "name": "Execute Agent", "category": "agent", "description": "Run AI agent chat and reasoning workflows"},

    # Admin
    {"code": "admin.users", "name": "Manage Users", "category": "admin", "description": "Invite and manage organization users"},
    {"code": "admin.roles", "name": "Manage Roles", "category": "admin", "description": "Create and edit custom roles and permissions"},
    {"code": "admin.models", "name": "Manage AI Models", "category": "admin", "description": "Configure AI providers and model settings"},
    {"code": "admin.policies", "name": "Manage Policies", "category": "admin", "description": "Configure table, column, and row security policies"},
    {"code": "admin.audit", "name": "View Audit Logs", "category": "admin", "description": "View system compliance and audit trails"},
]

DEFAULT_ROLE_DEFINITIONS = {
    "Organization Admin": [p["code"] for p in SYSTEM_PERMISSIONS],
    "Data Admin": [
        "source.read", "source.create", "source.update", "source.delete",
        "document.read", "document.upload", "document.delete",
        "database.read", "database.query",
        "report.view", "report.create",
        "mcp.use", "mcp.manage",
        "web.search", "agent.execute",
    ],
    "Analyst": [
        "source.read", "document.read", "database.read", "database.query",
        "report.view", "report.create", "web.search", "agent.execute", "mcp.use"
    ],
    "User": [
        "document.read", "report.view", "web.search", "agent.execute"
    ],
    "Viewer": [
        "document.read", "report.view"
    ]
}
