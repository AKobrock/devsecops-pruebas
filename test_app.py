from app import app


def test_hello_funciona():
    client = app.test_client()
    resp = client.get('/hello?name=TEST')
    assert resp.status_code == 200
    assert b'TEST' in resp.data


def test_xss_no_se_refleja_sin_escapar():
    client = app.test_client()
    resp = client.get('/hello?name=<script>alert(1)</script>')
    assert b'<script>' not in resp.data