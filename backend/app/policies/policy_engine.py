from typing import List, Dict, Any, Set, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Policy, PolicyRule, OrganizationUser, Role
from app.policies.sql_validator import SQLSecurityLayer, SQLValidationError

class PolicyEvaluationResult:
    def __init__(
        self,
        allowed: bool,
        reason: Optional[str] = None,
        rewritten_sql: Optional[str] = None,
        masking_rules: Optional[Dict[str, str]] = None
    ):
        self.allowed = allowed
        self.reason = reason
        self.rewritten_sql = rewritten_sql
        self.masking_rules = masking_rules or {}

class PolicyEngine:
    @staticmethod
    async def get_user_role_id(db: AsyncSession, user_id: str, organization_id: str) -> Optional[str]:
        stmt = select(OrganizationUser.role_id).where(
            OrganizationUser.user_id == user_id,
            OrganizationUser.organization_id == organization_id,
            OrganizationUser.status == "ACTIVE"
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def evaluate_sql_query(
        db: AsyncSession,
        organization_id: str,
        user_id: str,
        raw_sql: str
    ) -> PolicyEvaluationResult:
        """
        Validates SQL AST, checks table/column permissions against active policies,
        injects row filters, and returns rewritten safe SQL with masking instructions.
        """
        # 1. AST Safety & Parse
        try:
            expression, tables, columns = SQLSecurityLayer.parse_and_validate(raw_sql)
        except SQLValidationError as e:
            return PolicyEvaluationResult(allowed=False, reason=str(e))

        role_id = await PolicyEngine.get_user_role_id(db, user_id, organization_id)

        # 2. Fetch active policies and rules for this organization
        stmt = (
            select(PolicyRule)
            .join(Policy, Policy.id == PolicyRule.policy_id)
            .where(
                Policy.organization_id == organization_id,
                Policy.is_active == True,
                (PolicyRule.role_id == None) | (PolicyRule.role_id == role_id)
            )
        )
        res = await db.execute(stmt)
        rules = res.scalars().all()

        row_filters: List[str] = []
        masking_rules: Dict[str, str] = {}

        # 3. Check table and column permissions
        for rule in rules:
            target_res = rule.resource_name.lower()
            
            # Check Table Denials
            if rule.resource_type == "TABLE" and rule.effect == "DENY":
                if target_res in tables or target_res == "*":
                    return PolicyEvaluationResult(
                        allowed=False,
                        reason=f"Access denied by security policy for table: '{target_res}'"
                    )

            # Check Column Denials
            if rule.resource_type == "COLUMN" and rule.effect == "DENY":
                if target_res in columns:
                    return PolicyEvaluationResult(
                        allowed=False,
                        reason=f"Access denied by security policy for column: '{target_res}'"
                    )

            # Check Table Allowed Columns restriction
            if rule.resource_type == "TABLE" and rule.allowed_columns:
                if target_res in tables:
                    allowed_col_set = {c.lower() for c in rule.allowed_columns}
                    for col in columns:
                        if col not in allowed_col_set and col != "*":
                            return PolicyEvaluationResult(
                                allowed=False,
                                reason=f"Column '{col}' on table '{target_res}' is not permitted by data policy."
                            )

            # Collect Row Filters
            if rule.row_filter_expr and (target_res in tables or target_res == "*"):
                row_filters.append(rule.row_filter_expr)

            # Collect Data Masking Rules
            if rule.data_masking_rule:
                masking_rules[target_res] = rule.data_masking_rule

        # 4. Rewrite SQL with row filters and limits
        rewritten_sql = SQLSecurityLayer.enforce_limits_and_safety(
            expression,
            row_filters=row_filters
        )

        return PolicyEvaluationResult(
            allowed=True,
            rewritten_sql=rewritten_sql,
            masking_rules=masking_rules
        )

    @staticmethod
    def apply_data_masking(rows: List[Dict[str, Any]], masking_rules: Dict[str, str]) -> List[Dict[str, Any]]:
        """Applies configured masking rules (REDACT, MASK_EMAIL, MASK_NUMERIC) to result rows."""
        if not masking_rules or not rows:
            return rows

        masked_results = []
        for row in rows:
            new_row = dict(row)
            for col_name, val in row.items():
                rule = masking_rules.get(col_name.lower())
                if rule and val is not None:
                    if rule == "REDACT":
                        new_row[col_name] = "[REDACTED]"
                    elif rule == "MASK_EMAIL":
                        s = str(val)
                        if "@" in s:
                            parts = s.split("@")
                            masked_prefix = parts[0][:2] + "***" if len(parts[0]) > 2 else "***"
                            new_row[col_name] = f"{masked_prefix}@{parts[1]}"
                    elif rule == "MASK_NUMERIC":
                        new_row[col_name] = "***"
            masked_results.append(new_row)
        return masked_results
