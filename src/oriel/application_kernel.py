"""Shared application framework kernel for ORIEL 0.9.0."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generic, Mapping, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    value: T | None = None
    error: str | None = None

    @property
    def successful(self) -> bool:
        return self.error is None

    def unwrap(self) -> T:
        if self.error is not None:
            raise RuntimeError(self.error)
        return self.value  # type: ignore[return-value]


@dataclass(frozen=True)
class ApplicationConfig:
    values: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_environment(cls, prefix: str = "ORIEL_") -> "ApplicationConfig":
        return cls({key[len(prefix):].lower(): value for key, value in os.environ.items() if key.startswith(prefix)})

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.values.get(key, default)

    def require(self, key: str) -> str:
        value = self.values.get(key)
        if value is None or value == "":
            raise KeyError(f"missing application configuration: {key}")
        return value


Factory = Callable[["ServiceContainer"], object]


class ServiceContainer:
    def __init__(self):
        self._factories: dict[str, tuple[Factory, bool]] = {}
        self._instances: dict[str, object] = {}
        self._resolving = threading.local()
        self._lock = threading.RLock()

    def register(self, name: str, factory: Factory, *, singleton: bool = True) -> None:
        with self._lock:
            if name in self._factories:
                raise KeyError(f"service already registered: {name}")
            self._factories[name] = (factory, singleton)

    def instance(self, name: str, value: object) -> None:
        self.register(name, lambda container: value)
        self._instances[name] = value

    def resolve(self, name: str) -> object:
        with self._lock:
            if name in self._instances:
                return self._instances[name]
            if name not in self._factories:
                raise KeyError(f"service not registered: {name}")
            stack = getattr(self._resolving, "stack", [])
            if name in stack:
                raise RuntimeError("circular service dependency: " + " -> ".join([*stack, name]))
            self._resolving.stack = [*stack, name]
            try:
                factory, singleton = self._factories[name]
                value = factory(self)
                if singleton:
                    self._instances[name] = value
                return value
            finally:
                self._resolving.stack = stack


@dataclass(frozen=True)
class Event:
    name: str
    payload: object = None


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}
        self._lock = threading.RLock()

    def subscribe(self, name: str, handler: Callable[[Event], None]) -> Callable[[], None]:
        with self._lock:
            self._subscribers.setdefault(name, []).append(handler)
        def unsubscribe() -> None:
            with self._lock:
                handlers = self._subscribers.get(name, [])
                if handler in handlers: handlers.remove(handler)
        return unsubscribe

    def publish(self, event: Event) -> None:
        with self._lock:
            handlers = tuple(self._subscribers.get(event.name, ()))
        for handler in handlers:
            handler(event)


@dataclass(frozen=True)
class HealthCheck:
    name: str
    healthy: bool
    detail: str = ""


class HealthRegistry:
    def __init__(self):
        self._checks: dict[str, Callable[[], bool | HealthCheck]] = {}

    def register(self, name: str, check: Callable[[], bool | HealthCheck]) -> None:
        if name in self._checks: raise KeyError(f"health check already registered: {name}")
        self._checks[name] = check

    def run(self) -> list[HealthCheck]:
        results: list[HealthCheck] = []
        for name, check in self._checks.items():
            try:
                value = check()
                results.append(value if isinstance(value, HealthCheck) else HealthCheck(name, bool(value)))
            except Exception as error:
                results.append(HealthCheck(name, False, str(error)))
        return results


class ApplicationState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"


class Application:
    def __init__(self, name: str, config: ApplicationConfig | None = None):
        self.name = name
        self.config = config or ApplicationConfig()
        self.services = ServiceContainer()
        self.events = EventBus()
        self.health = HealthRegistry()
        self.state = ApplicationState.CREATED
        self._startup: list[Callable[["Application"], None]] = []
        self._shutdown: list[Callable[["Application"], None]] = []

    def on_start(self, callback: Callable[["Application"], None]) -> None:
        if self.state is not ApplicationState.CREATED: raise RuntimeError("startup hooks are frozen")
        self._startup.append(callback)

    def on_stop(self, callback: Callable[["Application"], None]) -> None:
        if self.state is not ApplicationState.CREATED: raise RuntimeError("shutdown hooks are frozen")
        self._shutdown.append(callback)

    def start(self) -> None:
        if self.state is not ApplicationState.CREATED: raise RuntimeError(f"cannot start application from {self.state.value}")
        for callback in self._startup: callback(self)
        self.state = ApplicationState.RUNNING
        self.events.publish(Event("application.started", self.name))

    def stop(self) -> None:
        if self.state is not ApplicationState.RUNNING: raise RuntimeError(f"cannot stop application from {self.state.value}")
        errors: list[str] = []
        for callback in reversed(self._shutdown):
            try: callback(self)
            except Exception as error: errors.append(str(error))
        self.state = ApplicationState.STOPPED
        self.events.publish(Event("application.stopped", self.name))
        if errors: raise RuntimeError("shutdown errors: " + "; ".join(errors))

    def __enter__(self) -> "Application":
        self.start(); return self

    def __exit__(self, error_type, error, traceback) -> None:
        self.stop()
