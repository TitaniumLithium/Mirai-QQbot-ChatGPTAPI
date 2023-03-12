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

with open('config.json','r',encoding="UTF-8") as json_file:
    botconfig = json.load(json_file)

logger.info(botconfig)

#群聊隔离
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
    if Group.id not in Group_Chats:
    #init a chat
        Group_Chats[Group.id] = Chatbot(
            api_key=botconfig.get("openai").get("openai_api_key"),
            max_tokens=botconfig.get("openai").get("max_tokens"),
            temperature=botconfig.get("openai").get("temperature")
        )
        logger.debug("Group.id added to dict")

    if "/reset" in chain.display:
        # 重置会话reset conversation
        Group_Chats[Group.id].reset()
        logger.info("conversation reset")
        await app.send_message(group, MessageChain([Plain("conversation reset")]), quote=source)
        return
    
    response = Group_Chats[Group.id].ask(chain.display)
    logger.info(response)
    
    await app.send_message(group, MessageChain([Plain(response)]), quote=source)

cmd = Commander(app.broadcast)

help_msg = '''
.help 帮助
.reset 重置会话
.preset 重置并使用预设会话 当前可使用预设：猫娘
.temparature 修改情感值0-1.0 基础0.5 数值越高回复字数越多
'''

@cmd.command(".help")
async def bot_help(app: Ariadne, event: MessageEvent, sender: Group):
    await app.send_message(MessageEvent, MessageChain([Plain(help_msg)]))

@cmd.command(".reset")
async def bot_reset(app: Ariadne, event: MessageEvent, sender: Group):
    if Group.id in Group_Chats:
        Group_Chats[Group.id].reset()
        logger.info(Group.id + " conversation reset")
        await app.send_message(sender, MessageChain([Plain("conversation reset")]))
    else:
        Group_Chats[Group.id] = Chatbot(
            api_key=botconfig.get("openai").get("openai_api_key"),
            max_tokens=botconfig.get("openai").get("max_tokens"),
            temperature=botconfig.get("openai").get("temperature")
        )
        logger.debug("Group.id added to dict by reset")

@cmd.command(".temperature {value: float}")
async def bot_temperature(app: Ariadne, event: MessageEvent, sender: Group, value: float):
    if Group.id in Group_Chats:
        Group_Chats[Group.id].temperature = value
        logger.debug("temperature set")
        await app.send_message(sender, MessageChain([Plain("temprature set to " +  value)]))    

@cmd.command(".preset {preset: str}")
async def bot_preset(app: Ariadne, event: MessageEvent, sender: Group, preset: str):
    preset_prompt : list
    preset_prompt = botconfig.get("presets").get(preset)
    logger.debug(preset_prompt)
    if preset_prompt is None:
        await app.send_message(sender, MessageChain([Plain("preset applied failed: preset does not exit " +  preset)])) 
        return
    if Group.id in Group_Chats:
        Group_Chats[Group.id].reset()
        Group_Chats[Group.id].conversation["default"] = preset_prompt
        await app.send_message(sender, MessageChain([Plain("preset applied: " +  preset)])) 
    else:
        Group_Chats[Group.id] = Chatbot(
            api_key=botconfig.get("openai").get("openai_api_key"),
            max_tokens=botconfig.get("openai").get("max_tokens"),
            temperature=botconfig.get("openai").get("temperature")
        )
        Group_Chats[Group.id].conversation["default"] = preset_prompt
        await app.send_message(sender, MessageChain([Plain("preset applied: " +  preset)])) 
        logger.debug("Group.id added to dict by preset")

@app.broadcast.receiver("FriendMessage")
# 私人信息
async def friend_message_listener(app: Ariadne, friend: Friend):
    await app.send_message(friend, MessageChain([Plain("喵 我只会在群聊聊天QAQ")]))

app.launch_blocking()
