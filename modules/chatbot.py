from json import loads
from queue import Queue, Empty
from re import findall
from threading import Thread
from typing import Generator, Optional
from curl_cffi import requests
from fake_useragent import UserAgent

class Completion:
    # experimental
    part1 = '{"role":"assistant","id":"chatcmpl'
    part2 = '"},"index":0,"finish_reason":null}]}}'
    regex = rf'{part1}(.*){part2}'

    timer = None
    message_queue = Queue()
    stream_completed = False
    last_msg_id = None
    thread = None

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

        try:
            response = requests.post(
                'https://chatbot.theb.ai/api/chat-process',
                headers=headers,
                proxies=proxies,
                content_callback=Completion.handle_stream_response,
                json={'prompt': prompt, 'options': options},
                timeout=100000
            )

            response.raise_for_status()
            Completion.stream_completed = True

        except Exception as e:
            print(f"An error occurred while sending the request: {e}")
            Completion.stream_completed = True

    @staticmethod
    def create(prompt: str, proxy: Optional[str] = None) -> Generator[str, None, None]:
        Completion.stream_completed = False

        Completion.thread = Thread(target=Completion.request, args=[prompt, proxy])
        Completion.thread.start()

        while not Completion.stream_completed or not Completion.message_queue.empty():
            try:
                message = Completion.message_queue.get(timeout=0.01)
                for message in findall(Completion.regex, message):
                    message_json = loads(Completion.part1 + message + Completion.part2)
                    Completion.last_msg_id = message_json['id']
                    yield message_json['text']

            except Empty:
                pass

        Completion.message_queue.queue.clear()

    @staticmethod
    def handle_stream_response(response):
        Completion.message_queue.put(response.decode())

    @staticmethod
    def get_response(prompt: str, proxy: Optional[str] = None) -> Optional[str]:
        response_list = []
        try:
            for message in Completion.create(prompt, proxy):
                response_list.append(message)

            if response_list:
                return response_list[-1]

        except Exception as e:
            print(f"An error occurred while getting the response: {e}")

        return None

    @staticmethod
    def reset():
        Completion.stream_completed = False
        Completion.last_msg_id = None
        if Completion.thread is not None:
            Completion.thread.join()
            Completion.thread = None
        Completion.message_queue.queue.clear()