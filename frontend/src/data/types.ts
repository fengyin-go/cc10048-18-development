/** 纯前端数据层的公共类型：与全栈版后端返回的结构保持一致，换回后端时页面不用改。 */

export type EntryRow = {
  id: number
  status: string
  pending: boolean
  abnormal: boolean
  [field: string]: string | number | boolean
}

export type ModuleMeta = {
  key: string
  name: string
  entity: string
  desc: string
  fields: string[]
  statuses: string[]
  actions: string[]
  actionTargets: Record<string, string>
  metrics: string[]
}

export type PageResult = {
  items: EntryRow[]
  total: number
  page: number
  size: number
}

export type ActionResult = {
  ok: boolean
  message: string
}

export type OverviewResult = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

/** 实验评估域：已登记曝光、转化事件、导入文件与评估报告版本。 */
export type ExposureRow = {
  id: number
  experiment_id: number
  exposure_no: string
  subject_id: string
  group: string
  exposed_at: string
}

export type ConversionEvent = {
  id: number
  file_id: number
  filename: string
  line_no: number
  receipt_id: string
  subject_id: string
  converted_at: string
  channel: string
  group: string
  exposure_id: number | null
  counted: boolean
  status: string
  reason: string
}

export type ConversionFile = {
  id: number
  experiment_id: number
  filename: string
  imported_at: string
  total: number
  matched: number
  duplicate: number
  unmatched: number
}

export type ImportResult = {
  file: ConversionFile
  events: ConversionEvent[]
  message: string
}

export type EvalGroupStat = {
  group: string
  exposures: number
  conversions: number
  conversion_rate: number
}

export type EvalReportRecord = {
  receipt_id: string
  subject_id: string
  filename: string
  reason: string
}

export type EvalReport = {
  id: number
  experiment_id: number
  experiment_name: string
  version: number
  is_latest?: boolean
  period: { start: string; end: string }
  issued_at: string
  grouping_basis: string
  groups: EvalGroupStat[]
  totals: { exposures: number; conversions: number }
  source_files: { id: number; filename: string; imported_at: string; total: number; matched: number }[]
  exposure_range: { start: string; end: string } | null
  unmatched_records: EvalReportRecord[]
  duplicate_records: EvalReportRecord[]
}
