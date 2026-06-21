import os
import uuid
import httpx

RUNWARE_API_URL = "https://api.runware.ai/v1"
CREDITS_PER_IMAGE = 1

async def generate_images(
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    count: int,
    cfg_scale: float,
    steps: int,
) -> list[str]:
    api_key = os.getenv("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    payload = [
        {
            "taskType": "imageInference",
            "taskUUID": str(uuid.uuid4()),
            "positivePrompt": prompt,
            "negativePrompt": negative_prompt,
            "model": "klingai:klingai-image-3-0",
            "width": width,
            "height": height,
            "numberResults": count,
            "CFGScale": cfg_scale,
            "steps": steps,
            "outputFormat": "WEBP",
        }
    ]

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            RUNWARE_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["imageURL"] for item in data["data"]]
