from oriel.lsp import diagnostics, declaration, locations, word_at

def test_lsp_shared_analysis_and_navigation():
    text='fn main() {\n let value = 1\n print(value)\n}'
    assert diagnostics(text)==[]
    assert declaration(text,'value')['line']==1
    assert len(locations('file:///x.orl',text,'value'))==2
    assert word_at(text,2,8)[0]=='value'
