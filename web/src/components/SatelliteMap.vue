<template>
  <div class="map-wrapper">
    <div id="satellite-map-container"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch, shallowRef } from "vue";
import AMapLoader from "@amap/amap-jsapi-loader";
import html2canvas from "html2canvas";

const props = defineProps<{
  center?: [number, number]; // 经纬度参数 [longitude, latitude]
  fence?: [number, number][]; // 围栏参数，多边形路径点
}>();

const map = shallowRef<any>(null);
const currentPolygon = shallowRef<any>(null); // 保存当前的多边形实例

// 内部方法：绘制多边形围栏
const drawPolygon = (path?: [number, number][]) => {
  if (!map.value) return;

  // 如果已经有绘制的多边形，先清除
  if (currentPolygon.value) {
    map.value.remove(currentPolygon.value);
    currentPolygon.value = null;
  }

  // 如果传入的路径为空，则只清除不绘制
  if (!path || path.length === 0) return;

  // 使用 AMap 绘制多边形
  const AMap = (window as any).AMap;
  if (!AMap) return;

  currentPolygon.value = new AMap.Polygon({
    path: path,
    strokeColor: "red", // 线条颜色 (蓝色)
    strokeWeight: 3, // 线条宽度
    strokeOpacity: 0.8, // 线条透明度
    fillOpacity: 0, // 填充完全透明，不影响 AI 识别
    zIndex: 50,
  });

  map.value.add(currentPolygon.value);
  
  // 自动缩放地图以适应多边形
  // map.value.setFitView([currentPolygon.value]);
};

// 监听经纬度参数变化，动态更新地图中心点
watch(
  () => props.center,
  (newCenter) => {
    if (map.value && newCenter && newCenter.length === 2) {
      // 使用 panTo 实现动画平滑移动
      map.value.panTo(newCenter);
      // 延时绘制新的多边形，等待平滑移动
      setTimeout(() => {
        drawPolygon(props.fence);
      }, 500);
    }
  },
  { deep: true },
);

// 暴露截图方法
const captureMap = (): Promise<string> => {
  return new Promise((resolve, reject) => {
    if (!map.value) {
      reject(new Error("地图未初始化"));
      return;
    }

    const center = props.center || [121.304018, 31.217688];
    console.log("准备截图，设置中心点和缩放:", center);
    map.value.setZoomAndCenter(19, center);

    let isResolved = false;

    // 监听地图加载完成事件以确保瓦片渲染完毕
    const onMapComplete = () => {
      if (isResolved) return;
      isResolved = true;
      console.log("地图渲染完成(complete)事件已触发");
      map.value.off('complete', onMapComplete);
      
      // 额外延迟一点时间，确保高德的动画和瓦片完全绘制完成
      setTimeout(async () => {
        try {
          console.log("开始执行 html2canvas 截图...");
          const mapContainer = document.getElementById("satellite-map-container");
          if (!mapContainer) {
            reject(new Error("找不到地图容器"));
            return;
          }
          
          const canvas = await html2canvas(mapContainer, {
            useCORS: true, // 允许跨域图片，解决高德瓦片跨域问题
            backgroundColor: null
          });
          console.log("html2canvas 截图成功");
          resolve(canvas.toDataURL("image/png"));
        } catch (error) {
          console.error("截图失败:", error);
          reject(error);
        }
      }, 1000);
    };

    map.value.on('complete', onMapComplete);
    
    // 如果地图中心点本身没变，或者由于缓存原因 complete 事件没有被触发
    // 设置一个兜底的超时强制执行截图
    setTimeout(() => {
      if (!isResolved) {
        console.warn("触发超时兜底机制，未收到 complete 事件，强制进行截图");
        onMapComplete();
      }
    }, 3000);

    // 触发一次重绘或者如果在同层级也会触发complete
    map.value.panTo(center);
  });
};

defineExpose({
  captureMap
});

onMounted(() => {
  AMapLoader.load({
    key: import.meta.env.VITE_GAODE_KEY, // 沿用原有的 Web 端开发者 Key
    version: "2.0", // 指定要加载的 JSAPI 的版本
    plugins: [], // 需要使用的的插件列表
  })
    .then((AMap) => {
      // 创建卫星图层
      const satelliteLayer = new AMap.TileLayer.Satellite();

      map.value = new AMap.Map("satellite-map-container", {
        viewMode: "3D", // 开启 3D 模式
        zoom: 19, // 设置合适的缩放级别
        center: props.center || [121.304018, 31.217688], // 默认或者传入的中心点
        layers: [satelliteLayer], // 将图层替换为卫星图层
        WebGLParams: {
          preserveDrawingBuffer: true // 允许对 WebGL Canvas 进行截图
        }
      });
      map.value.on("complete", function () {
        console.log("地图加载完成！");
        // 初始化时绘制围栏
        if (props.fence && props.fence.length > 0) {
          drawPolygon(props.fence);
        }
      });
    })
    .catch((e) => {
      console.error("高德地图加载失败:", e);
    });
});

onUnmounted(() => {
  map.value?.destroy();
  map.value = null;
});
</script>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}
#satellite-map-container {
  width: 100%;
  height: 100%;
  min-width: 400px;
}
</style>
