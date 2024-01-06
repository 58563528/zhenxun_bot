from datetime import datetime
from typing import Optional, Union

from nonebot.adapters.onebot.v11 import Bot
from nonebot.config import Config
from pydantic import BaseModel


class SystemStatus(BaseModel):
    """
    系统状态
    """

    cpu: float
    memory: float
    disk: float


class BaseInfo(BaseModel):
    """
    基础信息
    """

    bot: Bot
    """Bot"""
    self_id: str
    """SELF ID"""
    nickname: str
    """昵称"""
    ava_url: str
    """头像url"""
    friend_count: int = 0
    """好友数量"""
    group_count: int = 0
    """群聊数量"""
    received_messages: int = 0
    """今日 累计接收消息"""
    # received_messages_day: int = 0
    # """今日累计接收消息"""
    # received_messages_week: int = 0
    # """一周内累计接收消息"""
    # received_messages_month: int = 0
    # """一月内累计接收消息"""
    # received_messages_year: int = 0
    # """一年内累计接受消息"""
    connect_time: int = 0
    """连接时间"""
    connect_date: Optional[datetime] = None
    """连接日期"""

    plugin_count: int = 0
    """加载插件数量"""
    success_plugin_count: int = 0
    """加载成功插件数量"""
    fail_plugin_count: int = 0
    """加载失败插件数量"""

    is_select: bool = False
    """当前选择"""

    config: Optional[Config] = None
    """nb配置"""

    class Config:
        arbitrary_types_allowed = True


class ChatHistoryCount(BaseModel):
    """
    聊天记录数量
    """

    num: int
    """总数"""
    day: int
    """一天内"""
    week: int
    """一周内"""
    month: int
    """一月内"""
    year: int
    """一年内"""


class ActiveGroup(BaseModel):
    """
    活跃群聊数据
    """

    group_id: Union[str, int]
    """群组id"""
    name: str
    """群组名称"""
    chat_num: int
    """发言数量"""
    ava_img: str
    """群组头像"""


class HotPlugin(BaseModel):
    """
    热门插件
    """

    module: str
    """模块名"""
    name: str
    """插件名称"""
    count: int
    """调用次数"""
