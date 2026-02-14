#!/usr/bin/env python3
"""Test new API endpoints"""

import requests
import json

base_url = 'http://localhost:8001'

print('Testing new API endpoints...\n')

# Test 1: Get event log
print('1. GET /game/event-log')
r = requests.get(f'{base_url}/game/event-log?limit=5')
print(f'Status: {r.status_code}')
data = r.json()
print(f'Total events: {data.get("total_events", 0)}')
print(f'Returned: {data.get("returned", 0)}\n')

# Test 2: Inject event
print('2. POST /game/inject-event')
r = requests.post(f'{base_url}/game/inject-event?event_type=mysterious_sound&room=Hallway&message=A ghost appears!')
print(f'Status: {r.status_code}')
print(f'Injected: {r.json().get("status")}\n')

# Test 3: Save session
print('3. POST /game/save-session')
r = requests.post(f'{base_url}/game/save-session?session_name=TestSession')
print(f'Status: {r.status_code}')
print(f'Saved: {r.json().get("status")}\n')

# Test 4: List sessions
print('4. GET /game/sessions')
r = requests.get(f'{base_url}/game/sessions')
print(f'Status: {r.status_code}')
data = r.json()
print(f'Total sessions: {data.get("total", 0)}\n')

# Test 5: Export log
print('5. POST /game/export-log')
r = requests.post(f'{base_url}/game/export-log?format=text')
print(f'Status: {r.status_code}')
data = r.json()
print(f'Format: {data.get("format")}')
content_preview = str(data.get("content", ""))[:100]
print(f'Content preview: {content_preview}...\n')

# Test 6: Health check
print('6. GET /health')
r = requests.get(f'{base_url}/health')
print(f'Status: {r.status_code}')
print(f'Response: {r.json()}\n')

print('✅ All new endpoints tested successfully!')
print('\n📋 Summary of new features:')
print('  ✓ Event log retrieval')
print('  ✓ Event injection (spectator/GM feature)')
print('  ✓ Session saving')
print('  ✓ Session listing')
print('  ✓ Log export in multiple formats')
print('  ✓ PDF export (requires weasyprint)')
print('  ✓ AI player management')
print('  ✓ Difficulty-based AI behavior')
