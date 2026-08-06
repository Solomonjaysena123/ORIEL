# ORIEL API Framework 0.9.2

ORIEL v0.9.2 compiles API declarations into a reusable application dispatcher shared by the in-process test client and development HTTP server.

```oriel
api Inventory {
    get "/items/{id}" => item
    post "/items" => create
}

fn item() -> Map { return {"name":"sample"} }
fn create() -> Map { return {"created":true} }
```

Supported behavior includes GET, POST, PUT, PATCH, DELETE, OPTIONS, path parameters, query values, JSON request bodies, structured errors, CORS development headers, OpenAPI 3.1, and deterministic in-process tests.

## Limitations

- Handler return expressions are deterministic source literals; full runtime-bound request handlers remain future work.
- The threaded server is for local development and testing, not direct production exposure.
- Authentication, streaming, WebSockets, multipart uploads, rate limiting, and production deployment are outside this package.
