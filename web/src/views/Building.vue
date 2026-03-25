<template>
  <div class="building-dashboard">
    <!-- 底部全屏地图 -->
    <div class="map-wrapper">
      <MapContainer />
    </div>

    <!-- 右侧悬浮数据面板 -->
    <div class="right-panel">
      <!-- 窗口 1 -->
      <div class="data-window">
        <div class="window-header">
          <h3>建筑基础信息</h3>
        </div>
        <div class="window-content">
          <div class="content-placeholder">基础数据展示区</div>
        </div>
      </div>
      
      <!-- 窗口 2 -->
      <div class="data-window">
        <div class="window-header">
          <h3>实时监控状态</h3>
        </div>
        <div class="window-content">
          <div class="content-placeholder">监控数据展示区</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MapContainer from '../components/MapContainer.vue'
</script>

<style scoped>
.building-dashboard {
  position: relative;
  width: 100%;
  height: 100vh; /* 全屏高度 */
  overflow: hidden;
  background-color: #050f22; /* 兜底深色背景 */
}

/* 地图容器 */
.map-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1; /* 地图层级在下 */
}

/* 右侧悬浮面板容器 */
.right-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 400px;
  height: calc(100% - 40px); /* 上下留白 20px */
  z-index: 10; /* 悬浮层级在上 */
  display: flex;
  flex-direction: column;
  gap: 20px;
  /* 允许鼠标穿透面板容器的空白区域，点击地图 */
  pointer-events: none;
}

/* 悬浮窗口 */
.data-window {
  flex: 1;
  background: rgba(11, 25, 48, 0.85); /* 科技感半透明深蓝背景 */
  border: 1px solid rgba(0, 204, 255, 0.3); /* 科技蓝边框 */
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), inset 0 0 10px rgba(0, 204, 255, 0.1);
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  color: #fff;
  /* 恢复面板本身的鼠标交互 */
  pointer-events: auto;
}

/* 窗口头部 */
.window-header {
  padding: 16px;
  border-bottom: 1px solid rgba(0, 204, 255, 0.2);
  background: linear-gradient(90deg, rgba(0, 204, 255, 0.1) 0%, transparent 100%);
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.window-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #00ffff;
  letter-spacing: 1px;
}

/* 窗口内容区 */
.window-content {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

/* 临时占位样式 */
.content-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed rgba(0, 204, 255, 0.2);
  border-radius: 4px;
  color: rgba(0, 204, 255, 0.5);
  font-size: 14px;
  background: rgba(0, 204, 255, 0.02);
}
</style>
