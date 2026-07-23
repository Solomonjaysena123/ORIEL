from oriel.lsp import diagnostics


def test_lsp_diagnostic_shape():
    items = diagnostics('let = 1\n')
    assert len(items) == 1
    item = items[0]
    assert item['source'] == 'oriel'
    assert item['severity'] == 1
    assert 'range' in item
    assert str(item['code']).startswith('E')


def test_lsp_accepts_valid_source():
    assert diagnostics('let value = 1\nprint(value)\n') == []
