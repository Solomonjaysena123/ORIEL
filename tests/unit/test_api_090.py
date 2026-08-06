import unittest

from oriel.api_framework import APIApplication, Request, TestClient, openapi_manifest


SOURCE = '''api Inventory {
    get "/items/{id}" => item
    post "/items" => create
}
fn item() -> Map { return {"name":"sample"} }
fn create() -> Map { return {"created":true} }
'''


class APIFramework090Tests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(APIApplication(SOURCE, title="Inventory", version="0.9.0"))

    def test_path_parameters_and_query(self):
        response = self.client.get('/items/42?expand=true')
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body['meta']['params'], {'id': '42'})
        self.assertEqual(response.body['meta']['query'], {'expand': ['true']})

    def test_method_not_allowed_has_allow_header(self):
        response = self.client.post('/items/42')
        self.assertEqual(response.status, 405)
        self.assertEqual(response.headers['Allow'], 'GET')

    def test_not_found_and_openapi(self):
        self.assertEqual(self.client.get('/missing').status, 404)
        document = self.client.get('/openapi.json').body
        self.assertEqual(document['info'], {'title': 'Inventory', 'version': '0.9.0'})
        parameter = document['paths']['/items/{id}']['get']['parameters'][0]
        self.assertEqual((parameter['name'], parameter['in']), ('id', 'path'))

    def test_request_body_is_available_to_transport(self):
        response = self.client.post('/items', json_body={'name': 'Desk'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body['data'], {'created': True})

    def test_dispatch_is_transport_independent(self):
        response = self.client.app.dispatch(Request('GET', '/items/7'))
        self.assertEqual(response.body['meta']['params']['id'], '7')
