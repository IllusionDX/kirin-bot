import json
from queue import Queue, Empty
from re import findall
from threading import Thread
from typing import Generator, Optional

from curl_cffi import requests
from fake_useragent import UserAgent

class Completion:
	timer = None
	message_queue = Queue()
	stream_completed = False
	last_msg_id = None
	thread = None
	buffer = ""

	@staticmethod
	def request(prompt: str, proxy: Optional[str] = None):
		headers = {
			'authority': 'chatbot.theb.ai',
			'content-type': 'application/json',
			'origin': 'https://chatbot.theb.ai',
			'user-agent': UserAgent().random,
		}

		proxies = {'http': 'http://' + proxy, 'https': 'http://' + proxy} if proxy else None
		
		options = {}
		if Completion.last_msg_id:
			options['parentMessageId'] = Completion.last_msg_id
		
		requests.post(
			'https://chatbot.theb.ai/api/chat-process',
			headers=headers,
			proxies=proxies,
			content_callback=Completion.handle_stream_response,
			json={'prompt': prompt, 'options': options},
			timeout=100000
		)

		Completion.stream_completed = True

	@staticmethod
	def create(prompt: str, proxy: Optional[str] = None) -> Generator[dict, None, None]:
		Completion.stream_completed = False
		Completion.thread = Thread(target=Completion.request, args=[prompt, proxy])
		Completion.thread.start()

		while not Completion.stream_completed or not Completion.message_queue.empty():
			try:
				message = Completion.message_queue.get(timeout=1)
				if message is not None:
					Completion.last_msg_id = message['id']
					yield message['delta']

			except Empty:
				pass

	@staticmethod
	def handle_stream_response(response):
		Completion.buffer += response.decode()
		messages = Completion.buffer.split("\n")
		for i in range(len(messages) - 1):
			message = messages[i].strip()
			if message:
				message_json = json.loads(message)
				Completion.message_queue.put(message_json)
				Completion.last_msg_id = message_json['id']
		Completion.buffer = messages[-1].strip()
		if Completion.buffer.endswith("}"):
			try:
				message_json = json.loads(Completion.buffer)
				Completion.message_queue.put(message_json)
				Completion.buffer = ""
			except json.JSONDecodeError:
				pass

	@staticmethod
	def get_response(prompt: str, proxy: Optional[str] = None) -> str:
		response_list = []
		for message in Completion.create(prompt, proxy):
			response_list.append(message)
		return ''.join(response_list)

	@staticmethod
	def reset():
		Completion.thread = None
		Completion.message_queue = Queue()
		Completion.stream_completed = False
		Completion.last_msg_id = None