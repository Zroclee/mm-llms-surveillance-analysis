<template>
  <div class="satellite-monitor">
    <!-- 左侧地图区域 -->
    <div class="monitor-panel">
      <SatelliteMapComponent ref="mapComponent" :center="selectedProjectCenter" :fence="selectedProjectFence" />
    </div>

    <!-- 右侧 AI 分析侧边栏 -->
    <div class="ai-sidebar">
      <div class="sidebar-header">
        <h2><span class="ai-icon">⟡</span> AI 智能分析面板</h2>
      </div>

      <div class="sidebar-content">
        <!-- 工程选择 -->
        <section class="analysis-section">
          <h3 class="section-title">选择工程</h3>
          <select v-model="selectedProject" class="project-select">
            <option v-for="proj in projects" :key="proj.id" :value="proj.id">
              {{ proj.name }}
            </option>
          </select>
        </section>

        <!-- 立即分析按钮 -->
        <div class="action-area">
          <button
            class="analyze-btn"
            :disabled="isAnalyzing"
            @click="startAnalysis"
          >
            <span v-if="isAnalyzing">分析中...</span>
            <span v-else>✧ AI 智能分析</span>
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
        <button 
          class="report-btn" 
          :disabled="isAnalyzing || !analysisResult || analysisResult.includes('正在获取卫星云图截图')" 
          @click="generateReport"
        >
          📄 生成分析报告 (PDF)
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import SatelliteMapComponent from "../components/SatelliteMap.vue";
import MarkdownIt from "markdown-it";
import html2pdf from "html2pdf.js";

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
});

const mapComponent = ref<any>(null);

const projects = [
  {
    id: "proj0",
    name: "蔡屋围小学",
    center: [114.108938, 22.539372] as [number, number],
    fence: [
      [114.108452, 22.5397],
      [114.10946, 22.53974],
      [114.109465, 22.539231],
      [114.108469, 22.539231],
    ] as [number, number][],
    description: "罗湖区蔡屋围小学重建项目。规划为36班小学，总建筑面积约2.5万平方米。包含教学楼、综合楼、地下车库及室外运动场等配套设施。",
  },
  {
    id: "proj1",
    name: "天健天骄",
    center: [121.304018, 31.217688] as [number, number],
    fence: [] as [number, number][],
    description: "天健天骄高端住宅社区项目。占地面积约3.2万平方米，总建筑面积约15万平方米，主要建设高层住宅、配套商业及幼儿园。",
  },
  {
    id: "proj2",
    name: "银康苑动迁安置房",
    center: [121.5043258, 31.2392241] as [number, number],
    fence: [] as [number, number][],
    description: "银康苑动迁安置房工程。项目总建筑面积约8万平方米，由多栋高层住宅及地下车库组成，用于安置周边拆迁居民，提供完善的生活配套。",
  },
  {
    id: "proj3",
    name: "陆家嘴中心",
    center: [121.500419, 31.238089] as [number, number],
    fence: [] as [number, number][],
    description: "陆家嘴核心区商业综合体项目。涵盖超高层写字楼、大型购物中心及高端酒店。总建筑面积超30万平方米，是区域内的地标性建筑。",
  },
];

const selectedProject = ref("proj0");
const selectedProjectCenter = computed(() => {
  const proj = projects.find((p) => p.id === selectedProject.value);
  return (proj?.center || projects[0]?.center || [121.304018, 31.217688]) as [
    number,
    number,
  ];
});

const selectedProjectFence = computed(() => {
  const proj = projects.find((p) => p.id === selectedProject.value);
  return proj?.fence || [];
});

const isAnalyzing = ref(false);
const analysisResult = ref("");

const formattedResult = computed(() => {
  if (!analysisResult.value) return "";
  return md.render(analysisResult.value);
});

const startAnalysis = async () => {
  if (isAnalyzing.value) return;

  isAnalyzing.value = true;
  analysisResult.value = "正在获取卫星云图截图，请稍候...\n";

  const currentProj = projects.find((p) => p.id === selectedProject.value);
  
  if (!mapComponent.value) {
    analysisResult.value += "\n错误：地图组件未初始化。";
    isAnalyzing.value = false;
    return;
  }

  try {
    // 1. 截图
    const dataUrl = await mapComponent.value.captureMap();
    
    // 2. 将 base64 转换为 Blob
    const res = await fetch(dataUrl);
    const blob = await res.blob();
    const filename = `satellite_${Date.now()}.png`;

    // 3. 上传图片
    analysisResult.value = "卫星云图获取成功，正在上传并分析...\n";
    const formData = new FormData();
    formData.append("file", blob, filename);

    const uploadResponse = await fetch("http://localhost:8000/files/upload", {
      method: "POST",
      body: formData,
    });

    if (!uploadResponse.ok) {
      throw new Error(`上传失败: ${uploadResponse.statusText}`);
    }

    const uploadData = await uploadResponse.json();
    const serverPath = uploadData.saved_path;
    const uploadedFilename = serverPath.split('/').pop() || filename;

    // 4. 调用流式分析接口
    analysisResult.value = ""; // 清空提示，准备接收结果
    
    const analysisResponse = await fetch("http://localhost:8000/agent/map/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_name: uploadedFilename,
        description: currentProj?.description || "",
      }),
    });

    if (!analysisResponse.ok) {
      throw new Error(`分析请求失败: ${analysisResponse.statusText}`);
    }

    const reader = analysisResponse.body?.getReader();
    if (!reader) {
      throw new Error("无法读取响应流");
    }

    const decoder = new TextDecoder("utf-8");
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const dataStr = line.slice(6);
          if (dataStr === "[DONE]") {
            break;
          }
          try {
            const dataObj = JSON.parse(dataStr);
            if (dataObj.content) {
              analysisResult.value += dataObj.content;
            }
          } catch (e) {
            console.error("解析流式数据失败:", e, dataStr);
          }
        }
      }
    }

  } catch (error: any) {
    console.error("分析过程出错:", error);
    analysisResult.value += `\n**分析失败**: ${error.message}`;
  } finally {
    isAnalyzing.value = false;
  }
};

const generateReport = () => {
  const element = document.querySelector('.markdown-content');
  if (!element || !analysisResult.value || isAnalyzing.value) {
    alert('暂无完整分析结果可生成报告');
    return;
  }
  
  const currentProj = projects.find((p) => p.id === selectedProject.value);
  const projName = currentProj?.name || '项目';
  
  const opt: any = {
    margin:       10,
    filename:     `${projName}_卫星云图评估报告_${new Date().toISOString().slice(0,10)}.pdf`,
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2, useCORS: true },
    jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
  };

  html2pdf().set(opt).from(element as HTMLElement).save();
};
</script>

<style scoped>
/* 全局容器 */
.satellite-monitor {
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
  position: relative;
  min-width: 0;
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

/* 表单元素 */
.project-select {
  width: 100%;
  box-sizing: border-box;
  background-color: #1e293b;
  border: 1px solid #334155;
  color: #e2e8f0;
  border-radius: 6px;
  padding: 10px;
  font-size: 13px;
  outline: none;
  cursor: pointer;
}

.project-select:focus {
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
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.markdown-output::-webkit-scrollbar {
  width: 6px;
}

.markdown-output::-webkit-scrollbar-thumb {
  background-color: #475569;
  border-radius: 3px;
}

.typing-indicator {
  color: #94a3b8;
  font-size: 13px;
  font-style: italic;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

/* Markdown 内容样式 */
:deep(.markdown-content) {
  font-size: 14px;
  line-height: 1.6;
  color: #e2e8f0;
}

:deep(.markdown-content h1),
:deep(.markdown-content h2),
:deep(.markdown-content h3) {
  color: #f8fafc;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

:deep(.markdown-content p) {
  margin-bottom: 1em;
}

:deep(.markdown-content ul),
:deep(.markdown-content ol) {
  padding-left: 20px;
  margin-bottom: 1em;
}

:deep(.markdown-content li) {
  margin-bottom: 0.5em;
}

:deep(.markdown-content strong) {
  color: #60a5fa;
  font-weight: 600;
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
  transition: all 0.2s;
}

.report-btn:hover:not(:disabled) {
  border-color: #475569;
  color: #e2e8f0;
}

.report-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
