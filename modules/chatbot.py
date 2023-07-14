import aiohttp
import json
import asyncio

class Completion:
	MAX_RETRIES = 3

	@staticmethod
	async def create(
		systemMessage: str = "You are a helpful assistant",
		prompt: str = "",
		parentMessageId: str = "",
		temperature: float = 0.8,
		top_p: float = 1,
		server_id: str = None,
	):
		json_data = {
			"prompt": prompt,
			"options": {"parentMessageId": parentMessageId},
			"systemMessage": systemMessage,
			"temperature": temperature,
			"top_p": top_p,
		}

		url = "https://www.aitianhu.com/api/chat-process"
		headers = {
			"Accept": "application/json, text/plain, */*",
			"Accept-Encoding": "gzip, deflate",
			"Accept-Language": "en-US",
			"Connection": "keep-alive",
			"Content-Type": "application/json",
			"Origin": "https://www.aitianhu.com",
			"Referer": "https://www.aitianhu.com/",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 OPR/99.0.0.0",
		}

		if server_id:
			headers["Cookie"] = f"SERVERID={server_id}"

		retries = 0
		while retries < Completion.MAX_RETRIES:
			try:
				async with aiohttp.ClientSession() as session:
					async with session.post(url, json=json_data, headers=headers, raise_for_status=True) as response:
						content = await response.text(encoding='utf-8')
						if content:
							server_id_cookie = response.cookies.get('SERVERID')
							server_id_value = server_id_cookie.value if server_id_cookie else None

							json_data = [item.rstrip() for item in content.split('\n')]
							to_json = json.loads(json_data[-1])

							return {
								"json": to_json,
								"cookie": server_id_value
								}

			except Exception as e:
				if retries == 3:
					raise e
				else:
					print(f"Ha ocurrido un error: {str(e)}")
					# Retry if there is an error
					retries += 1