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
            try:
                async with session.post(url, json=json_data, headers=headers) as response:
                    content = await response.text()

                    if response.status != 200:
                        raise Exception(f"Request failed with status code {response.status}")

                    return Completion._load_json(content)
            except aiohttp.ClientError as e:
                print(f"HTTP request error: {e}")
            except Exception as e:
                print(f"Error: {e}")
    
    @classmethod
    def _load_json(cls, content) -> dict:
        try:
            lines = content.strip().split('\n')
            last_line = lines[-1]
            json_object = json.loads(last_line)
            return json_object
        except Exception as e:
            print(f"Error: {e}")
            print(f"JSON object: {json_object}")