import aiohttp
import json

class Completion:
    @staticmethod
    async def create(
        systemMessage: str = "You are a helpful assistant",
        prompt: str = "",
        parentMessageId: str = "",
        temperature: float = 0.8,
        top_p: float = 1,
    ):
        json_data = {
            "prompt": prompt,
            "options": {"parentMessageId": parentMessageId},
            "systemMessage": systemMessage,
            "temperature": temperature,
            "top_p": top_p,
        }

        url = "http://aiassist.art/api/chat-process"
        headers = {"Content-type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=json_data, headers=headers) as response:
                content = await response.text()

        return Completion._load_json(content)

    @classmethod
    def _load_json(cls, content) -> dict:
        lines = content.strip().split('\n')
        last_line = lines[-1]
        json_object = json.loads(last_line)
        return json_object