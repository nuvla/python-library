# -*- coding: utf-8 -*-
from datetime import datetime, time, timezone, timedelta


def parse_nuvla_date(date: str) -> datetime:
    return datetime.fromisoformat(date[:-1] + '+00:00')


def nuvla_date(date: datetime) -> str:
    return date.astimezone(timezone.utc) \
        .isoformat('T', timespec='milliseconds') \
        .replace('+00:00', 'Z')


def utcnow() -> datetime:
    return datetime.utcnow()


def today_start_time() -> datetime:
    return datetime.combine(utcnow(), time.min)


def today_end_time() -> datetime:
    return datetime.combine(utcnow(), time.max)


def plus(date: datetime, td: timedelta) -> datetime:
    return date + td


def minus(date: datetime, td: timedelta) -> datetime:
    return date - td
