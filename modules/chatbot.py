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

		url = "http://43.153.7.56:8081/api/chat-process"
		headers = {
			"Accept": "application/json, text/plain, */*",
			"Accept-Encoding": "gzip, deflate",
			"Accept-Language": "en-US",
			"Connection": "keep-alive",
			"Content-Length": str(len(json.dumps(json_data))),
			"Content-Type": "application/json",
			"Host": "43.153.7.56:8081",
			"Origin": "http://aiassist.art",
			"Referer": "http://aiassist.art/",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 OPR/99.0.0.0",
		}

		async with aiohttp.ClientSession() as session:
			retries = 3
			while retries > 0:
				async with session.post(url, json=json_data, headers=headers) as response:
					try:
						if response.status != 200:
							raise Exception(f"HTTP error: {response.status} - {response.reason}")

						content = await response.text(encoding='utf-8')

						if not content:
							retries -= 1
							continue

					finally:
						response.release()
				await session.close()
				break

			if retries == 0:
				raise Exception("Failed to get a non-empty response after multiple retries.")

		try:
			split = content.rsplit("\n", 1)[1]
			to_json = json.loads(split)
			return to_json
		except Exception as e:
			raise Exception(f"Error parsing JSON response: {e}\nResponse: {content}") from e
