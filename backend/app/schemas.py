"""通用接口契约；模块字段由领域服务持有，不再为每个模块复制一份模型类。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    size: int = 20


class ActionResult(BaseModel):
    ok: bool
    message: str
    entry: dict[str, Any] | None = None


class EntryPayload(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)
    remark: str | None = None


class ActionPayload(BaseModel):
    action: str
    remark: str | None = None


class ConversionImportPayload(BaseModel):
    """转化明细文件导入：文件名 + CSV 文本内容。"""
    filename: str = ""
    content: str = ""


class EvaluatePayload(BaseModel):
    """实验评估入参：统计期留空时回退到实验方案的开始/结束日期。"""
    period_start: str | None = None
    period_end: str | None = None
