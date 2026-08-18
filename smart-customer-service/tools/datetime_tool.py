"""日期时间工具"""
from datetime import datetime
from zoneinfo import ZoneInfo
from langchain.tools import tool


@tool()
def get_current_datetime():
    """
    获取当前的日期和时间（北京时间）
    """
    tz = ZoneInfo("Asia/Shanghai")
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S")