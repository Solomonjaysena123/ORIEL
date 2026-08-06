# ORIEL Shared Application Framework Kernel 0.9.0

ORIEL 0.9.0 establishes the common application foundation used by later API, database, web, and security frameworks.

```python
from oriel.application_kernel import Application, ApplicationConfig

app = Application("inventory", ApplicationConfig.from_environment())
app.services.register("repository", lambda services: InventoryRepository())
app.health.register("database", lambda: app.services.resolve("repository").healthy())

app.on_start(lambda current: current.events.publish(Event("inventory.ready")))
with app:
    run_application(app)
```

The kernel provides:

- created, running, and stopped lifecycle states;
- ordered startup and reverse-order shutdown hooks;
- environment-backed immutable configuration;
- singleton and transient service factories with circular-dependency detection;
- synchronous thread-safe events and unsubscribe handles;
- isolated health checks that report exceptions without aborting the registry;
- structured `Result` values with explicit unwrap behavior.

## Limitations

- The container is intentionally small and does not perform reflection-based dependency injection.
- Events are in-process and synchronous; durable queues and distributed delivery are later concerns.
- Configuration values are strings and secret storage remains the application's responsibility.
- The kernel does not itself provide HTTP, databases, UI, authentication, or deployment.
