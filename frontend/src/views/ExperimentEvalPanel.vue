<template>
  <section class="eval-panel" data-testid="experiment-eval-panel">
    <h3>转化导入与实验评估</h3>
    <p class="page-desc">
      从文件导入渠道转化事件明细，按真实曝光组形成可评估转化数据；评估关联已登记曝光，
      报告标出采用的文件与曝光时间范围，已发出的版本均可回查。
    </p>

    <div class="eval-toolbar">
      <label class="filter-item">
        <span>实验方案</span>
        <select v-model.number="selectedId" data-testid="eval-experiment-select" @change="onSelectExperiment">
          <option v-for="exp in experiments" :key="String(exp.id)" :value="Number(exp.id)">
            {{ exp['方案标识'] }}（{{ exp['实验名称'] }}）
          </option>
        </select>
      </label>
      <label class="filter-item">
        <span>统计期开始</span>
        <input v-model="periodStart" type="date" data-testid="eval-period-start" />
      </label>
      <label class="filter-item">
        <span>统计期结束</span>
        <input v-model="periodEnd" type="date" data-testid="eval-period-end" />
      </label>
      <label class="btn eval-upload" data-testid="eval-upload-label">
        选择并导入转化文件
        <input
          type="file"
          accept=".csv,text/csv,text/plain"
          class="eval-file-input"
          data-testid="eval-file-input"
          @change="onFilePicked"
        />
      </label>
      <button
        class="btn primary"
        type="button"
        data-testid="eval-run"
        :disabled="!selectedId || evaluating"
        @click="runEvaluate"
      >
        {{ evaluating ? '评估中…' : '从该周期发起评估' }}
      </button>
    </div>

    <p v-if="notice" class="eval-notice" data-testid="eval-notice">{{ notice }}</p>
    <p v-if="errorMessage" class="error-text" data-testid="eval-error">{{ errorMessage }}</p>

    <div class="eval-columns">
      <div class="eval-block">
        <h4>已登记曝光（真实曝光组）</h4>
        <table class="data-table">
          <thead>
            <tr><th>曝光编号</th><th>主体标识</th><th>曝光组</th><th>曝光时间</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in exposures" :key="row.id">
              <td>{{ row.exposure_no }}</td>
              <td>{{ row.subject_id }}</td>
              <td>{{ row.group }}</td>
              <td>{{ row.exposed_at }}</td>
            </tr>
            <tr v-if="!exposures.length">
              <td colspan="4" class="empty-state">该实验暂无已登记曝光</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="eval-block">
        <h4>转化事件明细（按来源文件回查）</h4>
        <table class="data-table">
          <thead>
            <tr>
              <th>回执号</th><th>主体标识</th><th>归集组</th><th>状态</th><th>原因</th><th>来源文件</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in events" :key="row.id" :data-status="row.status">
              <td>{{ row.receipt_id || '—' }}</td>
              <td>{{ row.subject_id || '—' }}</td>
              <td>{{ row.group || '—' }}</td>
              <td>{{ row.status }}</td>
              <td>{{ row.reason || '—' }}</td>
              <td>{{ row.filename }}</td>
            </tr>
            <tr v-if="!events.length">
              <td colspan="6" class="empty-state">尚未导入转化明细文件</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="eval-block">
      <h4>评估报告（最新版为实际可领取，旧版可回查）</h4>
      <table class="data-table">
        <thead>
          <tr><th>版本</th><th>统计期</th><th>发出时间</th><th>参与曝光</th><th>参与转化</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="report in reports" :key="report.id" :data-testid="`eval-report-${report.version}`">
            <td>
              v{{ report.version }}
              <span v-if="report.is_latest" class="eval-tag">可领取</span>
              <span v-else class="eval-tag old">旧版</span>
            </td>
            <td>{{ report.period.start }} ~ {{ report.period.end }}</td>
            <td>{{ report.issued_at }}</td>
            <td>{{ report.totals.exposures }}</td>
            <td>{{ report.totals.conversions }}</td>
            <td class="row-actions">
              <button
                class="link"
                type="button"
                :data-testid="`eval-report-view-${report.version}`"
                @click="viewReport(report.id)"
              >
                查看
              </button>
            </td>
          </tr>
          <tr v-if="!reports.length">
            <td colspan="6" class="empty-state">尚未发出评估报告，可先导入转化文件并发起评估</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="activeReport" class="eval-block eval-report-detail" data-testid="eval-report-detail">
      <h4>
        报告 v{{ activeReport.version }} 快照
        <span v-if="activeReport.is_latest" class="eval-tag">可领取</span>
        <span v-else class="eval-tag old">旧版</span>
      </h4>
      <p class="page-desc">
        统计期 {{ activeReport.period.start }} ~ {{ activeReport.period.end }}；
        曝光时间范围 {{ activeReport.exposure_range ? `${activeReport.exposure_range.start} ~ ${activeReport.exposure_range.end}` : '无' }}；
        {{ activeReport.grouping_basis }}
      </p>
      <table class="data-table">
        <thead>
          <tr><th>组别</th><th>参与曝光</th><th>参与转化</th><th>转化率</th></tr>
        </thead>
        <tbody>
          <tr v-for="stat in activeReport.groups" :key="stat.group">
            <td>{{ stat.group }}</td>
            <td>{{ stat.exposures }}</td>
            <td>{{ stat.conversions }}</td>
            <td>{{ (stat.conversion_rate * 100).toFixed(2) }}%</td>
          </tr>
        </tbody>
      </table>
      <p class="eval-notice">
        采用文件：
        <span v-if="activeReport.source_files.length">
          {{ activeReport.source_files.map((f) => `${f.filename}（匹配 ${f.matched} 条）`).join('、') }}
        </span>
        <span v-else>无</span>
      </p>
      <div v-if="activeReport.unmatched_records.length" class="eval-subblock">
        <h5>未匹配曝光记录（单独原因）</h5>
        <table class="data-table">
          <thead>
            <tr><th>回执号</th><th>主体标识</th><th>来源文件</th><th>原因</th></tr>
          </thead>
          <tbody>
            <tr v-for="(rec, idx) in activeReport.unmatched_records" :key="`u-${idx}`">
              <td>{{ rec.receipt_id || '—' }}</td>
              <td>{{ rec.subject_id || '—' }}</td>
              <td>{{ rec.filename }}</td>
              <td>{{ rec.reason }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="activeReport.duplicate_records.length" class="eval-subblock">
        <h5>重复回执（不重复统计）</h5>
        <table class="data-table">
          <thead>
            <tr><th>回执号</th><th>主体标识</th><th>来源文件</th><th>原因</th></tr>
          </thead>
          <tbody>
            <tr v-for="(rec, idx) in activeReport.duplicate_records" :key="`d-${idx}`">
              <td>{{ rec.receipt_id }}</td>
              <td>{{ rec.subject_id }}</td>
              <td>{{ rec.filename }}</td>
              <td>{{ rec.reason }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import {
  evaluateExperiment,
  getEvalReport,
  importConversionFile,
  listConversionEvents,
  listEvalReports,
  listExposures,
} from '@/api/backend-service'
import type { ConversionEvent, EntryRow, EvalReport, ExposureRow } from '@/data/types'

const props = defineProps<{ experiments: EntryRow[] }>()

const selectedId = ref<number>(0)
const periodStart = ref('')
const periodEnd = ref('')
const exposures = ref<ExposureRow[]>([])
const events = ref<ConversionEvent[]>([])
const reports = ref<EvalReport[]>([])
const activeReport = ref<EvalReport | null>(null)
const notice = ref('')
const errorMessage = ref('')
const evaluating = ref(false)

function syncPeriodFromExperiment() {
  const current = props.experiments.find((row) => Number(row.id) === selectedId.value)
  periodStart.value = current ? String(current['开始日期'] ?? '') : ''
  periodEnd.value = current ? String(current['结束日期'] ?? '') : ''
}

async function refreshEvalData() {
  if (!selectedId.value) return
  const [exposurePayload, conversionPayload, reportPayload] = await Promise.all([
    listExposures(selectedId.value),
    listConversionEvents(selectedId.value),
    listEvalReports(selectedId.value),
  ])
  exposures.value = exposurePayload.items
  events.value = conversionPayload.events
  reports.value = reportPayload.items
}

async function onSelectExperiment() {
  notice.value = ''
  errorMessage.value = ''
  activeReport.value = null
  syncPeriodFromExperiment()
  try {
    await refreshEvalData()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '评估数据读取失败'
  }
}

async function onFilePick(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !selectedId.value) return
  notice.value = ''
  errorMessage.value = ''
  try {
    const content = await file.text()
    const result = await importConversionFile(selectedId.value, file.name, content)
    notice.value = result.message
    await refreshEvalData()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '转化文件导入失败'
  } finally {
    input.value = ''
  }
}

// 暴露为可测试的处理器名，模板中保持 @change 绑定
const onFilePicked = onFilePick

async function runEvaluate() {
  if (!selectedId.value) return
  evaluating.value = true
  notice.value = ''
  errorMessage.value = ''
  try {
    const report = await evaluateExperiment(selectedId.value, periodStart.value, periodEnd.value)
    notice.value = `评估报告 v${report.version} 已生成并发出`
    activeReport.value = report
    await refreshEvalData()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '实验评估发起失败'
  } finally {
    evaluating.value = false
  }
}

async function viewReport(reportId: number) {
  errorMessage.value = ''
  try {
    activeReport.value = await getEvalReport(selectedId.value, reportId)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '评估报告读取失败'
  }
}

watch(
  () => props.experiments,
  (rows) => {
    if (!selectedId.value && rows.length) {
      selectedId.value = Number(rows[0].id)
      void onSelectExperiment()
    }
  },
)

onMounted(() => {
  if (props.experiments.length && !selectedId.value) {
    selectedId.value = Number(props.experiments[0].id)
    void onSelectExperiment()
  }
})
</script>
