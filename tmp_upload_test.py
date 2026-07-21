import urllib.request

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
payload = (
    '--' + boundary + '\r\n'
    'Content-Disposition: form-data; name="file"; filename="sample.txt"\r\n'
    'Content-Type: text/plain\r\n\r\n'
    'Hello from upload test\r\n'
    '--' + boundary + '--\r\n'
).encode('utf-8')

req = urllib.request.Request('http://127.0.0.1:8000/api/analyze', data=payload, method='POST')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
with urllib.request.urlopen(req, timeout=10) as response:
    print(response.status)
    print(response.read().decode('utf-8'))
