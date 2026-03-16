import httpx
import asyncio

async def check_live():
    url = "https://gemini-storyteller-2320255921.us-central1.run.app/story/stream?prompt=Test&style=Fantasy"
    print(f"Checking live URL: {url}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("GET", url) as response:
                print(f"HTTP Status: {response.status_code}")
                async for line in response.aiter_lines():
                    if line:
                        print(line)
                        if "v11" in line:
                            print("VERIFIED: Hitting V11 revision")
                        if "error" in line.lower():
                            print(f"ERROR DETECTED: {line}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_live())
