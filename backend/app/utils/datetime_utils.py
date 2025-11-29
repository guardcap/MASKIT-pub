# backend/app/utils/datetime_utils.py
"""
한국 시간(KST, UTC+9) 유틸리티
"""
from datetime import datetime, timedelta
from typing import Optional
import pytz

# 한국 표준시 타임존
KST = pytz.timezone('Asia/Seoul')


def get_kst_now() -> datetime:
    """
    현재 한국 시간을 반환 (timezone-aware)
    
    Returns:
        datetime: 한국 시간 (timezone-aware)
    """
    return datetime.now(KST)


def utc_to_kst(utc_dt: datetime) -> datetime:
    """
    UTC 시간을 한국 시간으로 변환
    
    Args:
        utc_dt: UTC datetime 객체 (timezone-aware 또는 naive)
        
    Returns:
        datetime: 한국 시간으로 변환된 datetime 객체
    """
    if utc_dt.tzinfo is None:
        # naive datetime은 UTC로 간주
        utc_dt = pytz.utc.localize(utc_dt)
    
    return utc_dt.astimezone(KST)


def kst_to_utc(kst_dt: datetime) -> datetime:
    """
    한국 시간을 UTC로 변환
    
    Args:
        kst_dt: 한국 시간 datetime 객체
        
    Returns:
        datetime: UTC로 변환된 datetime 객체
    """
    if kst_dt.tzinfo is None:
        # naive datetime은 KST로 간주
        kst_dt = KST.localize(kst_dt)
    
    return kst_dt.astimezone(pytz.utc)


def format_kst(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    datetime을 한국 시간 문자열로 포맷
    
    Args:
        dt: datetime 객체
        format_str: 포맷 문자열
        
    Returns:
        str: 포맷된 한국 시간 문자열
    """
    if dt.tzinfo is None:
        # naive datetime은 UTC로 간주하고 KST로 변환
        dt = pytz.utc.localize(dt)
    
    kst_dt = dt.astimezone(KST)
    return kst_dt.strftime(format_str)


def parse_kst(date_string: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    한국 시간 문자열을 datetime으로 파싱
    
    Args:
        date_string: 날짜 문자열
        format_str: 포맷 문자열
        
    Returns:
        datetime: timezone-aware datetime 객체 (KST)
    """
    naive_dt = datetime.strptime(date_string, format_str)
    return KST.localize(naive_dt)


def get_kst_date_range(days: int = 7) -> tuple[datetime, datetime]:
    """
    현재부터 N일 전까지의 한국 시간 범위 반환
    
    Args:
        days: 일 수
        
    Returns:
        tuple: (시작 시간, 종료 시간) - 둘 다 KST
    """
    end_time = get_kst_now()
    start_time = end_time - timedelta(days=days)
    return start_time, end_time


# 호환성을 위한 별칭
def get_kst_timestamp() -> datetime:
    """get_kst_now()의 별칭"""
    return get_kst_now()