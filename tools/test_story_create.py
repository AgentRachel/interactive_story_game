import requests
import json

url = 'http://localhost:8001/story/new'
params = {
    'world': 'testworld',
    'character': 'Tester',
    'genre': 'mystery',
    'advanced': json.dumps({'mood':'tense','ai_freq':5})
}
print('POST', url, 'params=', params)
r = requests.post(url, params=params)
print('status', r.status_code)
try:
    print('json:', r.json())
except Exception as e:
    print('resp text:', r.text)
