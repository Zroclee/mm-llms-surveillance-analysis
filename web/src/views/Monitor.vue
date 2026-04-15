<template>
  <div class="house-monitor">
    <!-- 左侧监控区域 -->
    <div class="monitor-panel">
      <!-- 监控头部 -->
      <header class="monitor-header">
        <div class="header-left">
          <h1 class="monitor-title">实时监控与分析</h1>
          <span class="monitor-status">● 播放中</span>
        </div>
        <div class="header-right">
          <!-- 预留控制按钮或其他选项 -->
        </div>
      </header>

      <!-- 监控画面 -->
      <div class="monitor-view">
        <!-- 萤石云播放器容器 -->
        <div id="ezuikit-player" class="video-player-container"></div>
        
        <div class="video-overlay">
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

        <!-- 分析说明 -->
        <section class="analysis-section">
          <h3 class="section-title">分析说明</h3>
          <textarea
            v-model="analysisDescription"
            class="description-input"
            placeholder="输入分析背景和提示词帮助大模型理解..."
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
          <!-- 结果展示 -->
          <div class="markdown-output">
            <div v-if="!analysisResult && isAnalyzing" class="typing-indicator">
              AI 正在思考...
            </div>
            <div v-else class="markdown-content" style="white-space: pre-wrap;">{{ analysisResult }}</div>
          </div>
        </section>
      </div>

      <div class="sidebar-footer">
        <button class="report-btn" @click="generateReport">📄 生成分析报告</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import EZUIKit from "ezuikit-js";
import { ref, onMounted, onUnmounted } from "vue";

// ==========================================
// 视频播放器逻辑
// ==========================================
let myPlayer: any = null;

onMounted(async () => {
  try {
    const res = await fetch("http://localhost:8000/video/");
    const data = await res.json();
    if (data.success) {
      initEzPlayer(data.accessToken, data.url);
    } else {
      console.error("获取视频配置失败:", data.message); 
    }
  } catch (error) {
    console.error("请求后端接口失败:", error);
  }
});

onUnmounted(() => {
  if (myPlayer) {
    myPlayer.destroy();
  }
  myPlayer = null;
});

const initEzPlayer = (accessToken: string, url: string) => {
  const wrapper = document.getElementById("ezuikit-player");
  if (!wrapper) return;
  
  // 可以根据容器动态计算宽高，此处为了简单直接取父容器宽高或默认值
  const rect = wrapper.parentElement?.getBoundingClientRect();
  const width = rect?.width || 800;
  const height = rect?.height || 600;

  wrapper.style.width = `100%`;
  wrapper.style.height = `100%`;

  if (!accessToken || !url) return;

  myPlayer = new EZUIKit.EZUIKitPlayer({
    id: "ezuikit-player",
    accessToken,
    url,
    width,
    height,
    handleSuccess: () => {
      console.log("播放成功");
    },
    handleError: (err: any) => {
      console.error("播放失败:", err);
    },
  });
  myPlayer.play();
};

// ==========================================
// 抽帧与历史记录逻辑
// ==========================================
interface HistoryFrame {
  time: string;
  url: string;
  serverPath?: string;
  filename?: string;
  status?: "uploading" | "success" | "error";
}

const historyFrames = ref<HistoryFrame[]>([]);
const currentFrameIndex = ref(0);
const baselineFrame = ref<HistoryFrame | null>(null);
const currentAnalysisFrame = ref<HistoryFrame | null>(null);

const setBaseline = (frame: HistoryFrame) => {
  baselineFrame.value = frame;
};

const setCurrentAnalysis = (frame: HistoryFrame) => {
  currentAnalysisFrame.value = frame;
};

const processCapturedBase64 = async (base64Data: string, isBaseline: boolean = false) => {
  const now = new Date();
  const timeString = `今日 ${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
  const filename = `capture_${Date.now()}.jpg`;

  const newFrame: HistoryFrame = {
    time: timeString,
    url: base64Data,
    status: "uploading",
    filename: filename,
  };

  historyFrames.value.unshift(newFrame);
  const activeFrame = historyFrames.value[0];
  if (!activeFrame) return;

  currentFrameIndex.value = 0;
  if (isBaseline) {
    setBaseline(activeFrame);
  }

  try {
    // 将 base64 转换为 Blob
    const response = await fetch(base64Data);
    const blob = await response.blob();

    const formData = new FormData();
    formData.append("file", blob, filename);

    // 调用上传接口
    const uploadRes = await fetch("http://localhost:8000/files/upload", {
      method: "POST",
      body: formData,
    });

    if (uploadRes.ok) {
      const data = await uploadRes.json();
      activeFrame.serverPath = data.saved_path;
      activeFrame.status = "success";
      console.log("Image uploaded successfully:", data.saved_path);
    } else {
      activeFrame.status = "error";
      console.error("Failed to upload image:", uploadRes.statusText);
    }
  } catch (error) {
    activeFrame.status = "error";
    console.error("Error uploading image:", error);
  }
};

// 辅助方法：从萤石云播放器中截取当前画面
const captureFromPlayer = (isBaseline: boolean) => {
  if (!myPlayer) {
    alert("播放器未初始化或未就绪");
    return;
  }
  
  // 使用 ezuikit 提供的 capturePicture 方法，回调获取 base64
  myPlayer.capturePicture('default', (data: any) => {
    let base64Data = typeof data === 'string' ? data : (data?.base64 || data?.data);
    if (base64Data) {
      if (!base64Data.startsWith('data:')) {
        base64Data = 'data:image/jpeg;base64,' + base64Data;
      }
      processCapturedBase64(base64Data, isBaseline);
    } else {
      console.error("无法获取有效的截图数据:", data);
      alert("截图失败");
    }
  });
};

const captureFrameForBase = () => {
  captureFromPlayer(true);
};

const captureFrame = () => {
  captureFromPlayer(false);
};

// ==========================================
// AI 分析逻辑 (预留接口)
// ==========================================
const analysisDescription = ref("");
const isAnalyzing = ref(false);
const analysisResult = ref("");

// 【预留接口】大模型分析函数
const startAnalysis = async () => {
  if (isAnalyzing.value) return;

  if (!baselineFrame.value || !currentAnalysisFrame.value) {
    alert("请先选择基准图和目标图");
    return;
  }

  isAnalyzing.value = true;
  analysisResult.value = "";

  try {
    // ----------------------------------------------------
    // TODO: 在这里替换为实际的后端分析 API，处理流式返回或常规请求
    // ----------------------------------------------------
    console.log("准备发送给大模型的参数:", {
      baseline: baselineFrame.value.filename,
      target: currentAnalysisFrame.value.filename,
      prompt: analysisDescription.value
    });

    // 模拟接口请求和流式返回延迟
    await new Promise(resolve => setTimeout(resolve, 500));
    analysisResult.value += "分析结果正在生成...\n";
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    analysisResult.value += "对比基准图和目标图发现如下变化：\n1. 画面整体正常\n2. 未见明显异常活动\n";

    /*
    // 真实的 Fetch 请求示例代码：
    const response = await fetch("http://localhost:8000/api/llm/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        base_image: baselineFrame.value.filename,
        target_image: currentAnalysisFrame.value.filename,
        description: analysisDescription.value,
      }),
    });
    
    // 如果是流式接口 (SSE)，可使用 reader 进行分块读取并拼接到 analysisResult.value 中
    */

  } catch (error) {
    analysisResult.value = `分析请求失败: ${error}`;
  } finally {
    isAnalyzing.value = false;
  }
};

const generateReport = () => {
  alert("生成分析报告功能预留中...");
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
  min-width: 0;
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
  background-color: rgba(16, 185, 129, 0.2);
  color: #10b981;
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
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

.video-player-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 修改 EZUIKit 内部的样式以适配容器 */
:deep(#ezuikit-player video), :deep(#ezuikit-player canvas) {
  max-width: 100%;
  max-height: 100%;
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
  color: #fbbf24;
}

.status-badge.success {
  color: #4ade80;
}

.status-badge.error {
  color: #f87171;
}

.status-icon.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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

.comp-img {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 0;
  box-sizing: border-box;
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

.img-placeholder {
  width: 100%;
  aspect-ratio: 16/9;
  background-color: #1e293b;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #64748b;
  border: 1px dashed #475569;
  box-sizing: border-box;
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
  resize: vertical;
  min-height: 60px;
}

.description-input:focus {
  border-color: #3b82f6;
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

.markdown-output {
  font-size: 13px;
  line-height: 1.6;
  color: #cbd5e1;
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
