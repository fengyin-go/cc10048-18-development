"""领域业务操作接口：每个模块的计算/处理/聚合等真实业务操作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas import ConversionImportPayload, EvaluatePayload
from app.services import SERVICES

router = APIRouter(prefix="/api/domain", tags=["领域业务"])


def _experiment_service():
    from app.services.experiment import ExperimentService
    svc = SERVICES.get("experiment")
    if not svc or not isinstance(svc, ExperimentService):
        raise HTTPException(404, "实验管理服务不可用")
    return svc


@router.get("/metric_def/{metric_id}/compute")
def metric_compute(metric_id: int) -> dict[str, Any]:
    """指标聚合计算。"""
    from app.services.metric_def import MetricDefService
    svc = SERVICES.get("metric_def")
    if not svc or not isinstance(svc, MetricDefService):
        raise HTTPException(404, "指标口径服务不可用")
    return svc.domain_compute(metric_id)


@router.get("/dim_query/{query_id}/execute")
def dim_query_execute(query_id: int) -> dict[str, Any]:
    """多维交叉查询执行。"""
    from app.services.dim_query import DimQueryService
    svc = SERVICES.get("dim_query")
    if not svc or not isinstance(svc, DimQueryService):
        raise HTTPException(404, "多维查询服务不可用")
    return svc.execute_query(query_id)


@router.get("/experiment/{experiment_id}/compute-effect")
def experiment_compute(experiment_id: int) -> dict[str, Any]:
    """实验效果计算。"""
    svc = _experiment_service()
    return svc.compute_effect(experiment_id)


@router.get("/experiment/{experiment_id}/exposures")
def experiment_exposures(experiment_id: int) -> dict[str, Any]:
    """该实验已登记的曝光明细（真实曝光组别以此为准）。"""
    svc = _experiment_service()
    if svc.get_entry(experiment_id) is None:
        raise HTTPException(404, f"实验方案 {experiment_id} 不存在")
    items = svc.list_exposures(experiment_id)
    return {"items": items, "total": len(items)}


@router.post("/experiment/{experiment_id}/conversions/import")
def experiment_import_conversions(
    experiment_id: int, payload: ConversionImportPayload
) -> dict[str, Any]:
    """从文件导入渠道转化事件明细，按真实曝光组形成可评估转化数据。"""
    svc = _experiment_service()
    result, error = svc.import_conversions(experiment_id, payload.filename, payload.content)
    if result is None:
        raise HTTPException(400, error)
    return result


@router.get("/experiment/{experiment_id}/conversions")
def experiment_conversions(experiment_id: int) -> dict[str, Any]:
    """该实验的导入文件台账与转化事件明细（含未匹配原因）。"""
    svc = _experiment_service()
    if svc.get_entry(experiment_id) is None:
        raise HTTPException(404, f"实验方案 {experiment_id} 不存在")
    return svc.list_conversion_events(experiment_id)


@router.post("/experiment/{experiment_id}/evaluate")
def experiment_evaluate(experiment_id: int, payload: EvaluatePayload) -> dict[str, Any]:
    """按统计期发起评估并发出新版报告（晚到转化归入原统计期）。"""
    svc = _experiment_service()
    report, error = svc.evaluate(experiment_id, payload.period_start, payload.period_end)
    if report is None:
        raise HTTPException(400, error)
    return report


@router.get("/experiment/{experiment_id}/reports")
def experiment_reports(experiment_id: int) -> dict[str, Any]:
    """该实验已发出的全部报告版本，最新版标记为可领取。"""
    svc = _experiment_service()
    if svc.get_entry(experiment_id) is None:
        raise HTTPException(404, f"实验方案 {experiment_id} 不存在")
    items = svc.list_reports(experiment_id)
    return {"items": items, "total": len(items)}


@router.get("/experiment/{experiment_id}/reports/{report_id}")
def experiment_report_detail(experiment_id: int, report_id: int) -> dict[str, Any]:
    """回查指定版本的评估报告快照（旧版结果保持原样）。"""
    svc = _experiment_service()
    report = svc.get_report(experiment_id, report_id)
    if report is None:
        raise HTTPException(404, f"实验 {experiment_id} 的评估报告 {report_id} 不存在")
    return report


@router.get("/significance/{task_id}/run-test")
def significance_run_test(task_id: int) -> dict[str, Any]:
    """显著性检验执行。"""
    from app.services.significance import SignificanceService
    svc = SERVICES.get("significance")
    if not svc or not isinstance(svc, SignificanceService):
        raise HTTPException(404, "显著性检验服务不可用")
    return svc.run_test(task_id)


@router.get("/cohort/{cohort_id}/estimate-scale")
def cohort_estimate(cohort_id: int) -> dict[str, Any]:
    """人群规模预估。"""
    from app.services.cohort import CohortService
    svc = SERVICES.get("cohort")
    if not svc or not isinstance(svc, CohortService):
        raise HTTPException(404, "人群圈选服务不可用")
    return svc.estimate_scale(cohort_id)


@router.get("/data_service/{service_id}/invoke")
def data_service_invoke(service_id: int) -> dict[str, Any]:
    """数据服务接口调用。"""
    from app.services.data_service import DataServiceService
    svc = SERVICES.get("data_service")
    if not svc or not isinstance(svc, DataServiceService):
        raise HTTPException(404, "数据服务不可用")
    return svc.invoke_service(service_id)


@router.get("/anomaly_detect/{rule_id}/detect")
def anomaly_detect_run(rule_id: int) -> dict[str, Any]:
    """异常检测执行。"""
    from app.services.anomaly_detect import AnomalyDetectService
    svc = SERVICES.get("anomaly_detect")
    if not svc or not isinstance(svc, AnomalyDetectService):
        raise HTTPException(404, "异常检测服务不可用")
    return svc.detect_anomalies(rule_id)


@router.get("/analysis_chart/{chart_id}/render")
def chart_render(chart_id: int) -> dict[str, Any]:
    """图表数据渲染。"""
    from app.services.analysis_chart import AnalysisChartService
    svc = SERVICES.get("analysis_chart")
    if not svc or not isinstance(svc, AnalysisChartService):
        raise HTTPException(404, "分析图表服务不可用")
    return svc.render_chart_data(chart_id)


@router.get("/aggregate_job/{job_id}/execute")
def aggregate_job_execute(job_id: int) -> dict[str, Any]:
    """预聚合任务执行。"""
    from app.services.aggregate_job import AggregateJobService
    svc = SERVICES.get("aggregate_job")
    if not svc or not isinstance(svc, AggregateJobService):
        raise HTTPException(404, "预聚合任务服务不可用")
    return svc.execute_aggregate(job_id)


@router.get("/drill_down/{path_id}/execute")
def drill_down_execute(path_id: int) -> dict[str, Any]:
    """下钻分析执行。"""
    from app.services.drill_down import DrillDownService
    svc = SERVICES.get("drill_down")
    if not svc or not isinstance(svc, DrillDownService):
        raise HTTPException(404, "下钻分析服务不可用")
    return svc.execute_drill_down(path_id)


@router.get("/data_export/{task_id}/execute")
def data_export_execute(task_id: int) -> dict[str, Any]:
    """数据导出执行。"""
    from app.services.data_export import DataExportService
    svc = SERVICES.get("data_export")
    if not svc or not isinstance(svc, DataExportService):
        raise HTTPException(404, "数据导出服务不可用")
    return svc.execute_export(task_id)


@router.get("/data_freshness/{check_id}/check")
def data_freshness_check(check_id: int) -> dict[str, Any]:
    """数据时效检查执行。"""
    from app.services.data_freshness import DataFreshnessService
    svc = SERVICES.get("data_freshness")
    if not svc or not isinstance(svc, DataFreshnessService):
        raise HTTPException(404, "数据时效服务不可用")
    return svc.run_freshness_check(check_id)


@router.get("/query_cache/{strategy_id}/check-status")
def query_cache_check(strategy_id: int) -> dict[str, Any]:
    """查询缓存状态检查。"""
    from app.services.query_cache import QueryCacheService
    svc = SERVICES.get("query_cache")
    if not svc or not isinstance(svc, QueryCacheService):
        raise HTTPException(404, "查询缓存服务不可用")
    return svc.check_cache_status(strategy_id)


@router.get("/segment_compare/{plan_id}/execute")
def segment_compare_execute(plan_id: int) -> dict[str, Any]:
    """分群对比执行。"""
    from app.services.segment_compare import SegmentCompareService
    svc = SERVICES.get("segment_compare")
    if not svc or not isinstance(svc, SegmentCompareService):
        raise HTTPException(404, "分群对比服务不可用")
    return svc.execute_compare(plan_id)


@router.get("/metric_calibrate/{record_id}/compute")
def metric_calibrate_compute(record_id: int) -> dict[str, Any]:
    """指标校准偏差计算。"""
    from app.services.metric_calibrate import MetricCalibrateService
    svc = SERVICES.get("metric_calibrate")
    if not svc or not isinstance(svc, MetricCalibrateService):
        raise HTTPException(404, "指标校准服务不可用")
    return svc.compute_calibration(record_id)


@router.post("/query_log/log")
def query_log_record() -> dict[str, Any]:
    """查询操作记录。"""
    from app.services.query_log import QueryLogService
    svc = SERVICES.get("query_log")
    if not svc or not isinstance(svc, QueryLogService):
        raise HTTPException(404, "查询日志服务不可用")
    return svc.log_query()


@router.get("/data_sample/{config_id}/execute")
def data_sample_execute(config_id: int) -> dict[str, Any]:
    """数据采样执行。"""
    from app.services.data_sample import DataSampleService
    svc = SERVICES.get("data_sample")
    if not svc or not isinstance(svc, DataSampleService):
        raise HTTPException(404, "数据采样服务不可用")
    return svc.execute_sampling(config_id)


@router.get("/report_schedule/{task_id}/generate")
def report_schedule_generate(task_id: int) -> dict[str, Any]:
    """报告生成。"""
    from app.services.report_schedule import ReportScheduleService
    svc = SERVICES.get("report_schedule")
    if not svc or not isinstance(svc, ReportScheduleService):
        raise HTTPException(404, "报告调度服务不可用")
    return svc.generate_report(task_id)