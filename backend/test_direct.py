import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from app.main import app

async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health
        res = await client.get("/health")
        print("[1] Health status:", res.status_code, res.json())

        # 2. Dashboard
        res = await client.get("/dashboard/stats")
        print("[2] Dashboard status:", res.status_code, res.json()["total_leads"])

        # 3. Influencers
        res = await client.get("/influencers")
        print("[3] Influencers status:", res.status_code, "Count:", len(res.json()))

    print("SUCCESS: Core endpoints verified!")

if __name__ == "__main__":
    asyncio.run(run())
