import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional

import nonebot
from fastapi import APIRouter, WebSocket
from nonebot.utils import escape_tag
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from tortoise.functions import Count
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from configs.config import NICKNAME
from models.chat_history import ChatHistory
from models.group_info import GroupInfo
from models.statistics import Statistics
from services.log import logger
from utils.manager import plugin_data_manager, plugins2settings_manager, plugins_manager

from ....base_model import Result
from ....config import QueryDateType
from ....utils import authentication, get_system_status
from .data_source import bot_live
from .model import ActiveGroup, BaseInfo, ChatHistoryCount, HotPlugin

AVA_URL = "http://q1.qlogo.cn/g?b=qq&nk={}&s=160"

GROUP_AVA_URL = "http://p.qlogo.cn/gh/{}/{}/640/"

run_time = time.time()

ws_router = APIRouter()
router = APIRouter()


@router.get("/get_base_info", dependencies=[authentication()], description="基础信息")
async def _(bot_id: Optional[str] = None) -> Result:
    """
    获取Bot基础信息

    Args:
        bot_id (Optional[str], optional): bot_id. Defaults to None.

    Returns:
        Result: 获取指定bot信息与bot列表
    """
    bot_list: List[BaseInfo] = []
    if bots := nonebot.get_bots():
        select_bot: BaseInfo
        for key, bot in bots.items():
            login_info = await bot.get_login_info()
            bot_list.append(
                BaseInfo(
                    bot=bot,  # type: ignore
                    self_id=bot.self_id,
                    nickname=login_info["nickname"],
                    ava_url=AVA_URL.format(bot.self_id),
                )
            )
        # 获取指定qq号的bot信息，若无指定   则获取第一个
        if _bl := [b for b in bot_list if b.self_id == bot_id]:
            select_bot = _bl[0]
        else:
            select_bot = bot_list[0]
        select_bot.is_select = True
        select_bot.config = select_bot.bot.config
        now = datetime.now()
        # 今日累计接收消息
        select_bot.received_messages = await ChatHistory.filter(
            bot_id=select_bot.self_id,
            create_time__gte=now - timedelta(hours=now.hour),
        ).count()
        # 群聊数量
        select_bot.group_count = len(await select_bot.bot.get_group_list())
        # 好友数量
        select_bot.friend_count = len(await select_bot.bot.get_friend_list())
        for bot in bot_list:
            bot.bot = None  # type: ignore
        # 插件加载数量
        select_bot.plugin_count = len(plugins2settings_manager)
        pm_data = plugins_manager.get_data()
        select_bot.fail_plugin_count = len([pd for pd in pm_data if pm_data[pd].error])
        select_bot.success_plugin_count = (
            select_bot.plugin_count - select_bot.fail_plugin_count
        )
        # 连接时间
        select_bot.connect_time = bot_live.get(select_bot.self_id) or 0
        if select_bot.connect_time:
            connect_date = datetime.fromtimestamp(select_bot.connect_time)
            select_bot.connect_date = connect_date.strftime("%Y-%m-%d %H:%M:%S")

        return Result.ok(bot_list, "拿到信息啦!")
    return Result.warning_("无Bot连接...")


@router.get(
    "/get_all_ch_count", dependencies=[authentication()], description="获取接收消息数量"
)
async def _(bot_id: str) -> Result:
    now = datetime.now()
    all_count = await ChatHistory.filter(bot_id=bot_id).count()
    day_count = await ChatHistory.filter(
        bot_id=bot_id, create_time__gte=now - timedelta(hours=now.hour)
    ).count()
    week_count = await ChatHistory.filter(
        bot_id=bot_id, create_time__gte=now - timedelta(days=7)
    ).count()
    month_count = await ChatHistory.filter(
        bot_id=bot_id, create_time__gte=now - timedelta(days=30)
    ).count()
    year_count = await ChatHistory.filter(
        bot_id=bot_id, create_time__gte=now - timedelta(days=365)
    ).count()
    return Result.ok(
        ChatHistoryCount(
            num=all_count,
            day=day_count,
            week=week_count,
            month=month_count,
            year=year_count,
        )
    )


@router.get("/get_ch_count", dependencies=[authentication()], description="获取接收消息数量")
async def _(bot_id: str, query_type: Optional[QueryDateType] = None) -> Result:
    if bots := nonebot.get_bots():
        if not query_type:
            return Result.ok(await ChatHistory.filter(bot_id=bot_id).count())
        now = datetime.now()
        if query_type == QueryDateType.DAY:
            return Result.ok(
                await ChatHistory.filter(
                    bot_id=bot_id, create_time__gte=now - timedelta(hours=now.hour)
                ).count()
            )
        if query_type == QueryDateType.WEEK:
            return Result.ok(
                await ChatHistory.filter(
                    bot_id=bot_id, create_time__gte=now - timedelta(days=7)
                ).count()
            )
        if query_type == QueryDateType.MONTH:
            return Result.ok(
                await ChatHistory.filter(
                    bot_id=bot_id, create_time__gte=now - timedelta(days=30)
                ).count()
            )
        if query_type == QueryDateType.YEAR:
            return Result.ok(
                await ChatHistory.filter(
                    bot_id=bot_id, create_time__gte=now - timedelta(days=365)
                ).count()
            )
    return Result.warning_("无Bot连接...")


@router.get("get_fg_count", dependencies=[authentication()], description="好友/群组数量")
async def _(bot_id: str) -> Result:
    if bots := nonebot.get_bots():
        if bot_id not in bots:
            return Result.warning_("指定Bot未连接...")
        bot = bots[bot_id]
        data = {
            "friend_count": len(await bot.get_friend_list()),
            "group_count": len(await bot.get_group_list()),
        }
        return Result.ok(data)
    return Result.warning_("无Bot连接...")


@router.get("/get_run_time", dependencies=[authentication()], description="获取nb运行时间")
async def _() -> Result:
    return Result.ok(int(time.time() - run_time))


@router.get("/get_active_group", dependencies=[authentication()], description="获取活跃群聊")
async def _(date_type: Optional[QueryDateType] = None) -> Result:
    query = ChatHistory
    now = datetime.now()
    if date_type == QueryDateType.DAY:
        query = ChatHistory.filter(create_time__gte=now - timedelta(hours=now.hour))
    if date_type == QueryDateType.WEEK:
        query = ChatHistory.filter(create_time__gte=now - timedelta(days=7))
    if date_type == QueryDateType.MONTH:
        query = ChatHistory.filter(create_time__gte=now - timedelta(days=30))
    if date_type == QueryDateType.YEAR:
        query = ChatHistory.filter(create_time__gte=now - timedelta(days=365))
    data_list = (
        await query.annotate(count=Count("id"))
        .group_by("group_id").order_by("-count").limit(5)
        .values_list("group_id", "count")
    )
    active_group_list = []
    id2name = {}
    if data_list:
        if info_list := await GroupInfo.filter(group_id__in=[x[0] for x in data_list]).all():
            for group_info in info_list:
                id2name[group_info.group_id] = group_info.group_name
    for data in data_list:
        active_group_list.append(
            ActiveGroup(
                group_id=data[0],
                name=id2name.get(data[0]) or data[0],
                chat_num=data[1],
                ava_img=GROUP_AVA_URL.format(data[0], data[0]),
            )
        )
    active_group_list = sorted(
        active_group_list, key=lambda x: x.chat_num, reverse=True
    )
    if len(active_group_list) > 5:
        active_group_list = active_group_list[:5]
    return Result.ok(active_group_list)


@router.get("/get_hot_plugin", dependencies=[authentication()], description="获取热门插件")
async def _(date_type: Optional[QueryDateType] = None) -> Result:
    query = Statistics
    now = datetime.now()
    if date_type == QueryDateType.DAY:
        query = Statistics.filter(create_time__gte=now - timedelta(hours=now.hour))
    if date_type == QueryDateType.WEEK:
        query = Statistics.filter(create_time__gte=now - timedelta(days=7))
    if date_type == QueryDateType.MONTH:
        query = Statistics.filter(create_time__gte=now - timedelta(days=30))
    if date_type == QueryDateType.YEAR:
        query = Statistics.filter(create_time__gte=now - timedelta(days=365))
    data_list = (
        await query.annotate(count=Count("id"))
        .group_by("plugin_name").order_by("-count").limit(5)
        .values_list("plugin_name", "count")
    )
    hot_plugin_list = []
    for data in data_list:
        name = data[0]
        if plugin_data := plugin_data_manager.get(data[0]):
            name = plugin_data.name
        hot_plugin_list.append(
            HotPlugin(
                module=data[0],
                name=name,
                count=data[1],
            )
        )
    hot_plugin_list = sorted(hot_plugin_list, key=lambda x: x.count, reverse=True)
    if len(hot_plugin_list) > 5:
        hot_plugin_list = hot_plugin_list[:5]
    return Result.ok(hot_plugin_list)


@ws_router.websocket("/system_status")
async def system_logs_realtime(websocket: WebSocket):
    await websocket.accept()
    logger.debug("ws system_status is connect")
    try:
        while websocket.client_state == WebSocketState.CONNECTED:
            system_status = await get_system_status()
            await websocket.send_text(system_status.json())
            await asyncio.sleep(5)
    except (WebSocketDisconnect, ConnectionClosedError, ConnectionClosedOK):
        pass
    return
