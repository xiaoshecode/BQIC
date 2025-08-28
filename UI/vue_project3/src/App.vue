<template>
  <div class="wrapper">
    <!-- 连接 / 发送 / 滑块 -->
    <button @click="toggleConnect" :disabled="connecting">
      {{ connected ? '断开' : '连接' }}
      <span v-if="connecting">…</span>
    </button>

    <button
      @click="sendStart"
      :disabled="!connected || sending"
      style="margin-left: 1rem"
    >
      {{ sending ? '发送中…' : '发送' }}
    </button>

    <div class="slider-box">
      显示点数：
      <input
        type="range"
        min="20"
        :max="MAX_POINTS"
        v-model.number="viewPoints"
        :disabled="sending"
        @input="sliderChanged"
      />
      {{ viewPoints }}
      <button
        style="margin-left:0.5rem"
        @click="resetZoom"
        :disabled="!connected"
      >
        重置视图
      </button>
    </div>

    <!-- 拟合控制 -->
    <div class="fit-box">
      <button @click="doFit" :disabled="!hasData()">开始拟合</button>
      <select v-model="fitModel" :disabled="!hasData()">
        <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
      </select>
    </div>

    <!-- 主图 -->
    <div class="chart-box">
      <canvas ref="chartRef" width="800" height="400"></canvas>
    </div>

    <p v-if="!connected && !connecting" class="tip">
      点击「连接」后再点「发送」开始接收数据
    </p>

    <!-- 总览图 -->
    <h3 style="margin-top:1.5rem">全部数据总览</h3>
    <div class="chart-box">
      <canvas ref="overviewRef" width="800" height="200"></canvas>
    </div>

    <!-- 拟合结果弹窗 -->
    <dialog ref="fitDlg" class="fit-dialog">
      <img v-if="fitImg" :src="fitImg" style="max-width:100%;" />
      <pre>{{ JSON.stringify(fitParams, null, 2) }}</pre>
      <button @click="fitDlg.close()">关闭</button>
    </dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import {
  Chart as ChartJS,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  CategoryScale,
  Filler
} from 'chart.js'
import ChartDataLabels from 'chartjs-plugin-datalabels'
import zoomPlugin from 'chartjs-plugin-zoom'

ChartJS.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
  Filler,
  zoomPlugin,
  ChartDataLabels
)

/* ---------- 模板引用 ---------- */
const chartRef    = ref(null)
const overviewRef = ref(null)

/* ---------- 图表实例 ---------- */
let chart         = null
let overviewChart = null
let ws            = null

/* ---------- 状态 ---------- */
const connected  = ref(false)
const connecting = ref(false)
const sending    = ref(false)
const MAX_POINTS = 2000
const viewPoints = ref(100)
let localCounter = 0

/* ---------- 拟合相关 ---------- */
const models     = ref([])
const fitModel   = ref('rabi')
const fitImg     = ref('')
const fitParams  = ref({})
const fitDlg     = ref(null)

/* 关键：全局暴露 chart，供控制台和按钮可用性检测 */
function hasData() {
  return window.chart && window.chart.data.labels.length > 2
}

onMounted(async () => {
  /* 拉取模型列表 */
  models.value = await fetch('http://localhost:8766/models').then(r => r.json())
  initMainChart()
  initOverviewChart()
})

/* ---------- 主图初始化（带 zoom/pan） ---------- */
function initMainChart() {
  if (chart) chart.destroy()
  chart = new ChartJS(chartRef.value, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'value',
        data: [],
        borderColor: '#42b983',
        backgroundColor: 'rgba(66, 185, 131, 0.2)',
        tension: 0.2,
        fill: true,
        pointRadius: 2
      }]
    },
    options: {
      responsive: false,
      animation: { duration: 0 },
      scales: {
        x: {
          type: 'linear',
          title: { display: true, text: '计数' }
        },
        y: { min: 0, max: 100, title: { display: true, text: 'value' } }
      },
      plugins: {
        datalabels: {
          display: true,
          color: '#000',
          align: 'top',
          anchor: 'end',
          offset: 2,
          formatter: v => v.toFixed(1),
          font: { size: 9 }
        },
        zoom: {
          pan: { enabled: true, mode: 'x' },
          zoom: {
            wheel: { enabled: true },
            pinch: { enabled: true },
            mode: 'x',
            drag: { enabled: false }
          }
        }
      }
    }
  })
  window.chart = chart   // <-- 关键：暴露全局
}

/* ---------- 总览图 ---------- */
function initOverviewChart() {
  if (overviewChart) overviewChart.destroy()
  overviewChart = new ChartJS(overviewRef.value, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: '全部数据',
        data: [],
        borderColor: '#5470c6',
        backgroundColor: 'rgba(84,112,198,0.15)',
        tension: 0.2,
        fill: true,
        pointRadius: 0
      }]
    },
    options: {
      responsive: false,
      animation: { duration: 0 },
      scales: {
        x: {
          type: 'linear',
          display: true,
          title: { display: true, text: '计数' },
          ticks: { maxTicksLimit: 8 }
        },
        y: { min: 0, max: 100, title: { display: true, text: 'value' } }
      },
      plugins: {
        legend: { display: false },
        datalabels: { display: false }
      }
    }
  })
}

/* ---------- 滑块 / 缩放 ---------- */
function sliderChanged() {
  if (!window.chart) return
  const total = window.chart.data.labels.length
  if (total) {
    const start = Math.max(0, total - viewPoints.value)
    const end   = total - 1
    window.chart.options.scales.x.min = start
    window.chart.options.scales.x.max = end
    window.chart.update('none')
  }
}

function resetZoom() {
  if (!window.chart) return
  window.chart.resetZoom()
  sliderChanged()
}

/* ---------- WebSocket ---------- */
function openSocket() {
  connecting.value = true
  initMainChart()
  initOverviewChart()
  localCounter = 0
  if (window.chart) {
    window.chart.data.labels = []
    window.chart.data.datasets[0].data = []
  }
  if (overviewChart) {
    overviewChart.data.labels = []
    overviewChart.data.datasets[0].data = []
  }

  ws = new WebSocket('ws://localhost:8765')
  ws.onopen = () => { connected.value = true; connecting.value = false }
  ws.onclose = ws.onerror = () => { connected.value = false; sending.value = false; ws = null }
  ws.onmessage = ({ data }) => {
    const { value } = JSON.parse(data)
    if (window.chart) {
      window.chart.data.labels.push(localCounter)
      window.chart.data.datasets[0].data.push(value)
      sliderChanged()
    }
    if (overviewChart) {
      overviewChart.data.labels.push(localCounter)
      overviewChart.data.datasets[0].data.push(value)
      overviewChart.update('none')
    }
    localCounter++
    if (localCounter >= MAX_POINTS) { sending.value = false; ws.close() }
  }
}

function closeSocket() { if (ws) ws.close() }
function toggleConnect() { connected.value ? closeSocket() : openSocket() }
function sendStart() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  sending.value = true
  ws.send('start')
}

/* ---------- 拟合 ---------- */
async function doFit() {
  const x = window.chart.data.labels
  const y = window.chart.data.datasets[0].data
  let payload = { x, y, model: fitModel.value }
  if (fitModel.value === 'gaussian') {
    const p0str = prompt('p0 用逗号分隔', '1,0,1,0')
    if (!p0str) return
    payload.p0 = p0str.split(',').map(Number)
  }
  const res = await fetch('http://localhost:8766/fit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(r => r.json())
  if (res.error) return alert('拟合失败：' + res.error)
  fitImg.value   = res.img
  fitParams.value = res.params
  fitDlg.value.showModal()
}

/* ---------- 生命周期 ---------- */
onUnmounted(() => {
  closeSocket()
  chart?.destroy()
  overviewChart?.destroy()
})
</script>

<style scoped>
.wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
}
button {
  margin-bottom: 0.5rem;
  padding: 0.5rem 1.2rem;
  font-size: 1rem;
  cursor: pointer;
}
.slider-box {
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}
.chart-box {
  width: 800px;
  border: 1px solid #ddd;
}
.tip {
  margin-top: 0.5rem;
  color: #666;
}
.fit-box {
  margin: 0.5rem 0;
}
.fit-dialog {
  border: 1px solid #ccc;
  padding: 1rem;
  max-width: 700px;
}
</style>