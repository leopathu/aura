import time
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import DataSource, DataSourceCredential, Report
from app.connectors.factory import get_data_connector
from app.policies.policy_engine import PolicyEngine
from app.rag.retriever import DocumentRetriever
from app.mcp.service import MCPService
from app.tools.base import BaseTool, ToolDefinition, ToolResultContainer
from app.rbac.service import RBACService

class DatabaseQueryTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="query_database",
            description="Execute a safe, read-only SQL query against an organization database.",
            input_schema={
                "type": "object",
                "properties": {
                    "source_id": {"type": "string", "description": "ID of the target data source"},
                    "sql_query": {"type": "string", "description": "SELECT SQL query"}
                },
                "required": ["source_id", "sql_query"]
            },
            required_permissions=["database.query"],
            resource_type="DATABASE"
        )

    async def execute(self, context: Dict[str, Any], **kwargs: Any) -> ToolResultContainer:
        db: AsyncSession = context["db"]
        user_id: str = context["user_id"]
        organization_id: str = context["organization_id"]
        source_id: str = kwargs.get("source_id", "")
        raw_sql: str = kwargs.get("sql_query", "")

        # 1. Fetch data source
        res = await db.execute(
            select(DataSource, DataSourceCredential)
            .join(DataSourceCredential, DataSourceCredential.data_source_id == DataSource.id)
            .where(DataSource.id == source_id, DataSource.organization_id == organization_id)
        )
        row = res.first()
        if not row:
            return ToolResultContainer(success=False, data=None, error="Data source not found.")
        source, cred = row

        # 2. Evaluate against Security & Policy Layer
        policy_eval = await PolicyEngine.evaluate_sql_query(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            raw_sql=raw_sql
        )
        if not policy_eval.allowed:
            return ToolResultContainer(
                success=False,
                data=None,
                error=f"Security Policy Denied: {policy_eval.reason}"
            )

        # 3. Execute query via connector
        start_time = time.time()
        connector = get_data_connector(source, cred)
        try:
            raw_rows = await connector.execute_query(policy_eval.rewritten_sql)
            # 4. Apply data masking rules
            masked_rows = PolicyEngine.apply_data_masking(raw_rows, policy_eval.masking_rules)
            exec_ms = int((time.time() - start_time) * 1000)

            citation = f"Data Source: {source.name} ({source.type}) → {len(masked_rows)} rows returned"
            return ToolResultContainer(
                success=True,
                data=masked_rows,
                citations=[citation],
                metadata={
                    "sql_executed": policy_eval.rewritten_sql,
                    "execution_time_ms": exec_ms,
                    "row_count": len(masked_rows)
                }
            )
        except Exception as e:
            return ToolResultContainer(success=False, data=None, error=f"Database Execution Error: {str(e)}")
        finally:
            await connector.close()


class DatabaseSchemaTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="inspect_database_schema",
            description="Inspect tables and columns available in a data source.",
            input_schema={
                "type": "object",
                "properties": {
                    "source_id": {"type": "string", "description": "ID of the target data source"}
                },
                "required": ["source_id"]
            },
            required_permissions=["database.read"],
            resource_type="DATABASE"
        )

    async def execute(self, context: Dict[str, Any], **kwargs: Any) -> ToolResultContainer:
        db: AsyncSession = context["db"]
        organization_id: str = context["organization_id"]
        source_id: str = kwargs.get("source_id", "")

        res = await db.execute(
            select(DataSource, DataSourceCredential)
            .join(DataSourceCredential, DataSourceCredential.data_source_id == DataSource.id)
            .where(DataSource.id == source_id, DataSource.organization_id == organization_id)
        )
        row = res.first()
        if not row:
            return ToolResultContainer(success=False, data=None, error="Data source not found.")
        source, cred = row

        connector = get_data_connector(source, cred)
        try:
            tables = await connector.discover_schema()
            return ToolResultContainer(
                success=True,
                data=[t.to_dict() for t in tables],
                citations=[f"Data Source: {source.name} Schema"]
            )
        except Exception as e:
            return ToolResultContainer(success=False, data=None, error=str(e))
        finally:
            await connector.close()


class DocumentSearchTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_documents",
            description="Search the organization knowledge base, documents, and files for answers with citations.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Semantic search query or question"},
                    "top_k": {"type": "integer", "description": "Number of chunks to retrieve", "default": 4}
                },
                "required": ["query"]
            },
            required_permissions=["document.read"],
            resource_type="DOCUMENT"
        )

    async def execute(self, context: Dict[str, Any], **kwargs: Any) -> ToolResultContainer:
        db: AsyncSession = context["db"]
        organization_id: str = context["organization_id"]
        query: str = kwargs.get("query", "")
        top_k: int = kwargs.get("top_k", 4)

        try:
            results = await DocumentRetriever.search(
                db=db,
                organization_id=organization_id,
                query=query,
                top_k=top_k
            )
            citations = [r.citation for r in results]
            data = [r.to_dict() for r in results]
            return ToolResultContainer(success=True, data=data, citations=citations)
        except Exception as e:
            return ToolResultContainer(success=False, data=None, error=str(e))


class ReportGeneratorTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="generate_report",
            description="Generate a first-class structured report artifact with findings, tables, and citations.",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Report title"},
                    "summary": {"type": "string", "description": "Executive summary"},
                    "content_markdown": {"type": "string", "description": "Full markdown report content"},
                    "data_sources": {"type": "array", "items": {"type": "string"}, "description": "Sources referenced"}
                },
                "required": ["title", "content_markdown"]
            },
            required_permissions=["report.create"],
            resource_type="REPORT"
        )

    async def execute(self, context: Dict[str, Any], **kwargs: Any) -> ToolResultContainer:
        db: AsyncSession = context["db"]
        user_id: str = context["user_id"]
        organization_id: str = context["organization_id"]

        title = kwargs.get("title", "Generated Analysis Report")
        summary = kwargs.get("summary", "")
        content = kwargs.get("content_markdown", "")
        sources = kwargs.get("data_sources", [])

        report = Report(
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            summary=summary,
            content_markdown=content,
            data_sources_json=sources
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        return ToolResultContainer(
            success=True,
            data={
                "report_id": report.id,
                "title": report.title,
                "created_at": report.created_at.isoformat()
            },
            citations=[f"Report Generated: {report.title}"]
        )


class WebSearchTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_search",
            description="Search external web knowledge and articles.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Web search query"}
                },
                "required": ["query"]
            },
            required_permissions=["web.search"],
            resource_type="WEB"
        )

    async def execute(self, context: Dict[str, Any], **kwargs: Any) -> ToolResultContainer:
        query = kwargs.get("query", "")
        # Simulated search result for offline/enterprise environments
        return ToolResultContainer(
            success=True,
            data={
                "query": query,
                "summary": f"Web results for query: {query}",
                "snippets": [
                    {"title": f"Industry insights on {query}", "url": "https://example.com/insights", "snippet": "Latest industry trends and benchmarks for modern data platforms."}
                ]
            },
            citations=[f"Web: https://example.com/insights ({query})"]
        )


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self.register(DatabaseQueryTool())
        self.register(DatabaseSchemaTool())
        self.register(DocumentSearchTool())
        self.register(ReportGeneratorTool())
        self.register(WebSearchTool())

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.definition.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    async def get_allowed_tools_for_user(
        self,
        db: AsyncSession,
        user_id: str,
        organization_id: str
    ) -> List[ToolDefinition]:
        """Filters available tools to only those the user's role has permission to invoke."""
        user_perms = await RBACService.get_user_permissions(db, user_id, organization_id)
        allowed: List[ToolDefinition] = []

        for tool in self._tools.values():
            # Check if all required permissions are held by the user
            if all(perm in user_perms for perm in tool.definition.required_permissions):
                allowed.append(tool.definition)

        return allowed

tool_registry = ToolRegistry()
