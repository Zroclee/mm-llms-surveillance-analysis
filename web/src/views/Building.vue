<template>
  <div class="building-dashboard">
    <!-- 底部全屏地图 -->
    <div class="map-wrapper">
      <MapContainer ref="mapContainerRef" :markerData="markerData" />
    </div>

    <!-- 右侧悬浮数据面板 -->
    <div class="right-panel">
      <!-- 窗口 1 -->
      <div class="data-window full-height-window">
        <div class="window-header">
          <h3>建筑基础信息</h3>
        </div>
        <div class="window-content building-list">
          <div 
            v-for="(feature, index) in markerData.features" 
            :key="index"
            class="building-item"
            @click="handleBuildingClick(feature.geometry.coordinates)"
          >
            <span class="building-name">{{ feature.properties.name }}</span>
            <span class="building-price">{{ feature.properties.price / 10000 }}万</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MapContainer from '../components/MapContainer.vue'

const mapContainerRef = ref<InstanceType<typeof MapContainer> | null>(null)

const markerData = { 
    "type": "FeatureCollection", 
    "features": [
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.59008979797363,39.90058428630659]},"properties":{"name":"远洋一方润园","price":65000,"count":92}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.59378051757811,39.89704498575387]},"properties":{"name":"远洋一方溪语苑","price":65000,"count":52}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.59366250038148,39.90657598772839]},"properties":{"name":"东会新村","price":49000,"count":53}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.60161256790161,39.91717540663561]},"properties":{"name":"北京新天地（东区）","price":62000,"count":639}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.59092664718628,39.913423004886894]},"properties":{"name":"京通苑阳光华苑","price":48000,"count":651}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.59223556518555,39.92263906258135]},"properties":{"name":"龙湖长楹天街","price":76000,"count":12}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.58066987991333,39.92166814352715]},"properties":{"name":"柏林爱乐","price":62000,"count":471}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.5806484222412,39.91766912840225]},"properties":{"name":"汇鸿家园","price":58000,"count":65}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.5688467025757,39.91737289576941]},"properties":{"name":"三间房南里","price":53000,"count":45}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.57416820526123,39.9034814381334]},"properties":{"name":"康惠园三号院","price":48000,"count":95}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.60126924514769,39.89893812274133]},"properties":{"name":"东一时区小区","price":54000,"count":199}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.60905838012695,39.90331683051646]},"properties":{"name":"八里桥南院","price":44000,"count":2}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.62437915802002,39.9101312551376]},"properties":{"name":"西马庄园","price":36000,"count":102}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.60266399383545,39.929747745342944]},"properties":{"name":"保利嘉园1号院","price":53000,"count":125}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.56524181365967,39.92691752490338]},"properties":{"name":"朝青知筑","price":80000,"count":36}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.54335498809814,39.903678966751734]},"properties":{"name":"北花园小区1号院","price":50000,"count":2}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.54949188232422,39.921421297504764]},"properties":{"name":"瑞和国际","price":49000,"count":74}},
        {"type":"Feature","geometry":{"type":"Point","coordinates":[116.63712501525877,39.92444921388591]},"properties":{"name":"天赐良园（东区）","price":49000,"count":51}}
    ] 
}

const handleBuildingClick = (coordinates: number[]) => {
  if (mapContainerRef.value) {
    mapContainerRef.value.focusOnBuilding(coordinates)
  }
}
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

.full-height-window {
  height: 100%;
}

.building-list {
  overflow-y: auto;
  gap: 12px;
}

.building-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(0, 204, 255, 0.05);
  border: 1px solid rgba(0, 204, 255, 0.1);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.building-item:hover {
  background: rgba(0, 204, 255, 0.15);
  border-color: rgba(0, 204, 255, 0.4);
  transform: translateX(-4px);
}

.building-name {
  font-size: 15px;
  color: #fff;
  font-weight: 500;
}

.building-price {
  font-size: 14px;
  color: #00ffff;
  font-weight: bold;
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
