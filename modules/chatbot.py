from json import loads
from queue import Queue, Empty
from re import findall
from typing import Generator, Optional
from curl_cffi import requests
from fake_useragent import UserAgent

class Completion:
	part1 = '{"role":"assistant","id":"chatcmpl'
	part2 = '"},"index":0,"finish_reason":null}]}}'
	regex = rf'{part1}(.*){part2}'

	message_queue = Queue()
	stream_completed = False
	last_msg_id = None
	session = requests.Session()

	@staticmethod
	def request(prompt: str, proxy: Optional[str] = None):
		if Completion.session is None:
			Completion.session = requests.Session()

		headers = {
			'authority': 'chatbot.theb.ai',
			'content-type': 'application/json',
			'origin': 'https://chatbot.theb.ai',
			'user-agent': UserAgent().edge,
		}

		proxies = {'http': 'http://' + proxy, 'https': 'http://' + proxy} if proxy else None

		options = {}
		if Completion.last_msg_id:
			options['parentMessageId'] = Completion.last_msg_id

		response = Completion.session.post(
			'https://chatbot.theb.ai/api/chat-process',
			headers=headers,
			proxies=proxies,
			content_callback=Completion.handle_stream_response,
			json={'prompt': prompt, 'options': options},
			timeout=420,
		)

		response.raise_for_status()
		Completion.stream_completed = True

	@staticmethod
	def create(prompt: str, proxy: Optional[str] = None) -> Generator[str, None, None]:
		Completion.stream_completed = False

		Completion.request(prompt, proxy)

		while not Completion.stream_completed or not Completion.message_queue.empty():
			try:
				message = Completion.message_queue.get_nowait()
				for message in findall(Completion.regex, message):
					message_json = loads(Completion.part1 + message + Completion.part2)
					Completion.last_msg_id = message_json['id']
					yield message_json['text']
			except Empty:
				pass

		Completion.message_queue.queue.clear()

	@staticmethod
	def handle_stream_response(response):
		try:
			Completion.message_queue.put(response.decode('utf-8'))
		except UnicodeDecodeError:
			pass

	@staticmethod
	def get_response(prompt: str, proxy: Optional[str] = None) -> Optional[str]:
		response_list = []
		for message in Completion.create(prompt, proxy):
			response_list.append(message)

		if response_list:
			return response_list[-1]
		
		return None

	@staticmethod
	def reset():
		Completion.stream_completed = False
		Completion.last_msg_id = None
		Completion.message_queue.queue.clear()
		Completion.session.close()
		Completion.session = None