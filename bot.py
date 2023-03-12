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
from typing_extensions import Annotated
from graia.ariadne.message.commander import Commander
from graia.ariadne.event.message import MessageEvent

from revChatGPT.V3 import Chatbot
from loguru import logger
import json

with open('config.json', 'r', encoding="UTF-8") as json_file:
    botconfig = json.load(json_file)

logger.info(botconfig)

# 群聊隔离
Group_Chats = {}

app = Ariadne(
    ariadne_config(
        botconfig.get("mirai").get("qq"),
        botconfig.get("mirai").get("mirai_api_key"),
        HttpClientConfig(host=botconfig.get("mirai").get("http_url")),
        WebsocketClientConfig(host=botconfig.get("mirai").get("ws_url")),
    ),
)


@app.broadcast.receiver("GroupMessage")
# 群聊信息
async def group_message_listener(app: Ariadne, group: Group, source: Source, chain: MessageChain = MentionMe()):
    logger.debug(chain.display)
    if group.id not in Group_Chats:
        # init a chat
        Group_Chats[group.id] = Chatbot(
            api_key=botconfig.get("openai").get("openai_api_key"),
            max_tokens=botconfig.get("openai").get("max_tokens"),
            temperature=botconfig.get("openai").get("temperature")
        )
        logger.debug("Group.id added to dict")
    response = Group_Chats[group.id].ask(chain.display)
    logger.debug(response)

    await app.send_message(group, MessageChain([Plain(response)]), quote=source)

cmd = Commander(app.broadcast)

help_msg = ".help 帮助 .reset 重置会话 .preset 重置并使用预设会话 当前可使用预设：猫娘 .temparature 修改情感值0-1.0 基础0.5 数值越高回复字数越多"


@cmd.command(".help")
async def bot_help(app: Ariadne, sender: Group):
    await app.send_message(sender, MessageChain([Plain(help_msg)]))


@cmd.command(".reset")
async def bot_reset(app: Ariadne, sender: Group):
    if sender.id in Group_Chats:
        Group_Chats[sender.id].reset()
        logger.debug(str(sender.id) + "conversation reset")
        await app.send_message(sender, MessageChain([Plain("conversation reset")]))
    else:
        Group_Chats[sender.id] = Chatbot(
            api_key=botconfig.get("openai").get("openai_api_key"),
            max_tokens=botconfig.get("openai").get("max_tokens"),
            temperature=botconfig.get("openai").get("temperature")
        )
        logger.debug(str(sender.id) + "Group.id added to dict by reset")


@cmd.command(".temperature {value: str}")
async def bot_temperature(app: Ariadne, sender: Group, value: str):
    try:
        value_float: float
        value_float = float(value)
        logger.debug(type(value_float))
        if value_float < 0 or value_float > 1:
            await app.send_message(sender, MessageChain([Plain("Please check the value 0-1")]))
            return
        if sender.id in Group_Chats:
            Group_Chats[sender.id].temperature = value_float
            logger.debug(str(sender.id) + "temperature set")
            await app.send_message(sender, MessageChain([Plain("temprature set to " + value)]))
    except Exception as e:
        await app.send_message(sender, MessageChain([Plain("Please check the value 0-1")]))


@cmd.command(".preset {preset: str}")
async def bot_preset(app: Ariadne, sender: Group, preset: str):
    preset_prompt: list
    preset_prompt = botconfig.get("presets").get(preset)
    logger.debug(preset_prompt)
    if preset_prompt is None:
        await app.send_message(sender, MessageChain([Plain("preset applied failed: preset does not exit " + preset)]))
        return
    if sender.id in Group_Chats:
        Group_Chats[sender.id].reset()
        Group_Chats[sender.id].conversation["default"] = preset_prompt
        await app.send_message(sender, MessageChain([Plain("preset applied: " + preset)]))
    else:
        Group_Chats[sender.id] = Chatbot(
            api_key=botconfig.get("openai").get("openai_api_key"),
            max_tokens=botconfig.get("openai").get("max_tokens"),
            temperature=botconfig.get("openai").get("temperature")
        )
        Group_Chats[sender.id].conversation["default"] = preset_prompt
        await app.send_message(sender, MessageChain([Plain("preset applied: " + preset)]))
        logger.debug(str(sender.id) + "Group.id added to dict by preset")


@app.broadcast.receiver("FriendMessage")
# 私人信息
async def friend_message_listener(app: Ariadne, friend: Friend):
    await app.send_message(friend, MessageChain([Plain("喵 我只会在群聊聊天QAQ")]))

app.launch_blocking()
