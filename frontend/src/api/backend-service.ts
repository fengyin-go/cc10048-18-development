import { request } from './client'
import { moduleMeta } from '@/data/modules'
import type {
  ActionResult,
  ConversionEvent,
  ConversionFile,
  EntryRow,
  EvalReport,
  ExposureRow,
  ImportResult,
  OverviewResult,
  PageResult,
} from '@/data/types'

export { moduleMeta }

export async function listEntries(
  key: string,
  filters: Record<string, string> = {},
): Promise<PageResult> {
  const query = new URLSearchParams(filters).toString()
  const response = await request(`/api/${key}?${query}`)
  if (!response.ok) throw new Error('业务数据读取失败')
  return await response.json()
}

export async function createEntry(
  key: string,
  values: Record<string, string>,
): Promise<ActionResult> {
  const response = await request(`/api/${key}`, {
    method: 'POST',
    body: JSON.stringify({ values }),
  })
  return await response.json()
}

export async function runAction(
  key: string,
  id: number,
  action: string,
): Promise<ActionResult> {
  const response = await request(`/api/${key}/${id}/actions`, {
    method: 'POST',
    body: JSON.stringify({ action }),
  })
  return await response.json()
}

export async function downloadEntries(
  key: string,
  filters: Record<string, string> = {},
): Promise<void> {
  const query = new URLSearchParams(filters).toString()
  const response = await request(`/api/${key}/export?${query}`)
  if (!response.ok) throw new Error('业务数据导出失败')
  const url = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${key}.csv`
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

export async function loadOverview(): Promise<OverviewResult> {
  const response = await request('/api/overview')
  if (!response.ok) throw new Error('运营概览读取失败')
  return await response.json()
}

/* ---- 实验评估域：转化导入、评估与报告版本 ---- */

async function parseJsonOrThrow<T>(response: Response, fallback: string): Promise<T> {
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = data && typeof data.detail === 'string' ? data.detail : fallback
    throw new Error(detail)
  }
  return data as T
}

export async function listExposures(
  experimentId: number,
): Promise<{ items: ExposureRow[]; total: number }> {
  const response = await request(`/api/domain/experiment/${experimentId}/exposures`)
  return parseJsonOrThrow(response, '已登记曝光读取失败')
}

export async function importConversionFile(
  experimentId: number,
  filename: string,
  content: string,
): Promise<ImportResult> {
  const response = await request(`/api/domain/experiment/${experimentId}/conversions/import`, {
    method: 'POST',
    body: JSON.stringify({ filename, content }),
  })
  return parseJsonOrThrow(response, '转化文件导入失败')
}

export async function listConversionEvents(
  experimentId: number,
): Promise<{ files: ConversionFile[]; events: ConversionEvent[]; total: number }> {
  const response = await request(`/api/domain/experiment/${experimentId}/conversions`)
  return parseJsonOrThrow(response, '转化明细读取失败')
}

export async function evaluateExperiment(
  experimentId: number,
  periodStart: string,
  periodEnd: string,
): Promise<EvalReport> {
  const response = await request(`/api/domain/experiment/${experimentId}/evaluate`, {
    method: 'POST',
    body: JSON.stringify({ period_start: periodStart, period_end: periodEnd }),
  })
  return parseJsonOrThrow(response, '实验评估发起失败')
}

export async function listEvalReports(
  experimentId: number,
): Promise<{ items: EvalReport[]; total: number }> {
  const response = await request(`/api/domain/experiment/${experimentId}/reports`)
  return parseJsonOrThrow(response, '评估报告读取失败')
}

export async function getEvalReport(experimentId: number, reportId: number): Promise<EvalReport> {
  const response = await request(`/api/domain/experiment/${experimentId}/reports/${reportId}`)
  return parseJsonOrThrow(response, '评估报告读取失败')
}
