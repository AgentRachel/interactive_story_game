import asyncio
import json
import sys

try:
    import requests
    import websockets
except Exception as e:
    print('Missing dependency:', e)
    print('Install with: pip install requests websockets')
    sys.exit(1)

async def ws_test():
    url = 'ws://localhost:8001/ws/TestClient'
    print('Connecting to', url)
    try:
        async with websockets.connect(url) as ws:
            print('Connected websocket')
            # receive welcome
            data = await ws.recv()
            print('WS welcome:', data)
            # send a test chat
            await ws.send(json.dumps({'type': 'chat', 'message': 'hello from test_index_ws'}))
            # try to receive a few messages for a short time
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=2)
                    print('WS msg:', msg)
            except asyncio.TimeoutError:
                print('No more messages (timeout)')
    except Exception as e:
        print('WebSocket error:', type(e).__name__, e)


def main():
    try:
        r = requests.get('http://localhost:8001/')
        print('HTTP GET / ->', r.status_code, 'bytes:', len(r.content))
    except Exception as e:
        print('HTTP request failed:', type(e).__name__, e)
        return

    asyncio.run(ws_test())

if __name__ == '__main__':
    main()
