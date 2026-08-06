# ORIEL API Framework Preview

This API framework preview builds on the shared application kernel. Routing and responses are independent of the HTTP server, so the same behavior can be tested in-process.

```oriel
api Inventory {
    get "/items/{id}" => item
    post "/items" => create
}

fn item() -> Map { return {"name":"sample"} }
fn create() -> Map { return {"created":true} }
```

Python integrations can compile and test this source directly:

```python
from oriel.api_framework import APIApplication, TestClient

client = TestClient(APIApplication(source, title="Inventory", version="0.9.0"))
response = client.get("/items/42?expand=true")
assert response.status == 200
assert response.body["meta"]["params"] == {"id": "42"}
```

The development server supports GET, POST, PUT, PATCH, DELETE, OPTIONS, JSON request bodies, CORS headers, `/openapi.json`, structured 400/404/405 errors, query values, and path parameters.

## Scope and limitations

- Handler return expressions are currently deterministic literals parsed from ORIEL source; full runtime-bound request handlers are future work.
- The included server is for development and testing, not direct internet-facing production deployment.
- Authentication, rate limiting, streaming, WebSockets, multipart uploads, and dependency injection are not included in this milestone.
- Database integration remains separate and is not promoted as part of the 0.9.0 API release.
