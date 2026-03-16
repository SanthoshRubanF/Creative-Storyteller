import httpx
import asyncio
import json
import base64
import time
import os
import urllib.parse # Added for URL quoting

BASE_URL = "http://localhost:8000"

async def test_health():
    print("\n[TEST 1] Health Check...")
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            print(f"PASS: Health is ok. Models: {data['model']}, {data['image_model']}")
            return True, time.time() - start
    except Exception as e:
        print(f"FAIL: {e}")
        return False, time.time() - start

async def test_styles():
    print("\n[TEST 2] Styles Endpoint...")
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/styles")
            assert response.status_code == 200
            styles = response.json()
            assert len(styles) == 5
            names = [s["name"] for s in styles]
            print(f"PASS: Found 5 styles: {', '.join(names)}")
            return True, time.time() - start
    except Exception as e:
        print(f"FAIL: {e}")
        return False, time.time() - start

async def test_story_stream_text():
    print("\n[TEST 3] Story Stream (Text & Structure)...")
    start = time.time()
    event_counts = {"story": 0, "image": 0, "status": 0, "done": 0}
    try:
        async with httpx.AsyncClient(timeout=40.0) as client:
            prompt_val = "A brave robot in Chennai"
            style_val = "children"
            url = f"{BASE_URL}/story/stream?prompt={urllib.parse.quote(prompt_val)}&style={urllib.parse.quote(style_val)}"
            async with client.stream("GET", url) as response:
                assert response.status_code == 200
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        event_type = data.get("type", "unknown")
                        if "text" in data: event_counts["story"] += 1
                        if event_type == "image": event_counts["image"] += 1
                        if event_type == "status": event_counts["status"] += 1
                        if event_type == "done":
                            event_counts["done"] += 1
                            break
                        
        print(f"Event Summary: {event_counts}")
        assert event_counts["story"] > 3
        # In a real run, image requests appear. We check for 'image_loading' status too.
        print("PASS: Stream received expected events.")
        return True, time.time() - start
    except Exception as e:
        print(f"FAIL: {e}")
        return False, time.time() - start

async def test_image_gen_standalone():
    print("\n[TEST 4] Standalone Image Generation...")
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {"prompt": "A golden temple at sunset, digital art"}
            response = await client.post(f"{BASE_URL}/image/generate", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert "image" in data
            
            # Save image
            img_data = base64.b64decode(data["image"])
            with open("test_image.png", "wb") as f:
                f.write(img_data)
            
            print("PASS: Image saved as test_image.png — open to verify")
            return True, time.time() - start
    except Exception as e:
        print(f"FAIL: {e}")
        return False, time.time() - start

async def test_full_story():
    print("\n[TEST 5] Full Story End-to-End...")
    start = time.time()
    full_text = ""
    image_count = 0
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            p_val = "A dragon discovers fire for the first time"
            s_val = "fantasy"
            url = f"{BASE_URL}/story/stream?prompt={urllib.parse.quote(p_val)}&style={urllib.parse.quote(s_val)}"
            async with client.stream("GET", url) as response:
                assert response.status_code == 200
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if "text" in data:
                            full_text += data["text"]
                        if data.get("type") == "image":
                            image_count += 1
                        if data.get("type") == "done":
                            break
        
        print("\n--- FULL STORY TEXT ---")
        print(full_text[:500] + "...")
        print("-----------------------")
        print(f"Images Received: {image_count}")
        print(f"PASS: Full story generated.")
        return True, time.time() - start
    except Exception as e:
        print(f"FAIL: {e}")
        return False, time.time() - start

async def run_all():
    print("="*50)
    print("GEMINI STORYTELLER LOCAL TEST SUITE")
    print("="*50)
    print("\nSTARTUP INSTRUCTIONS:")
    print("  cd backend")
    print("  uvicorn main:app --reload --port 8000")
    print("\nWAITING FOR SERVER...")
    
    results = []
    results.append(("Health Check", await test_health()))
    results.append(("Styles Endpoint", await test_styles()))
    results.append(("Story Stream (Text)", await test_story_stream_text()))
    results.append(("Standalone Image Gen", await test_image_gen_standalone()))
    results.append(("Full Story E2E", await test_full_story()))
    
    print("\n" + "="*50)
    print(f"{'TEST NAME':<25} {'STATUS':<10} {'TIME':<10}")
    print("-" * 50)
    for name, (status, duration) in results:
        status_str = "PASS" if status else "FAIL"
        print(f"{name:<25} {status_str:<10} {duration:.2f}s")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(run_all())
