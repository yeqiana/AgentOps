"""
Runtime configuration service.

What this is:
- An application-layer service for runtime policy overrides.

What it does:
- Reads database-backed configuration overrides.
- Merges them with environment-based defaults.
- Exposes stable effective workflow and security configuration snapshots.

Why this is done this way:
- Stage-2 configuration governance should stop depending only on process
  environment variables.
- A dedicated service keeps parsing and fallback rules out of API handlers,
  workflow nodes, and tool registries.
"""

from __future__ import annotations

import json
from typing import Any

from app.domain.errors import ValidationError

from app.config import (
    get_allowed_tools,
    get_workflow_executor_role_instruction,
    get_workflow_executor_role_name,
    get_workflow_execution_mode,
    get_workflow_planner_role_instruction,
    get_workflow_planner_role_name,
    get_workflow_reviewer_role_instruction,
    get_workflow_reviewer_role_name,
    is_recovery_llm_degrade_to_mock_enabled,
    is_recovery_tool_soft_fail_enabled,
    get_upload_allowed_kinds,
    get_upload_max_bytes,
    get_workflow_arbitration_role_instruction,
    get_workflow_arbitration_role_name,
    get_workflow_critic_role_instruction,
    get_workflow_critic_role_name,
    get_workflow_challenge_role_instruction,
    get_workflow_challenge_role_name,
    get_workflow_deliberation_keywords,
    get_workflow_support_role_instruction,
    get_workflow_support_role_name,
    is_auth_enabled,
    is_idempotency_enabled,
    is_rate_limit_enabled,
    is_workflow_deliberation_enabled,
)
from app.domain.models import RuntimeConfigRecord
from app.infrastructure.persistence.repositories import SQLiteRuntimeConfigRepository


class RuntimeConfigService:
    """
    What this is:
    - The orchestration-facing runtime configuration center.

    What it does:
    - Loads persisted overrides from `sys_runtime_config`.
    - Provides typed effective config values for workflow and security domains.

    Why this is done this way:
    - Runtime configuration needs one place that knows override precedence and
      value parsing; otherwise different layers would drift.
    """

    def __init__(self, repository: SQLiteRuntimeConfigRepository | None = None) -> None:
        self.repository = repository or SQLiteRuntimeConfigRepository()

    def list_configs(self, *, scope: str | None = None) -> list[RuntimeConfigRecord]:
        return self.repository.list_configs(scope=scope)

    def list_config_events(
        self,
        *,
        scope: str | None = None,
        key: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        return self.repository.list_config_events(
            scope=scope,
            key=key,
            limit=limit,
            offset=offset,
        )

    def get_latest_routing_config_version(self) -> dict[str, Any] | None:
        record = self.repository.get_latest_routing_config_version()
        return self._to_routing_config_version_payload(record) if record else None

    def list_routing_config_versions(self, *, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        return [
            self._to_routing_config_version_payload(record)
            for record in self.repository.list_routing_config_versions(limit=limit, offset=offset)
        ]

    def diff_routing_config_versions(self, *, from_version: int, to_version: int) -> dict[str, Any]:
        from_record = self.repository.get_routing_config_version(version_no=from_version)
        if not from_record:
            raise ValidationError(f"routing 配置版本 `{from_version}` 不存在。")
        to_record = self.repository.get_routing_config_version(version_no=to_version)
        if not to_record:
            raise ValidationError(f"routing 配置版本 `{to_version}` 不存在。")

        from_snapshot = json.loads(from_record["snapshot_json"])
        to_snapshot = json.loads(to_record["snapshot_json"])
        from_flat = self._flatten_routing_snapshot(from_snapshot)
        to_flat = self._flatten_routing_snapshot(to_snapshot)
        diff_items: list[dict[str, str]] = []
        for field_path in sorted(set(from_flat) | set(to_flat)):
            before_value = from_flat.get(field_path, "")
            after_value = to_flat.get(field_path, "")
            if before_value != after_value:
                diff_items.append(
                    {
                        "field_path": field_path,
                        "before_value": before_value,
                        "after_value": after_value,
                    }
                )
        return {
            "from_version": from_version,
            "to_version": to_version,
            "diff_items": diff_items,
        }

    def restore_routing_config_version(self, *, version_no: int, updated_by: str) -> dict[str, Any]:
        record = self.repository.get_routing_config_version(version_no=version_no)
        if not record:
            raise ValidationError(f"routing 配置版本 `{version_no}` 不存在。")

        snapshot = json.loads(record["snapshot_json"])
        configs = self._routing_snapshot_to_config_items(snapshot)
        self.repository.replace_scope_configs(
            scope="routing",
            configs=configs,
            updated_by=updated_by,
            description=f"restore from routing version {version_no}",
        )
        self.repository.create_routing_config_version(
            snapshot=snapshot,
            changed_key=f"restore:{version_no}",
            changed_value=str(version_no),
            change_action="restore",
            updated_by=updated_by,
        )
        latest = self.get_latest_routing_config_version()
        return {
            "restored_from_version": version_no,
            "current_version": latest["version_no"] if latest else None,
            "snapshot": snapshot,
        }

    def upsert_config(
        self,
        *,
        scope: str,
        key: str,
        value: str,
        value_type: str,
        description: str,
        updated_by: str,
    ) -> RuntimeConfigRecord:
        item = self.repository.upsert_config(
            scope=scope,
            key=key,
            value=value,
            value_type=value_type,
            description=description,
            updated_by=updated_by,
        )
        if scope.strip().lower() == "routing":
            self.repository.create_routing_config_version(
                snapshot=self.get_routing_config_snapshot(),
                changed_key=key,
                changed_value=value,
                change_action="upsert",
                updated_by=updated_by,
            )
        return item

    def validate_config_entry(self, *, scope: str, key: str, value: str, value_type: str) -> None:
        normalized_scope = scope.strip().lower()
        if normalized_scope != "routing":
            return

        normalized_key = key.strip()
        normalized_value_type = (value_type or "str").strip().lower()
        definitions = self.get_routing_config_template()
        definition = definitions.get(normalized_key)
        if not definition:
            raise ValidationError(f"routing 配置项 `{normalized_key}` 不存在。")

        expected_type = definition["value_type"]
        if normalized_value_type != expected_type:
            raise ValidationError(f"routing 配置项 `{normalized_key}` 只允许 `{expected_type}` 类型。")

        self._validate_typed_value(
            key=normalized_key,
            value=value,
            value_type=normalized_value_type,
        )

    def get_effective_workflow_config(self) -> dict[str, Any]:
        overrides = self._load_scope_overrides("workflow")
        return {
            "execution_mode": self._as_str(
                overrides.get("execution_mode"),
                get_workflow_execution_mode(),
            ),
            "deliberation_enabled": self._as_bool(
                overrides.get("deliberation_enabled"),
                is_workflow_deliberation_enabled(),
            ),
            "deliberation_keywords": self._as_csv(
                overrides.get("deliberation_keywords"),
                get_workflow_deliberation_keywords(),
            ),
            "support_role_name": self._as_str(
                overrides.get("support_role_name"),
                get_workflow_support_role_name(),
            ),
            "support_role_instruction": self._as_str(
                overrides.get("support_role_instruction"),
                get_workflow_support_role_instruction(),
            ),
            "challenge_role_name": self._as_str(
                overrides.get("challenge_role_name"),
                get_workflow_challenge_role_name(),
            ),
            "challenge_role_instruction": self._as_str(
                overrides.get("challenge_role_instruction"),
                get_workflow_challenge_role_instruction(),
            ),
            "planner_role_name": self._as_str(
                overrides.get("planner_role_name"),
                get_workflow_planner_role_name(),
            ),
            "planner_role_instruction": self._as_str(
                overrides.get("planner_role_instruction"),
                get_workflow_planner_role_instruction(),
            ),
            "executor_role_name": self._as_str(
                overrides.get("executor_role_name"),
                get_workflow_executor_role_name(),
            ),
            "executor_role_instruction": self._as_str(
                overrides.get("executor_role_instruction"),
                get_workflow_executor_role_instruction(),
            ),
            "arbitration_role_name": self._as_str(
                overrides.get("arbitration_role_name"),
                get_workflow_arbitration_role_name(),
            ),
            "arbitration_role_instruction": self._as_str(
                overrides.get("arbitration_role_instruction"),
                get_workflow_arbitration_role_instruction(),
            ),
            "critic_role_name": self._as_str(
                overrides.get("critic_role_name"),
                get_workflow_critic_role_name(),
            ),
            "critic_role_instruction": self._as_str(
                overrides.get("critic_role_instruction"),
                get_workflow_critic_role_instruction(),
            ),
            "reviewer_role_name": self._as_str(
                overrides.get("reviewer_role_name"),
                get_workflow_reviewer_role_name(),
            ),
            "reviewer_role_instruction": self._as_str(
                overrides.get("reviewer_role_instruction"),
                get_workflow_reviewer_role_instruction(),
            ),
        }

    def get_workflow_role_overrides(self) -> dict[str, str | None]:
        """
        What this is:
        - A narrow workflow-role override snapshot.

        What it does:
        - Returns only the role-related keys stored in `sys_runtime_config`.
        - Does not apply environment defaults.

        Why this is done this way:
        - Workflow role master data now lives in `sys_workflow_role`.
        - Runtime config should only override that master data when an explicit
          database override exists, otherwise role-table values must remain
          visible to orchestration and API queries.
        """

        overrides = self._load_scope_overrides("workflow")
        return {
            "support_role_name": overrides.get("support_role_name"),
            "support_role_instruction": overrides.get("support_role_instruction"),
            "challenge_role_name": overrides.get("challenge_role_name"),
            "challenge_role_instruction": overrides.get("challenge_role_instruction"),
            "planner_role_name": overrides.get("planner_role_name"),
            "planner_role_instruction": overrides.get("planner_role_instruction"),
            "executor_role_name": overrides.get("executor_role_name"),
            "executor_role_instruction": overrides.get("executor_role_instruction"),
            "arbitration_role_name": overrides.get("arbitration_role_name"),
            "arbitration_role_instruction": overrides.get("arbitration_role_instruction"),
            "critic_role_name": overrides.get("critic_role_name"),
            "critic_role_instruction": overrides.get("critic_role_instruction"),
            "reviewer_role_name": overrides.get("reviewer_role_name"),
            "reviewer_role_instruction": overrides.get("reviewer_role_instruction"),
        }

    def get_effective_security_config(self) -> dict[str, Any]:
        overrides = self._load_scope_overrides("security")
        return {
            "allowed_tools": self._as_csv(overrides.get("allowed_tools"), get_allowed_tools()),
            "upload_allowed_kinds": self._as_csv(
                overrides.get("upload_allowed_kinds"),
                get_upload_allowed_kinds(),
            ),
            "upload_max_bytes": self._as_int(
                overrides.get("upload_max_bytes"),
                get_upload_max_bytes(),
            ),
            "auth_enabled": self._as_bool(overrides.get("auth_enabled"), is_auth_enabled()),
            "rate_limit_enabled": self._as_bool(
                overrides.get("rate_limit_enabled"),
                is_rate_limit_enabled(),
            ),
            "idempotency_enabled": self._as_bool(
                overrides.get("idempotency_enabled"),
                is_idempotency_enabled(),
            ),
        }

    def get_effective_recovery_config(self) -> dict[str, Any]:
        overrides = self._load_scope_overrides("recovery")
        return {
            "llm_degrade_to_mock": self._as_bool(
                overrides.get("llm_degrade_to_mock"),
                is_recovery_llm_degrade_to_mock_enabled(),
            ),
            "tool_soft_fail": self._as_bool(
                overrides.get("tool_soft_fail"),
                is_recovery_tool_soft_fail_enabled(),
            ),
        }

    def get_effective_routing_config(self) -> dict[str, Any]:
        overrides = self._load_scope_overrides("routing")
        return {
            "video_route_name": self._as_str(overrides.get("video_route_name"), "video_analysis"),
            "video_route_reason": self._as_str(
                overrides.get("video_route_reason"),
                "检测到视频资产，优先走视频分析与后处理增强链。",
            ),
            "audio_route_name": self._as_str(overrides.get("audio_route_name"), "audio_analysis"),
            "audio_route_reason": self._as_str(
                overrides.get("audio_route_reason"),
                "检测到音频资产，优先走音频转写与分析链。",
            ),
            "file_route_name": self._as_str(overrides.get("file_route_name"), "document_analysis"),
            "file_route_reason": self._as_str(
                overrides.get("file_route_reason"),
                "检测到文档资产，优先走文档解析与总结链。",
            ),
            "image_route_name": self._as_str(overrides.get("image_route_name"), "image_analysis"),
            "image_route_reason": self._as_str(
                overrides.get("image_route_reason"),
                "检测到图片资产，优先走图片理解与 OCR 增强链。",
            ),
            "tool_augmented_route_name": self._as_str(
                overrides.get("tool_augmented_route_name"),
                "tool_augmented_chat",
            ),
            "tool_augmented_route_reason": self._as_str(
                overrides.get("tool_augmented_route_reason"),
                "检测到已有工具结果，优先结合工具输出完成回答。",
            ),
            "deliberation_enabled": self._as_bool(
                overrides.get("deliberation_enabled"),
                is_workflow_deliberation_enabled(),
            ),
            "deliberation_keywords": self._as_csv(
                overrides.get("deliberation_keywords"),
                get_workflow_deliberation_keywords(),
            ),
            "deliberation_route_name": self._as_str(
                overrides.get("deliberation_route_name"),
                "deliberation_chat",
            ),
            "deliberation_route_reason": self._as_str(
                overrides.get("deliberation_route_reason"),
                "检测到比较或评审型任务，优先进入更审慎的分析路径。",
            ),
            "contextual_message_threshold": self._as_int(
                overrides.get("contextual_message_threshold"),
                3,
            ),
            "contextual_route_name": self._as_str(
                overrides.get("contextual_route_name"),
                "contextual_chat",
            ),
            "contextual_route_reason": self._as_str(
                overrides.get("contextual_route_reason"),
                "检测到多轮上下文，优先保持连续对话一致性。",
            ),
            "default_route_name": self._as_str(overrides.get("default_route_name"), "direct_chat"),
            "default_route_reason": self._as_str(
                overrides.get("default_route_reason"),
                "当前是普通文本任务，优先走标准规划与回答链。",
            ),
        }

    def get_routing_config_snapshot(self) -> dict[str, dict[str, Any]]:
        effective = self.get_effective_routing_config()
        return {
            "image_route": {
                "route_name": effective["image_route_name"],
                "route_reason": effective["image_route_reason"],
            },
            "audio_route": {
                "route_name": effective["audio_route_name"],
                "route_reason": effective["audio_route_reason"],
            },
            "video_route": {
                "route_name": effective["video_route_name"],
                "route_reason": effective["video_route_reason"],
            },
            "file_route": {
                "route_name": effective["file_route_name"],
                "route_reason": effective["file_route_reason"],
            },
            "tool_augmented_route": {
                "route_name": effective["tool_augmented_route_name"],
                "route_reason": effective["tool_augmented_route_reason"],
            },
            "deliberation_route": {
                "route_name": effective["deliberation_route_name"],
                "route_reason": effective["deliberation_route_reason"],
                "enabled": effective["deliberation_enabled"],
                "keywords": effective["deliberation_keywords"],
                "message_threshold": 0,
            },
            "contextual_route": {
                "route_name": effective["contextual_route_name"],
                "route_reason": effective["contextual_route_reason"],
                "enabled": effective["contextual_message_threshold"] > 0,
                "keywords": [],
                "message_threshold": effective["contextual_message_threshold"],
            },
            "default_route": {
                "route_name": effective["default_route_name"],
                "route_reason": effective["default_route_reason"],
            },
        }

    def _load_scope_overrides(self, scope: str) -> dict[str, str]:
        rows = self.repository.list_configs(scope=scope)
        return {row["config_key"]: row["config_value"] for row in rows}

    def get_routing_config_template(self) -> dict[str, dict[str, str]]:
        return {
            "image_route_name": {"value_type": "str", "description": "图片输入默认命中的路由名称。", "example_value": "image_analysis"},
            "image_route_reason": {"value_type": "str", "description": "图片输入默认命中的路由原因。", "example_value": "检测到图片资产，优先走图片理解与 OCR 增强链。"},
            "audio_route_name": {"value_type": "str", "description": "音频输入默认命中的路由名称。", "example_value": "audio_analysis"},
            "audio_route_reason": {"value_type": "str", "description": "音频输入默认命中的路由原因。", "example_value": "检测到音频资产，优先走音频转写与分析链。"},
            "video_route_name": {"value_type": "str", "description": "视频输入默认命中的路由名称。", "example_value": "video_analysis"},
            "video_route_reason": {"value_type": "str", "description": "视频输入默认命中的路由原因。", "example_value": "检测到视频资产，优先走视频分析与后处理增强链。"},
            "file_route_name": {"value_type": "str", "description": "文件输入默认命中的路由名称。", "example_value": "document_analysis"},
            "file_route_reason": {"value_type": "str", "description": "文件输入默认命中的路由原因。", "example_value": "检测到文档资产，优先走文档解析与总结链。"},
            "tool_augmented_route_name": {"value_type": "str", "description": "已有工具结果时命中的路由名称。", "example_value": "tool_augmented_chat"},
            "tool_augmented_route_reason": {"value_type": "str", "description": "已有工具结果时命中的路由原因。", "example_value": "检测到已有工具结果，优先结合工具输出完成回答。"},
            "deliberation_enabled": {"value_type": "bool", "description": "是否启用审慎型任务路由判定。", "example_value": "true"},
            "deliberation_keywords": {"value_type": "csv", "description": "触发审慎型路由的关键词列表。", "example_value": "比较,评审,利弊,方案"},
            "deliberation_route_name": {"value_type": "str", "description": "审慎型任务命中的路由名称。", "example_value": "deliberation_chat"},
            "deliberation_route_reason": {"value_type": "str", "description": "审慎型任务命中的路由原因。", "example_value": "检测到比较或评审型任务，优先进入更审慎的分析路径。"},
            "contextual_message_threshold": {"value_type": "int", "description": "进入上下文路由所需的最小消息数。", "example_value": "3"},
            "contextual_route_name": {"value_type": "str", "description": "多轮上下文任务命中的路由名称。", "example_value": "contextual_chat"},
            "contextual_route_reason": {"value_type": "str", "description": "多轮上下文任务命中的路由原因。", "example_value": "检测到多轮上下文，优先保持连续对话一致性。"},
            "default_route_name": {"value_type": "str", "description": "默认兜底路由名称。", "example_value": "direct_chat"},
            "default_route_reason": {"value_type": "str", "description": "默认兜底路由原因。", "example_value": "当前是普通文本任务，优先走标准规划与回答链。"},
        }

    def list_routing_config_template_items(self) -> list[dict[str, str]]:
        return [
            {
                "config_key": key,
                "value_type": item["value_type"],
                "description": item["description"],
                "example_value": item["example_value"],
            }
            for key, item in self.get_routing_config_template().items()
        ]

    @staticmethod
    def _to_routing_config_version_payload(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": record["id"],
            "version_no": int(record["version_no"]),
            "snapshot": json.loads(record["snapshot_json"]),
            "changed_key": record["changed_key"],
            "changed_value": record["changed_value"],
            "change_action": record["change_action"],
            "created_by": record["created_by"],
            "updated_by": record["updated_by"],
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
        }

    @staticmethod
    def _routing_snapshot_to_config_items(snapshot: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {
                "config_key": "image_route_name",
                "config_value": snapshot["image_route"]["route_name"],
                "value_type": "str",
            },
            {
                "config_key": "image_route_reason",
                "config_value": snapshot["image_route"]["route_reason"],
                "value_type": "str",
            },
            {
                "config_key": "audio_route_name",
                "config_value": snapshot["audio_route"]["route_name"],
                "value_type": "str",
            },
            {
                "config_key": "audio_route_reason",
                "config_value": snapshot["audio_route"]["route_reason"],
                "value_type": "str",
            },
            {
                "config_key": "video_route_name",
                "config_value": snapshot["video_route"]["route_name"],
                "value_type": "str",
            },
            {
                "config_key": "video_route_reason",
                "config_value": snapshot["video_route"]["route_reason"],
                "value_type": "str",
            },
            {
                "config_key": "file_route_name",
                "config_value": snapshot["file_route"]["route_name"],
                "value_type": "str",
            },
            {
                "config_key": "file_route_reason",
                "config_value": snapshot["file_route"]["route_reason"],
                "value_type": "str",
            },
            {
                "config_key": "tool_augmented_route_name",
                "config_value": snapshot["tool_augmented_route"]["route_name"],
                "value_type": "str",
            },
            {
                "config_key": "tool_augmented_route_reason",
                "config_value": snapshot["tool_augmented_route"]["route_reason"],
                "value_type": "str",
            },
            {
                "config_key": "deliberation_enabled",
                "config_value": "true" if snapshot["deliberation_route"]["enabled"] else "false",
                "value_type": "bool",
            },
            {
                "config_key": "deliberation_keywords",
                "config_value": ",".join(snapshot["deliberation_route"]["keywords"]),
                "value_type": "csv",
            },
            {
                "config_key": "deliberation_route_name",
                "config_value": snapshot["deliberation_route"]["route_name"],
                "value_type": "str",
            },
            {
                "config_key": "deliberation_route_reason",
                "config_value": snapshot["deliberation_route"]["route_reason"],
                "value_type": "str",
            },
            {
                "config_key": "contextual_message_threshold",
                "config_value": str(snapshot["contextual_route"]["message_threshold"]),
                "value_type": "int",
            },
            {
                "config_key": "contextual_route_name",
                "config_value": snapshot["contextual_route"]["route_name"],
                "value_type": "str",
            },
            {
                "config_key": "contextual_route_reason",
                "config_value": snapshot["contextual_route"]["route_reason"],
                "value_type": "str",
            },
            {
                "config_key": "default_route_name",
                "config_value": snapshot["default_route"]["route_name"],
                "value_type": "str",
            },
            {
                "config_key": "default_route_reason",
                "config_value": snapshot["default_route"]["route_reason"],
                "value_type": "str",
            },
        ]

    @staticmethod
    def _flatten_routing_snapshot(snapshot: dict[str, Any]) -> dict[str, str]:
        flattened: dict[str, str] = {}
        for route_key, route_value in snapshot.items():
            if isinstance(route_value, dict):
                for field_key, field_value in route_value.items():
                    if isinstance(field_value, list):
                        flattened[f"{route_key}.{field_key}"] = ",".join(str(item) for item in field_value)
                    else:
                        flattened[f"{route_key}.{field_key}"] = str(field_value)
            else:
                flattened[route_key] = str(route_value)
        return flattened

    @staticmethod
    def _as_bool(raw_value: str | None, fallback: bool) -> bool:
        if raw_value is None:
            return fallback
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _as_int(raw_value: str | None, fallback: int) -> int:
        if raw_value is None:
            return fallback
        try:
            return max(1, int(raw_value.strip()))
        except ValueError:
            return fallback

    @staticmethod
    def _as_csv(raw_value: str | None, fallback: list[str]) -> list[str]:
        if raw_value is None:
            return fallback
        values = [item.strip() for item in raw_value.split(",") if item.strip()]
        return values or fallback

    @staticmethod
    def _as_str(raw_value: str | None, fallback: str) -> str:
        if raw_value is None:
            return fallback
        return raw_value.strip() or fallback

    @staticmethod
    def _validate_typed_value(*, key: str, value: str, value_type: str) -> None:
        normalized_value = value.strip()
        if value_type == "bool":
            if normalized_value.lower() not in {"1", "0", "true", "false", "yes", "no", "on", "off"}:
                raise ValidationError(f"routing 配置项 `{key}` 的值不是合法的 bool。")
            return
        if value_type == "int":
            try:
                int(normalized_value)
            except ValueError as error:
                raise ValidationError(f"routing 配置项 `{key}` 的值不是合法的 int。") from error
            return
        if value_type == "csv" and not normalized_value:
            raise ValidationError(f"routing 配置项 `{key}` 的值不能为空。")
            return
        if value_type == "str" and not normalized_value:
            raise ValidationError(f"routing 配置项 `{key}` 的值不能为空。")
