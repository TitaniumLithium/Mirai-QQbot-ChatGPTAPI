from graia.ariadne.app import Ariadne
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.model import Friend, Group
from graia.ariadne.message import Source
from graia.ariadne.message.parser.base import MentionMe
from graia.ariadne.connection.config import (
    HttpClientConfig,
    WebsocketClientConfig,
    config as ariadne_config,
)

from revChatGPT.V3 import Chatbot
from loguru import logger
import json

with open('config.json') as json_file:
    botconfig = json.load(json_file)

logger.info(botconfig)

chatgpt = Chatbot(
    api_key=botconfig.get("openai").get("openai_api_key"),
    max_tokens=botconfig.get("openai").get("max_tokens")
)

app = Ariadne(
    ariadne_config(
        botconfig.get("mirai").get("qq"),
        botconfig.get("mirai").get("mirai_api_key"),
        HttpClientConfig(host=botconfig.get("mirai").get("http_url")),
        WebsocketClientConfig(host=botconfig.get("mirai").get("ws_url")),
    ),
)

# 群聊信息


@app.broadcast.receiver("GroupMessage")
async def group_message_listener(app: Ariadne, group: Group, source: Source, chain: MessageChain = MentionMe()):
    logger.debug(chain.display)
    if "/reset" in chain.display:
        # 重置会话reset conversation
        chatgpt.conversation = [
            {
                "role": "system",
                "content": "You are ChatGPT, a large language model trained by OpenAI. Respond conversationally",
            },
        ]
        logger.info("conversation reset")
        await app.send_message(group, MessageChain([Plain("conversation reset")]), quote=source)
        return
    response = chatgpt.ask(
        chain.display, "user", temperature=botconfig.get("openai").get("temperature"))
    logger.info(response)
    await app.send_message(group, MessageChain([Plain(response)]), quote=source)

# 私人信息 只会hello world


@app.broadcast.receiver("FriendMessage")
async def friend_message_listener(app: Ariadne, friend: Friend):
    await app.send_message(friend, MessageChain([Plain("Hello, World!")]))

app.launch_blocking()
