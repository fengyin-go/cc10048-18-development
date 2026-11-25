"""实验转化导入与评估：文件导入、真实曝光组归集、幂等去重、报告版本回查。

场景：上传 A 组已有两个转化的文件并发出报告 → 改分组 → 同一早期转化再导入两次
→ 从原周期再次发起评估 → 新报告去重且仍按真实曝光组归集，旧版报告仍可查。
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXP_ID = 1
PERIOD = {"period_start": "2026-09-01", "period_end": "2026-09-01"}

# 第一份资料：A组主体 U-1001 / U-1002 各一笔转化，另含一条无曝光主体
FILE_ONE = (
    "回执号,主体标识,转化时间,渠道\n"
    "RCPT-9001,U-1001,2026-09-01 12:00:00,渠道甲\n"
    "RCPT-9002,U-1002,2026-09-01 13:10:00,渠道甲\n"
    "RCPT-9003,U-9999,2026-09-01 14:00:00,渠道甲\n"
)
# 补报文件一：重复回执 RCPT-9001（晚到，属原统计期）
FILE_TWO = (
    "回执号,主体标识,转化时间,渠道\n"
    "RCPT-9001,U-1001,2026-09-01 12:00:00,渠道甲\n"
)
# 补报文件二：再次重复同一回执
FILE_THREE = (
    "回执号,主体标识,转化时间,渠道\n"
    "RCPT-9001,U-1001,2026-09-01 12:00:00,渠道乙\n"
)


def _import(filename: str, content: str):
    return client.post(
        f"/api/domain/experiment/{EXP_ID}/conversions/import",
        json={"filename": filename, "content": content},
    )


class TestConversionImport:
    def test_import_matches_real_exposure_group(self):
        resp = _import("file-one.csv", FILE_ONE)
        assert resp.status_code == 200
        data = resp.json()
        assert data["file"]["total"] == 3
        assert data["file"]["matched"] == 2
        assert data["file"]["unmatched"] == 1
        by_receipt = {event["receipt_id"]: event for event in data["events"]}
        # 组别来自已登记的真实曝光（A组），与实验配置字段无关
        assert by_receipt["RCPT-9001"]["group"] == "A组"
        assert by_receipt["RCPT-9001"]["counted"] is True
        assert by_receipt["RCPT-9002"]["group"] == "A组"
        # 未匹配曝光的记录给出单独原因
        assert by_receipt["RCPT-9003"]["status"] == "未匹配曝光"
        assert "无已登记曝光" in by_receipt["RCPT-9003"]["reason"]
        assert by_receipt["RCPT-9003"]["counted"] is False

    def test_import_rejects_empty_content(self):
        resp = _import("empty.csv", "")
        assert resp.status_code == 400

    def test_import_rejects_unknown_experiment(self):
        resp = client.post(
            "/api/domain/experiment/99999/conversions/import",
            json={"filename": "x.csv", "content": FILE_ONE},
        )
        assert resp.status_code == 400

    def test_exposures_listing(self):
        resp = client.get(f"/api/domain/experiment/{EXP_ID}/exposures")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 10
        groups = {item["subject_id"]: item["group"] for item in data["items"]}
        assert groups["U-1001"] == "A组"
        assert groups["U-2001"] == "B组"


class TestEvaluateAndReports:
    def test_first_evaluation_issues_report(self):
        resp = client.post(f"/api/domain/experiment/{EXP_ID}/evaluate", json=PERIOD)
        assert resp.status_code == 200
        report = resp.json()
        assert report["version"] == 1
        assert report["is_latest"] is True
        assert report["period"] == {"start": "2026-09-01", "end": "2026-09-01"}
        # 分别给出实际参与评估的曝光和转化
        assert report["totals"] == {"exposures": 10, "conversions": 2}
        groups = {item["group"]: item for item in report["groups"]}
        assert groups["A组"]["exposures"] == 5
        assert groups["A组"]["conversions"] == 2
        assert groups["A组"]["conversion_rate"] == 0.4
        assert groups["B组"]["exposures"] == 5
        assert groups["B组"]["conversions"] == 0
        # 标出采用的文件及曝光时间范围
        assert [f["filename"] for f in report["source_files"]] == ["file-one.csv"]
        assert report["exposure_range"]["start"] == "2026-09-01 09:12:00"
        assert report["exposure_range"]["end"] == "2026-09-01 15:47:00"
        # 未匹配曝光的记录以单独原因给出
        assert len(report["unmatched_records"]) == 1
        assert report["unmatched_records"][0]["receipt_id"] == "RCPT-9003"
        assert report["unmatched_records"][0]["reason"]

    def test_change_grouping_config(self):
        """改分组：调整实验配置，不影响已登记曝光与已导入转化的组别。"""
        resp = client.put(
            f"/api/experiment/{EXP_ID}",
            json={"values": {"对照组": "改后对照组", "实验组": "改后实验组", "样本比例": "30/70"}},
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        entry = client.get(f"/api/experiment/{EXP_ID}").json()
        assert entry["对照组"] == "改后对照组"

    def test_duplicate_receipts_counted_once(self):
        resp2 = _import("file-two.csv", FILE_TWO)
        assert resp2.status_code == 200
        assert resp2.json()["file"]["duplicate"] == 1
        assert resp2.json()["file"]["matched"] == 0
        resp3 = _import("file-three.csv", FILE_THREE)
        assert resp3.status_code == 200
        assert resp3.json()["file"]["duplicate"] == 1
        # 台账中重复记录保留原因，但不参与统计
        events = client.get(f"/api/domain/experiment/{EXP_ID}/conversions").json()["events"]
        counted = [e for e in events if e["receipt_id"] == "RCPT-9001" and e["counted"]]
        assert len(counted) == 1
        duplicates = [e for e in events if e["receipt_id"] == "RCPT-9001" and not e["counted"]]
        assert len(duplicates) == 2
        assert all(e["status"] == "重复回执" for e in duplicates)

    def test_second_evaluation_from_original_period(self):
        resp = client.post(f"/api/domain/experiment/{EXP_ID}/evaluate", json=PERIOD)
        assert resp.status_code == 200
        report = resp.json()
        assert report["version"] == 2
        assert report["is_latest"] is True
        # 改分组后仍按真实曝光组归集；同一回执只计一次
        assert report["totals"] == {"exposures": 10, "conversions": 2}
        groups = {item["group"]: item for item in report["groups"]}
        assert groups["A组"]["conversions"] == 2
        assert "真实曝光组" in report["grouping_basis"]
        # 来源文件仍是首次计入的那份；重复回执单独列出
        assert [f["filename"] for f in report["source_files"]] == ["file-one.csv"]
        assert len(report["duplicate_records"]) == 2
        assert {d["filename"] for d in report["duplicate_records"]} == {"file-two.csv", "file-three.csv"}

    def test_reports_list_and_old_version_queryable(self):
        resp = client.get(f"/api/domain/experiment/{EXP_ID}/reports")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2
        latest = [item for item in items if item["is_latest"]]
        assert len(latest) == 1
        assert latest[0]["version"] == 2
        # 旧版报告仍可查，内容保持发出时的快照
        old_id = [item for item in items if item["version"] == 1][0]["id"]
        old = client.get(f"/api/domain/experiment/{EXP_ID}/reports/{old_id}")
        assert old.status_code == 200
        old_report = old.json()
        assert old_report["is_latest"] is False
        assert old_report["totals"]["conversions"] == 2
        assert old_report["duplicate_records"] == []
        assert [f["filename"] for f in old_report["source_files"]] == ["file-one.csv"]

    def test_report_detail_not_found(self):
        resp = client.get(f"/api/domain/experiment/{EXP_ID}/reports/99999")
        assert resp.status_code == 404

    def test_evaluate_rejects_bad_period(self):
        resp = client.post(
            f"/api/domain/experiment/{EXP_ID}/evaluate",
            json={"period_start": "2026-09-10", "period_end": "2026-09-01"},
        )
        assert resp.status_code == 400

    def test_health_still_18_modules(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["modules"] == 18
