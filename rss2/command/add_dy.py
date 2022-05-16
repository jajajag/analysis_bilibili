from typing import Optional

from nonebot import on_command, CommandSession
from .. import my_trigger as tr
from ..rss_class import Rss
from ..permission import admin_permission

prompt = """\
请输入
    名称 [订阅地址]
空格分割、[]表示可选
私聊默认订阅到当前账号，群聊默认订阅到当前群组
更多信息可通过 change 命令修改\
"""


@on_command(
    "add",
    aliases=("添加订阅", "sub"),
    permission=admin_permission,
    only_to_me=False,
)
async def add(session: CommandSession) -> None:
    rss_dy_link = (await session.aget("add", prompt=prompt)).strip()

    try:
        name, url = rss_dy_link.split(" ")
    except ValueError:
        await session.finish("❌ 请输入正确的格式！")

    user_id = session.ctx["user_id"]
    group_id = session.ctx.get("group_id")
    guild_channel_id = session.ctx.get("guild_id")
    if guild_channel_id:
        group_id = None
        guild_channel_id = guild_channel_id + "@" + session.ctx.get("channel_id")

    rss = Rss()
    rss.name = name
    rss.url = url
    await add_feed(session, rss, user_id, group_id, guild_channel_id)


async def add_feed(
    session: CommandSession,
    rss: Rss,
    user_id: Optional[str],
    group_id: Optional[int],
    guild_channel_id: Optional[str],
) -> None:
    if guild_channel_id:
        rss.add_user_or_group(guild_channel=guild_channel_id)
        await tr.add_job(rss)
        await session.finish("👏 订阅到当前子频道成功！")
    elif group_id:
        rss.add_user_or_group(group=str(group_id))
        await tr.add_job(rss)
        await session.finish("👏 订阅到当前群组成功！")
    else:
        rss.add_user_or_group(user=user_id)
        await tr.add_job(rss)
        await session.finish("👏 订阅到当前账号成功！")


# add.args_parser 装饰器将函数声明为 add 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@add.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空，意味着用户直接将订阅信息跟在命令名后面，作为参数传入
            # 例如用户可能发送了：订阅 test1 /twitter/user/key_official 1447027111 1037939056 1 true true #订阅名 订阅地址 qq 群组 更新时间 代理 第三方
            session.state["add"] = stripped_arg
        return

    if not stripped_arg:
        # 用户没有发送有效的订阅（而是发送了空白字符），则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause("输入不能为空！")

    # 如果当前正在向用户询问更多信息（例如本例中的要压缩的链接），且用户输入有效，则放入会话状态
    session.state[session.current_key] = stripped_arg