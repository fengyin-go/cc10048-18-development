"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from typing import Any

from app.seed import SEED_EXPOSURES, SEED_ROWS


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }
        # 实验评估域：已登记曝光、转化导入文件、转化事件、评估报告版本。
        # 与 18 个业务模块的 _tables 分开存放，不参与模块计数与概览汇总。
        self._exposures: list[dict[str, Any]] = [dict(row) for row in SEED_EXPOSURES]
        self._conversion_files: list[dict[str, Any]] = []
        self._conversions: list[dict[str, Any]] = []
        self._eval_reports: list[dict[str, Any]] = []
        self._eval_seq = {"file": 0, "conversion": 0, "report": 0}

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    # ---- 实验评估域存储 ----
    def exposures(self) -> list[dict[str, Any]]:
        """已登记的曝光明细（真实曝光组别以这里为准）。"""
        return self._exposures

    def conversion_files(self) -> list[dict[str, Any]]:
        """转化明细导入文件台账。"""
        return self._conversion_files

    def conversions(self) -> list[dict[str, Any]]:
        """导入的转化事件明细（含匹配状态与来源文件）。"""
        return self._conversions

    def eval_reports(self) -> list[dict[str, Any]]:
        """已发出的评估报告版本（快照，发出后不可改）。"""
        return self._eval_reports

    def next_eval_id(self, kind: str) -> int:
        self._eval_seq[kind] += 1
        return self._eval_seq[kind]

    def overview(self) -> dict[str, object]:
        modules: list[dict[str, object]] = []
        for name in self.module_names():
            rows = self.rows(name)
            modules.append({
                "name": name,
                "created": len(rows),
                "pending": sum(1 for row in rows if row.get("pending")),
                "abnormal": sum(1 for row in rows if row.get("abnormal")),
            })
        cards = [
            {"label": "业务模块", "value": len(modules)},
            {"label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
            {"label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"cards": cards, "modules": modules}


store = Store()
