<template>
  <div class="house-monitor">
    <!-- 左侧监控区域 -->
    <div class="monitor-panel">
      <!-- 监控头部 -->
      <header class="monitor-header">
        <div class="header-left">
          <h1 class="monitor-title">实时分析监控</h1>
          <span class="monitor-status">● 录制中 · 4K</span>
          <span class="monitor-location">天健天骄 · 西侧</span>
        </div>
        <div class="header-right">
          <select v-model="selectedCamera" class="camera-select">
            <option value="cam1">切换摄像头 ∨</option>
            <option value="cam2">塔吊摄像头 01</option>
            <option value="cam3">地面摄像头 02</option>
          </select>
        </div>
      </header>

      <!-- 监控画面 -->
      <div class="monitor-view">
        <video
          ref="videoRef"
          class="video-player"
          autoplay
          muted
          loop
          playbackRate="0.5"
          playsinline
          controls
          @loadedmetadata="updateVideoLayout"
        >
          <source src="../assets/tianjiantianjiao.mp4" type="video/mp4" />
          您的浏览器不支持视频播放。
        </video>
        <div class="video-overlay">
          <div 
            class="mark-layer"
            :style="{
              width: videoLayout.width,
              height: videoLayout.height,
              top: videoLayout.top,
              left: videoLayout.left
            }"
          >
            <div
              v-for="(mark, index) in marks"
              :key="index"
              class="mark-box"
              :style="{
                '--x': mark.x + '%',
                '--y': mark.y + '%',
                '--w': mark.w + '%',
                '--h': mark.h + '%',
                '--c': mark.c
              }"
            >
              <div class="mark-title">{{ mark.title }}</div>
            </div>
          </div>
          <div class="live-indicator">LIVE</div>
        </div>
      </div>

      <!-- 历史抽帧 -->
      <div class="history-strip">
        <div class="history-header">
          <div class="history-title-area">
            <span>历史抽帧画面</span>
          </div>
          <div>
            <button class="add-record-btn" @click="captureFrameForBase">
            ＋ 添加基准图
          </button>
          <button class="add-record-btn" @click="captureFrame">
            ＋ 添加记录
          </button>
          </div>
        </div>
        <div class="history-frames">
          <div
            v-for="(frame, index) in historyFrames"
            :key="index"
            class="frame-item"
            :class="{ active: currentFrameIndex === index }"
            @click="currentFrameIndex = index"
          >
            <div class="frame-img-wrapper">
              <img :src="frame.url" :alt="frame.time" />
              <!-- 上传状态指示器 -->
              <div
                v-if="frame.status"
                class="status-badge"
                :class="frame.status"
              >
                <span
                  v-if="frame.status === 'uploading'"
                  class="status-icon loading"
                  >↻</span
                >
                <span
                  v-else-if="frame.status === 'success'"
                  class="status-icon success"
                  >✓</span
                >
                <span
                  v-else-if="frame.status === 'error'"
                  class="status-icon error"
                  >!</span
                >
              </div>

              <!-- 悬浮操作层 -->
              <div class="frame-hover-overlay">
                <button
                  class="hover-btn left"
                  @click.stop="setBaseline(frame)"
                  title="设为基准"
                >
                  <span class="btn-icon">⚓</span>
                </button>
                <button
                  class="hover-btn right"
                  @click.stop="setCurrentAnalysis(frame)"
                  title="AI 分析"
                >
                  <span class="btn-icon">🧠</span>
                </button>
              </div>
            </div>
            <span class="frame-time">{{ frame.time }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧 AI 分析侧边栏 -->
    <div class="ai-sidebar">
      <div class="sidebar-header">
        <h2><span class="ai-icon">⟡</span> AI 智能分析面板</h2>
      </div>

      <div class="sidebar-content">
        <!-- 画面对比 -->
        <section class="analysis-section">
          <h3 class="section-title">画面对比</h3>
          <div class="comparison-view">
            <div class="comp-img">
              <div v-if="baselineFrame" class="img-content">
                <img :src="baselineFrame.url" :alt="baselineFrame.time" />
              </div>
              <div v-else class="img-placeholder baseline">基准图</div>
              <span class="img-label">基准图</span>
            </div>
            <div class="comp-img">
              <div v-if="currentAnalysisFrame" class="img-content">
                <img
                  :src="currentAnalysisFrame.url"
                  :alt="currentAnalysisFrame.time"
                />
              </div>
              <div v-else class="img-placeholder current">实时</div>
              <span class="img-label">目标图</span>
            </div>
          </div>
        </section>

        <!-- 建筑说明 -->
        <section class="analysis-section">
          <h3 class="section-title">建筑说明</h3>
          <textarea
            v-model="buildingDescription"
            class="description-input"
            placeholder="输入建筑背景和介绍帮助 AI 理解..."
            rows="2"
          ></textarea>
        </section>

        <!-- 立即分析按钮 -->
        <div class="action-area">
          <button
            class="analyze-btn"
            :disabled="isAnalyzing"
            @click="startAnalysis"
          >
            <span v-if="isAnalyzing">分析中...</span>
            <span v-else>✧ 立即分析</span>
          </button>
        </div>

        <!-- 分析结果 -->
        <section
          class="analysis-result-section"
          v-if="analysisResult || isAnalyzing"
        >
          <!-- Markdown 流式输出 -->
          <div class="markdown-output">
            <div v-if="!analysisResult && isAnalyzing" class="typing-indicator">
              AI 正在思考...
            </div>
            <div v-else class="markdown-content" v-html="formattedResult"></div>
          </div>
        </section>
      </div>

      <div class="sidebar-footer">
        <button class="report-btn">📄 生成进度报告</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import MarkdownIt from "markdown-it";

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
});

// 状态定义
const selectedCamera = ref("cam1");
const buildingDescription = ref(`【项目概况】
项目名称：深圳天健天骄北庐
监控视角：西侧视角（由西向东拍摄）
监控画面描述：以摄像头画面左侧2/3为基准，展示项目建筑的整体布局。监控画面右侧1/3内容不是需要监控的项目建筑！！！！
建筑布局：以蓝色的附着式升降脚手架为准，建筑从监控画面左侧到监控画面2/3处，分别是D座、B座、A座、E座）
1. D座：45层（最左侧，遮挡后方C座）
2. B座：46层，总高148米
3. A座：46层，总高148米（层高3.15米）（A座被E座遮挡一半）
4. E座：44层，总高141.7米
5. C座：44层，总高141.7米（位于D座后方被遮挡）

【注意事项】
画面最右侧1/3的画面出现的其他建筑不属于本项目分析范围，请忽略。`);
const isAnalyzing = ref(false);
const analysisResult = ref("");
const currentFrameIndex = ref(0);
const videoRef = ref<HTMLVideoElement | null>(null);

// 视频布局状态
const videoLayout = ref({
  width: '100%',
  height: '100%',
  top: '0px',
  left: '0px'
});

// 更新视频布局信息
const updateVideoLayout = () => {
  const video = videoRef.value;
  if (!video) return;

  const videoRatio = video.videoWidth / video.videoHeight;
  const container = video.parentElement;
  if (!container) return;

  const containerRect = container.getBoundingClientRect();
  const containerRatio = containerRect.width / containerRect.height;

  let renderWidth, renderHeight, top, left;

  if (containerRatio > videoRatio) {
    // 容器更宽，视频高度占满，宽度自适应
    renderHeight = containerRect.height;
    renderWidth = renderHeight * videoRatio;
    top = 0;
    left = (containerRect.width - renderWidth) / 2;
  } else {
    // 容器更高，视频宽度占满，高度自适应
    renderWidth = containerRect.width;
    renderHeight = renderWidth / videoRatio;
    left = 0;
    top = (containerRect.height - renderHeight) / 2;
  }

  videoLayout.value = {
    width: `${renderWidth}px`,
    height: `${renderHeight}px`,
    top: `${top}px`,
    left: `${left}px`
  };
};

onMounted(() => {
  window.addEventListener('resize', updateVideoLayout);
  // 监听视频元数据加载完成，以获取正确尺寸
  if (videoRef.value) {
    videoRef.value.addEventListener('loadedmetadata', updateVideoLayout);
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', updateVideoLayout);
  if (videoRef.value) {
    videoRef.value.removeEventListener('loadedmetadata', updateVideoLayout);
  }
});

// 标记框数据
const marks = ref([
  { x: 0, y: 27, w: 20, h: 64, c: 'red', title: '天健天骄北庐D座' },
  { x: 22, y: 40, w: 16, h: 51, c: 'red', title: '天健天骄北庐B座' },
  { x: 42, y: 49, w: 15, h: 41, c: 'red', title: '天健天骄北庐A座' },
  { x: 48, y: 62, w: 24, h: 30, c: 'red', title: '天健天骄北庐E座' }
]);

interface HistoryFrame {
  time: string;
  url: string;
  serverPath?: string;
  filename?: string;
  status?: "uploading" | "success" | "error";
}

// 模拟历史抽帧数据
const historyFrames = ref<HistoryFrame[]>([]);

// 基准图和当前分析图状态
const baselineFrame = ref<HistoryFrame | null>(null);
const currentAnalysisFrame = ref<HistoryFrame | null>(null);

// 设为基准图
const setBaseline = (frame: HistoryFrame) => {
  baselineFrame.value = frame;
};

// 设为 AI 分析画面
const setCurrentAnalysis = (frame: HistoryFrame) => {
  currentAnalysisFrame.value = frame;
};

// 处理图片捕获和上传的通用逻辑
const processCapturedImage = (canvas: HTMLCanvasElement, isBaseline: boolean = false) => {
  // 生成 Data URL
  const imageUrl = canvas.toDataURL("image/jpeg");

  // 获取当前时间
  const now = new Date();
  const timeString = `今日 ${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;

  const filename = `capture_${Date.now()}.jpg`;

  // 创建新记录对象
  const newFrame: HistoryFrame = {
    time: timeString,
    url: imageUrl,
    status: "uploading",
    filename: filename,
  };

  // 添加到历史记录头部
  historyFrames.value.unshift(newFrame);
  const activeFrame = historyFrames.value[0];
  if (!activeFrame) return;

  // 选中最新添加的帧
  currentFrameIndex.value = 0;
  
  // 如果是基准图，自动设为基准
  if (isBaseline) {
    setBaseline(activeFrame);
  }

  // 上传图片到服务端
  canvas.toBlob(async (blob) => {
    if (!blob) return;

    const formData = new FormData();
    formData.append("file", blob, filename);

    try {
      // 假设后端运行在本地 8000 端口
      const response = await fetch("http://localhost:8000/files/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        // 更新服务端保存路径
        activeFrame.serverPath = data.saved_path;
        activeFrame.status = "success";
        console.log("Image uploaded successfully:", data.saved_path);
      } else {
        activeFrame.status = "error";
        console.error("Failed to upload image:", response.statusText);
      }
    } catch (error) {
      activeFrame.status = "error";
      console.error("Error uploading image:", error);
    }
  }, "image/jpeg");
};

// 基准图（带标记）
const captureFrameForBase = () => {
  if (!videoRef.value) return;

  const video = videoRef.value;
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // 1. 绘制视频帧
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  // 2. 绘制标记层
  marks.value.forEach(mark => {
    const x = (mark.x / 100) * canvas.width;
    const y = (mark.y / 100) * canvas.height;
    const w = (mark.w / 100) * canvas.width;
    const h = (mark.h / 100) * canvas.height;

    // 绘制边框
    ctx.strokeStyle = mark.c;
    ctx.lineWidth = Math.max(2, canvas.width * 0.003); // 自适应线宽
    ctx.strokeRect(x, y, w, h);

    // 绘制标题
    const fontSize = Math.max(12, canvas.width * 0.015);
    ctx.font = `bold ${fontSize}px Arial, sans-serif`;
    const textPadding = fontSize * 0.4;
    
    // 计算文字尺寸
    const textMetrics = ctx.measureText(mark.title);
    const textWidth = textMetrics.width + textPadding * 2;
    const textHeight = fontSize + textPadding;
    
    // 标题背景位置（框的上方）
    const titleX = x;
    const titleY = y - textHeight;
    
    // 绘制标题背景（半透明）
    ctx.fillStyle = mark.c; 
    ctx.globalAlpha = 0.8;
    // 简单的圆角矩形模拟
    ctx.fillRect(titleX, titleY, textWidth, textHeight);
    ctx.globalAlpha = 1.0;
    
    // 绘制文字
    ctx.fillStyle = '#fff';
    ctx.textBaseline = 'top';
    ctx.fillText(mark.title, titleX + textPadding, titleY + textPadding/2);
  });

  // 处理图片
  processCapturedImage(canvas, true);
};

// 视频截图功能（纯视频）
const captureFrame = () => {
  if (!videoRef.value) return;

  const video = videoRef.value;
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // 绘制当前帧
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  // 处理图片
  processCapturedImage(canvas, false);
};

// 使用 MarkdownIt 解析
const formattedResult = computed(() => {
  return md.render(analysisResult.value);
});

// 流式分析
const startAnalysis = async () => {
  if (isAnalyzing.value) return;

  if (!baselineFrame.value || !currentAnalysisFrame.value) {
    alert("请先选择基准图和目标图");
    return;
  }

  isAnalyzing.value = true;
  analysisResult.value = "";

  try {
    const response = await fetch(
      "http://localhost:8000/agent/building/stream",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          basic_image_name: baselineFrame.value.filename,
          comparison_image_name: currentAnalysisFrame.value.filename,
          description: buildingDescription.value,
        }),
      },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      analysisResult.value = `Error: ${response.status} ${response.statusText}\n${errorData.detail || ""}`;
      isAnalyzing.value = false;
      return;
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let hasReasoning = false;

    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6);
            if (dataStr.trim() === "[DONE]") continue;

            try {
              const data = JSON.parse(dataStr);

              if (data.reasoning) {
                if (!hasReasoning) {
                  analysisResult.value += "**Thinking Process:**\n";
                  hasReasoning = true;
                }
                analysisResult.value += data.reasoning;
              }

              if (data.content) {
                if (hasReasoning) {
                  analysisResult.value += "\n\n**Final Answer:**\n";
                  hasReasoning = false;
                }
                analysisResult.value += data.content;
              }
            } catch (e) {
              console.error("Error parsing SSE data:", e);
            }
          }
        }
      }
    }
  } catch (error) {
    analysisResult.value = `Request failed: ${error}`;
  } finally {
    isAnalyzing.value = false;
  }
};
</script>

<style scoped>
/* 全局容器 */
.house-monitor {
  display: flex;
  width: 100vw;
  height: 100vh;
  background-color: #0b1121; /* 深色背景 */
  color: #e2e8f0;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial,
    sans-serif;
  overflow: hidden;
}

/* 左侧面板 */
.monitor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #1e293b;
  position: relative;
  min-width: 0; /* 修复 flex 子项溢出问题 */
}

/* 头部样式 */
.monitor-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background-color: #0f172a;
  border-bottom: 1px solid #1e293b;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.monitor-title {
  font-size: 18px;
  font-weight: 600;
  color: #f8fafc;
  margin: 0;
}

.monitor-status {
  font-size: 12px;
  background-color: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.monitor-location {
  font-size: 13px;
  color: #94a3b8;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.camera-select {
  background-color: #1e293b;
  color: #e2e8f0;
  border: 1px solid #334155;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}

/* 监控画面 */
.monitor-view {
  flex: 1;
  background-color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.mark-layer {
  position: absolute;
  pointer-events: none;
  /* 移除 inset: 0，由 JS 控制尺寸 */
}

.mark-box {
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: var(--w);
  height: var(--h);
  border: 2px solid color-mix(in srgb, var(--c) 92%, white 8%);
  border-radius: 16px 6px 22px 8px / 8px 22px 10px 18px;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--c) 12%, transparent) 0%,
    rgba(0, 0, 0, 0.06) 55%,
    rgba(0, 0, 0, 0.16) 100%
  );
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.06) inset,
    0 10px 30px rgba(0, 0, 0, 0.35);
}

.mark-box::before {
  content: "";
  position: absolute;
  inset: 6px;
  border: 1px dashed color-mix(in srgb, var(--c) 65%, transparent);
  border-radius: 14px 10px 18px 12px;
  transform: rotate(-0.2deg);
  opacity: 0.9;
}

.mark-box::after {
  content: "";
  position: absolute;
  left: -2px;
  top: -2px;
  width: 22px;
  height: 22px;
  border-left: 4px solid var(--c);
  border-top: 4px solid var(--c);
  border-top-left-radius: 10px;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.35));
}

.mark-title {
  position: absolute;
  top: -28px;
  left: -2px;
  max-width: calc(100% + 4px);
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.2px;
  color: #0b1121;
  background: color-mix(in srgb, var(--c) 90%, white 10%);
  border-radius: 10px 8px 10px 6px;
  transform: rotate(-0.4deg);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.35);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.overlay-box {
  position: absolute;
  border: 2px solid;
  background-color: rgba(0, 0, 0, 0.3);
  pointer-events: none;
}

.box-1 {
  top: 20%;
  left: 30%;
  width: 200px;
  height: 300px;
  border-color: #3b82f6; /* Blue */
}

.box-2 {
  top: 40%;
  left: 55%;
  width: 150px;
  height: 200px;
  border-color: #10b981; /* Green */
}

.box-label {
  position: absolute;
  top: -24px;
  left: -2px;
  background-color: inherit;
  color: #fff;
  font-size: 12px;
  padding: 2px 6px;
  white-space: nowrap;
}

.box-1 .box-label {
  background-color: #3b82f6;
}
.box-2 .box-label {
  background-color: #10b981;
}

.live-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  background-color: #ef4444;
  color: white;
  font-size: 12px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 2px;
}

/* 历史抽帧 */
.history-strip {
  height: 160px;
  background-color: #0f172a;
  border-top: 1px solid #1e293b;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 13px;
  color: #94a3b8;
}

.history-title-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.add-record-btn {
  background-color: #1e293b;
  border: 1px solid #334155;
  color: #e2e8f0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: 8px;
}

.add-record-btn:hover {
  background-color: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

.view-all {
  color: #3b82f6;
  text-decoration: none;
}

.history-frames {
  box-sizing: border-box;
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.frame-item {
  flex: 0 0 160px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.frame-item:hover {
  opacity: 0.8;
}

.frame-item.active .frame-img-wrapper {
  border-color: #3b82f6;
}

.frame-img-wrapper {
  position: relative;
  width: 100%;
  height: 90px;
  border: 2px solid transparent;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 6px;
}

.status-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  background-color: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(2px);
}

.status-icon {
  display: inline-block;
  line-height: 1;
}

.status-badge.uploading {
  color: #fbbf24; /* Amber 400 */
}

.status-badge.success {
  color: #4ade80; /* Green 400 */
}

.status-badge.error {
  color: #f87171; /* Red 400 */
}

.status-icon.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.frame-img-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.frame-time {
  font-size: 12px;
  color: #64748b;
}

/* 右侧 AI 侧边栏 */
.ai-sidebar {
  width: 360px;
  background-color: #111827;
  border-left: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px 20px;
  border-bottom: 1px solid #1e293b;
}

.sidebar-header h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f8fafc;
}

.ai-icon {
  color: #3b82f6;
}

.sidebar-content {
  flex: 1;
  padding: 12px 20px 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.analysis-section {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.section-title {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 8px;
  font-weight: 500;
}

/* 画面对比 */
.comparison-view {
  display: flex;
  gap: 12px;
}

.frame-hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.frame-img-wrapper:hover .frame-hover-overlay {
  opacity: 1;
}

.hover-btn {
  background-color: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.hover-btn:hover {
  background-color: rgba(255, 255, 255, 0.9);
  color: #0f172a;
  transform: scale(1.1);
}

.btn-icon {
  font-size: 14px;
  line-height: 1;
}

.img-content {
  width: 100%;
  aspect-ratio: 16/9;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.img-content img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.comp-img {
  position: relative;
  flex: 1;
  /* 移除背景色和边框圆角，由内部元素控制 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  /* 移除 aspect-ratio，让内容决定高度，或者保留并在内部处理 */
  min-width: 0; /* 防止 flex 子项溢出 */
  box-sizing: border-box; /* 确保边框计算在宽度内 */
}

.img-placeholder {
  width: 100%;
  aspect-ratio: 16/9;
  background-color: #1e293b;
  border-radius: 4px; /* 统一圆角 */
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #64748b;
  border: 1px dashed #475569; /* 改为虚线边框以示区别，并加深颜色 */
  box-sizing: border-box; /* 确保边框计算在宽度内 */
}

.img-placeholder.current {
  border-color: #3b82f6;
  position: relative;
}

.img-placeholder.current::after {
  content: "实时";
  position: absolute;
  top: 4px;
  right: 4px;
  background: #3b82f6;
  color: white;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 2px;
}

.img-label {
  font-size: 12px;
  color: #64748b;
}

/* 表单元素 */
.styled-select,
.description-input {
  width: 100%;
  box-sizing: border-box;
  background-color: #1e293b;
  border: 1px solid #334155;
  color: #e2e8f0;
  border-radius: 6px;
  padding: 10px;
  font-size: 13px;
  outline: none;
}

.styled-select:focus,
.description-input:focus {
  border-color: #3b82f6;
}

.description-input {
  resize: vertical;
  min-height: 60px;
}

.action-area {
  flex-shrink: 0;
  margin-bottom: 12px;
}

/* 按钮 */
.analyze-btn {
  width: 100%;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  padding: 12px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: opacity 0.2s;
}

.analyze-btn:hover {
  opacity: 0.9;
}

.analyze-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* 分析结果 */
.analysis-result-section {
  background-color: #1e293b;
  border-radius: 8px;
  padding: 12px;
  margin-top: 0;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.progress-card {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.progress-circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 4px solid #3b82f6;
  border-right-color: #1e293b; /* Mock partial circle */
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-value {
  font-size: 12px;
  font-weight: bold;
}

.progress-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
}

.progress-info p {
  margin: 0;
  font-size: 12px;
  color: #10b981;
}

.markdown-output {
  font-size: 13px;
  line-height: 1.6;
  color: #cbd5e1;
  border-top: 1px solid #334155;
  padding-top: 12px;
  flex: 1;
  overflow-y: auto;
}

.typing-indicator {
  color: #94a3b8;
  font-style: italic;
}

/* 底部按钮 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #1e293b;
}

.report-btn {
  width: 100%;
  background-color: transparent;
  border: 1px solid #334155;
  color: #94a3b8;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.report-btn:hover {
  border-color: #475569;
  color: #e2e8f0;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #0f172a;
}

::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #475569;
}
</style>
