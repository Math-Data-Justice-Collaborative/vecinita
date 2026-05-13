"""Lifecycle registry and execution primitives for model runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Literal
from uuid import uuid4

LifecyclePhase = Literal["startup", "steady_state", "teardown"]
LifecycleEventType = Literal[
    "preload_start",
    "preload_success",
    "preload_failure",
    "retry",
    "teardown_start",
    "teardown_success",
    "teardown_failure",
    "plugin_validation_failure",
]
LifecycleHook = Callable[[dict[str, Any]], None]

PHASE_ORDER: tuple[LifecyclePhase, ...] = ("startup", "steady_state", "teardown")


@dataclass(frozen=True)
class LifecyclePlugin:
    plugin_id: str
    phase: LifecyclePhase
    order: int
    hook: LifecycleHook
    required: bool = True
    enabled: bool = True


@dataclass(frozen=True)
class LifecycleEvent:
    event_type: LifecycleEventType
    phase: LifecyclePhase
    correlation_id: str
    timestamp: str
    plugin_id: str | None = None
    details: dict[str, Any] | None = None

    def as_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event_type": self.event_type,
            "phase": self.phase,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }
        if self.plugin_id:
            payload["plugin_id"] = self.plugin_id
        if self.details:
            payload["details"] = self.details
        return payload


def new_correlation_id() -> str:
    return str(uuid4())


def make_lifecycle_event(
    *,
    event_type: LifecycleEventType,
    phase: LifecyclePhase,
    correlation_id: str,
    plugin_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = LifecycleEvent(
        event_type=event_type,
        phase=phase,
        correlation_id=correlation_id,
        timestamp=datetime.now(tz=UTC).isoformat(),
        plugin_id=plugin_id,
        details=details,
    )
    return event.as_payload()


class PluginRegistry:
    """Ordered lifecycle plugin registry with validation and phase execution."""

    def __init__(self, registry_id: str) -> None:
        self.registry_id = registry_id
        self._plugins: list[LifecyclePlugin] = []

    def register(self, plugin: LifecyclePlugin) -> None:
        if plugin.phase not in PHASE_ORDER:
            raise ValueError(f"Invalid lifecycle phase '{plugin.phase}'")
        duplicate_order = next(
            (
                existing
                for existing in self._plugins
                if existing.phase == plugin.phase and existing.order == plugin.order
            ),
            None,
        )
        if duplicate_order is not None:
            raise ValueError(
                "Duplicate plugin order "
                f"{plugin.order} in phase '{plugin.phase}' "
                f"({duplicate_order.plugin_id}, {plugin.plugin_id})"
            )
        self._plugins.append(plugin)

    def validate(self) -> None:
        for phase in PHASE_ORDER:
            required_enabled = [
                p
                for p in self._plugins
                if p.phase == phase and p.required and p.enabled
            ]
            if phase in {"startup", "teardown"} and not required_enabled:
                raise ValueError(
                    f"Missing required enabled plugin for phase '{phase}' in registry "
                    f"'{self.registry_id}'"
                )

    def ordered_for_phase(self, phase: LifecyclePhase) -> list[LifecyclePlugin]:
        return sorted(
            [p for p in self._plugins if p.phase == phase and p.enabled],
            key=lambda plugin: plugin.order,
        )

    def execute_phase(self, phase: LifecyclePhase, context: dict[str, Any]) -> None:
        for plugin in self.ordered_for_phase(phase):
            plugin.hook(context)


def make_default_registry(
    *,
    registry_id: str,
    startup_hook: LifecycleHook,
    teardown_hook: LifecycleHook,
) -> PluginRegistry:
    """Construct the default cache-preserving lifecycle strategy registry."""
    registry = PluginRegistry(registry_id=registry_id)
    registry.register(
        LifecyclePlugin(
            plugin_id="default-startup-preload",
            phase="startup",
            order=10,
            hook=startup_hook,
            required=True,
            enabled=True,
        )
    )
    registry.register(
        LifecyclePlugin(
            plugin_id="default-teardown-cache-preserving",
            phase="teardown",
            order=10,
            hook=teardown_hook,
            required=True,
            enabled=True,
        )
    )
    registry.validate()
    return registry
