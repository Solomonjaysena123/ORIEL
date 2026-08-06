import os
import unittest
from unittest.mock import patch

from oriel.application_kernel import Application, ApplicationConfig, ApplicationState, Event, EventBus, HealthRegistry, Result, ServiceContainer


class ApplicationKernel090Tests(unittest.TestCase):
    def test_configuration_and_result(self):
        with patch.dict(os.environ, {"ORIEL_DATABASE_URL": "sqlite:///app.db"}, clear=True):
            config = ApplicationConfig.from_environment()
        self.assertEqual(config.require("database_url"), "sqlite:///app.db")
        with self.assertRaises(TypeError):
            config.values["database_url"] = "changed"  # type: ignore[index]
        self.assertEqual(Result(value=3).unwrap(), 3)
        with self.assertRaises(RuntimeError): Result(error="failed").unwrap()

    def test_services_singletons_factories_and_cycles(self):
        services = ServiceContainer(); services.register("value", lambda container: object())
        self.assertIs(services.resolve("value"), services.resolve("value"))
        services.register("transient", lambda container: object(), singleton=False)
        self.assertIsNot(services.resolve("transient"), services.resolve("transient"))
        cyclic = ServiceContainer(); cyclic.register("a", lambda container: container.resolve("b")); cyclic.register("b", lambda container: container.resolve("a"))
        with self.assertRaisesRegex(RuntimeError, "circular"): cyclic.resolve("a")

    def test_events_unsubscribe(self):
        bus = EventBus(); received = []
        unsubscribe = bus.subscribe("saved", lambda event: received.append(event.payload))
        bus.publish(Event("saved", 1)); unsubscribe(); bus.publish(Event("saved", 2))
        self.assertEqual(received, [1])

    def test_health_failures_are_isolated(self):
        health = HealthRegistry(); health.register("database", lambda: True); health.register("cache", lambda: (_ for _ in ()).throw(RuntimeError("offline")))
        results = health.run()
        self.assertTrue(results[0].healthy); self.assertFalse(results[1].healthy); self.assertEqual(results[1].detail, "offline")

    def test_lifecycle_order_and_state(self):
        app = Application("inventory"); order = []
        app.on_start(lambda current: order.append("start-1")); app.on_start(lambda current: order.append("start-2"))
        app.on_stop(lambda current: order.append("stop-1")); app.on_stop(lambda current: order.append("stop-2"))
        with app: self.assertEqual(app.state, ApplicationState.RUNNING)
        self.assertEqual(app.state, ApplicationState.STOPPED)
        self.assertEqual(order, ["start-1", "start-2", "stop-2", "stop-1"])
