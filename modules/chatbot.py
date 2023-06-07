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
                if response.status != 200:
                    raise Exception(f"HTTP error: {response.status} - {response.reason}")

                content = await response.text()

        try:
            split = content.rsplit("\n", 1)[1]
            to_json = json.loads(split)
            return to_json
        except Exception as e:
            raise Exception(f"Error parsing JSON response: {e}\nResponse: {content}") from e