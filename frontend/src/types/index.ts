export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  is_superuser: boolean;
  organizations?: Array<{
    id: string;
    name: string;
    slug: string;
    role: string | null;
  }>;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface BrainItem {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  created_at: string;
  sources_count: number;
  documents_count: number;
  assigned_roles: string[];
}

export interface DataSource {
  id: string;
  organization_id: string;
  brain_id?: string;
  name: string;
  type: string;
  description?: string;
  is_active: boolean;
  is_read_only: boolean;
  created_at: string;
}

export interface DataSourceColumn {
  name: string;
  data_type: string;
  is_nullable: boolean;
  is_primary_key: boolean;
}

export interface DataSourceTable {
  id: string;
  table_name: string;
  row_count: number;
  columns: DataSourceColumn[];
}

export interface DocumentItem {
  id: string;
  organization_id?: string;
  brain_id?: string;
  title: string;
  file_name: string;
  file_type: string;
  file_size: number;
  status: string;
  chunk_count: number;
  error_message?: string;
  created_at: string;
}

export interface AIProviderItem {
  id: string;
  name: string;
  provider_type: string;
  base_url?: string;
  is_active: boolean;
}

export interface PolicyRule {
  id: string;
  role_id?: string;
  resource_type: string;
  resource_name: string;
  effect: string;
  row_filter_expr?: string;
  allowed_columns?: string[];
  data_masking_rule?: string;
}

export interface PolicyItem {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  rules: PolicyRule[];
}

export interface RoleItem {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  is_system: boolean;
  permissions: string[];
}

export interface MCPServerItem {
  id: string;
  name: string;
  description?: string;
  transport_type: string;
  endpoint_url?: string;
  status: string;
  tools: Array<{
    id: string;
    name: string;
    description?: string;
    input_schema: any;
    is_approved: boolean;
  }>;
}

export interface Conversation {
  id: string;
  title: string;
  brain_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: string;
  sender: "USER" | "ASSISTANT" | "SYSTEM";
  content: string;
  reasoning_summary?: string;
  tool_calls: string[];
  citations: string[];
  created_at: string;
}

export interface ReportItem {
  id: string;
  title: string;
  summary?: string;
  content_markdown: string;
  data_sources: string[];
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  action: string;
  user_id?: string;
  resource_type?: string;
  resource_id?: string;
  status: string;
  created_at: string;
  metadata: Record<string, any>;
}
