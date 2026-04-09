<template>
  <div class="map-wrapper">
    <div id="map-container"></div>
    <!-- <button class="start-btn" @click="startAnimation">开始动画</button> -->
    <button class="tour-btn" @click="startTour">标点巡游</button>
  </div>
</template>
<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import AMapLoader from "@amap/amap-jsapi-loader";

const props = defineProps<{
  markerData: any;
}>();

let map: any = null;
let loca: any = null;
let pl: any = null;

const startTour = () => {
  if (!loca || !map) return;

  const features = props.markerData.features;
  if (features.length === 0) return;

  const firstPoint = features[0]?.geometry?.coordinates;
  if (!firstPoint) return;

  // 初始视角设置得高一点，俯视（pitch: 0），用于下钻动画的起点
  map.setCenter(firstPoint, true);
  map.setZoom(12.8, true);
  map.setPitch(0, true);

  setTimeout(() => {
    loca.animate.start();

    // 构建中间标点巡游的动画帧
    const tourAnimates = features.map((feat: any, i: number) => {
      const currentCoord = feat.geometry?.coordinates;
      const prevCoord =
        i === 0 ? currentCoord : features[i - 1]?.geometry?.coordinates;

      return {
        center: {
          value: currentCoord,
          control: [prevCoord || currentCoord, currentCoord],
          timing: [0.3, 0, 0.7, 1],
          duration: i === 0 ? 3000 : 2000,
        },
        zoom: {
          value: 16.5,
          control: [
            [0, 16.5],
            [1, 16.5],
          ],
          timing: [0.3, 0, 0.7, 1],
          duration: i === 0 ? 3000 : 2000,
        },
        pitch: {
          value: 45,
          control: [
            [0, 45],
            [1, 45],
          ],
          timing: [0.3, 0, 0.7, 1],
          duration: i === 0 ? 3000 : 2000,
        },
        rotation: {
          value: i * 30,
          control: [
            [0, (i - 1) * 30],
            [1, i * 30],
          ],
          timing: [0.3, 0, 0.7, 1],
          duration: i === 0 ? 3000 : 2000,
        },
      };
    });

    // 1. 下钻动画：拉近距离，视角变成俯视45度
    loca.viewControl.addAnimates(
      [
        {
          pitch: {
            value: 45,
            control: [
              [0, 0],
              [1, 45],
            ],
            timing: [0, 0, 0.8, 1],
            duration: 3000,
          },
          zoom: {
            value: 16.5,
            control: [
              [0, 12.8],
              [1, 16.5],
            ],
            timing: [0, 0, 0.8, 1],
            duration: 3000,
          },
        },
      ],
      function () {
        // 2. 标点巡游动画
        loca.viewControl.addAnimates(tourAnimates, function () {
          // 3. 巡游结束后：拉起，视角垂直向下 (pitch: 0)
          loca.viewControl.addAnimates(
            [
              {
                pitch: {
                  value: 0,
                  control: [
                    [0, 45],
                    [1, 0],
                  ],
                  timing: [0.1, 0, 0.7, 1],
                  duration: 2500,
                },
                zoom: {
                  value: 12.8,
                  control: [
                    [0, 16.5],
                    [1, 12.8],
                  ],
                  timing: [0.3, 0, 0.7, 1],
                  duration: 2500,
                },
                rotation: {
                  value: 360,
                  control: [
                    [
                      0,
                      tourAnimates[tourAnimates.length - 1]?.rotation?.value ||
                        0,
                    ],
                    [1, 360],
                  ],
                  timing: [0.3, 0, 0.7, 1],
                  duration: 2500,
                },
              },
            ],
            function () {
              console.log("标点巡游及拉起结束");
            },
          );
        });
      },
    );
  }, 500);
};

// const startAnimation = () => {
//   if (loca && pl) {
//     loca.animate.start();
//     animate();
//   }
// };

const focusOnBuilding = (coordinates: number[]) => {
  if (!map || !loca) return;

  // 中断当前所有的动画
  if (loca.viewControl) {
    loca.viewControl.clearAnimates();
  }

  // 定位到对应的建筑标点
  map.setCenter(coordinates, true);
  map.setZoom(16.5, true);
  map.setPitch(45, true);
};

defineExpose({
  focusOnBuilding,
});

// function animate() {
//   var speed = 1;
//   // 镜头动画
//   map.setZoom(11.8, true);
//   map.setPitch(0, true);
//   map.setCenter([121.304018, 31.217688], true);
//   map.setRotation(1, true);
//   pl.hide(1000);

//   // 下钻
//   loca.viewControl.addAnimates([{
//     pitch: {
//       value: 0,
//       control: [[0, 20], [1, 0]],
//       timing: [0, 0, 0.8, 1],
//       duration: 3000 / speed,
//     },
//     zoom: {
//       value: 15.9,
//       control: [[0, 12.8], [1, 15.9]],
//       timing: [0, 0, 0.8, 1],
//       duration: 3000 / speed,
//     },
//     rotation: {
//       value: -20,
//       control: [[0, 20], [1, -20]],
//       timing: [0, 0, 0.8, 1],
//       duration: 2000 / speed,
//     },
//   }], function () {
//     setTimeout(function () {
//       pl.show(2000);
//     }, 3000);

//     loca.viewControl.addAnimates([
//       // 寻迹
//       {
//         center: {
//           value: [121.500419, 31.238089],
//           control: [[121.424503326416, 31.199146851153124], [121.46656036376952, 31.245828642661486]],
//           timing: [0.3, 0, 0.1, 1],
//           duration: 8000 / speed,
//         },
//         zoom: {
//           value: 17,
//           control: [[0.3, 15], [1, 17]],
//           timing: [0.3, 0, 0.7, 1],
//           duration: 4000 / speed,
//         },
//         pitch: {
//           value: 50,
//           control: [[0.3, 0], [1, 50]],
//           timing: [0.3, 0, 1, 1],
//           duration: 3000 / speed,
//         },
//         rotation: {
//           value: -80,
//           control: [[0, -20], [1, -80]],
//           timing: [0, 0, 1, 1],
//           duration: 1000 / speed,
//         },
//       }, {
//         // 环绕
//         pitch: {
//           value: 50,
//           control: [[0, 40], [1, 50]],
//           timing: [0.3, 0, 1, 1],
//           duration: 7000 / speed,
//         },
//         rotation: {
//           value: 260,
//           control: [[0, -80], [1, 260]],
//           timing: [0, 0, 0.7, 1],
//           duration: 7000 / speed,
//         },
//         zoom: {
//           value: 17,
//           control: [[0.3, 16], [1, 17]],
//           timing: [0.3, 0, 0.9, 1],
//           duration: 5000 / speed,
//         },
//       }, {
//         // 拉起
//         center: {
//           value: [121.500419, 31.238089],
//           control: [[121.49986267089844, 31.227628422210365], [121.49969100952148, 31.24025152837923]],
//           timing: [0.3, 0, 0.7, 1],
//           duration: 2000 / speed,
//         },
//         pitch: {
//           value: 0,
//           control: [[0, 0], [1, 100]],
//           timing: [0.1, 0, 0.7, 1],
//           duration: 2000 / speed,
//         },
//         rotation: {
//           value: 361,
//           control: [[0, 260], [1, 361]],
//           timing: [0.3, 0, 0.7, 1],
//           duration: 2000 / speed,
//         },
//         zoom: {
//           value: 13.8,
//           control: [[0, 17.5], [1, 13.8]],
//           timing: [0.3, 0, 0.7, 1],
//           duration: 2500 / speed,
//         },
//       }], function () {
//         pl.hide(1000);
//         console.log('结束');
//       });
//   });
// }

onMounted(() => {
  AMapLoader.load({
    key: "383f3cc941db222b67078484daa7a58a", // 申请好的Web端开发者Key，首次调用 load 时必填
    version: "2.0", // 指定要加载的 JSAPI 的版本，缺省时默认为 1.4.15
    plugins: [], // 需要使用的的插件列表，如比例尺'AMap.Scale'等
    Loca: {
      version: "2.0.0",
    },
  })
    .then((AMap) => {
      map = new AMap.Map("map-container", {
        viewMode: "3D",
        zoom: 11.8,
        center: [121.304018, 31.217688],
        mapStyle: "amap://styles/darkblue", // 改用高德官方内置的暗色主题
        showBuildingBlock: false,
        showLabel: false,
      });

      const Loca = (window as any).Loca;
      loca = new Loca.Container({
        map,
      });

      loca.ambLight = {
        intensity: 2.2,
        color: "#babedc",
      };
      loca.dirLight = {
        intensity: 0.46,
        color: "#d4d4d4",
        target: [0, 0, 0],
        position: [0, -1, 1],
      };
      loca.pointLight = {
        color: "rgb(15,19,40)",
        position: [121.5043258, 31.2392241, 2600],
        intensity: 25,
        // 距离表示从光源到光照强度为 0 的位置，0 就是光不会消失。
        distance: 3900,
      };
      var geo = new Loca.GeoJSONSource({
        url: "https://a.amap.com/Loca/static/loca-v2/demos/mock_data/sh_building_center.json",
      });

      pl = new Loca.PolygonLayer({
        zIndex: 120,
        shininess: 10,
        hasSide: true,
        cullface: "back",
        depth: true,
      });

      pl.setSource(geo);
      pl.setStyle({
        topColor: "#111",
        height: function (_index: number, feature: any) {
          return feature.properties.h;
        },
        textureSize: [1000, 820],
        texture:
          "https://a.amap.com/Loca/static/loca-v2/demos/images/windows.jpg",
      });
      pl.setLoca(loca);

      var dat = new Loca.Dat();
      dat.addLight(loca.ambLight, loca, "环境光");
      dat.addLight(loca.dirLight, loca, "平行光");
      dat.addLight(loca.pointLight, loca, "点光");
      dat.addLayer(pl, "楼块");

      // --- 新增标点牌及相关图层 ---
      var markerGeo = new Loca.GeoJSONSource({
        data: props.markerData,
      });

      // 文字主体图层
      var zMarker = new Loca.ZMarkerLayer({
        loca: loca,
        zIndex: 120,
        depth: false,
      });
      zMarker.setSource(markerGeo);
      zMarker.setStyle({
        content: (_i: number, feat: any) => {
          var props = feat.properties;
          var leftColor =
            props.price < 60000 ? "rgba(0, 28, 52, 0.6)" : "rgba(33,33,33,0.6)";
          var rightColor =
            props.price < 60000 ? "#038684" : "rgba(172, 137, 51, 0.3)";
          var borderColor =
            props.price < 60000 ? "#038684" : "rgba(172, 137, 51, 1)";
          return (
            '<div style="width: 490px; height: 228px; padding: 0 0;">' +
            '<p style="display: block; height:80px; line-height:80px;font-size:40px;background-image: linear-gradient(to right, ' +
            leftColor +
            "," +
            leftColor +
            "," +
            rightColor +
            ",rgba(0,0,0,0.4)); border:4px solid " +
            borderColor +
            '; color:#fff; border-radius: 15px; text-align:center; margin:0; padding:5px;">' +
            props["name"] +
            ": " +
            props["price"] / 10000 +
            '</p><span style="width: 130px; height: 130px; margin: 0 auto; display: block; background: url(https://a.amap.com/Loca/static/loca-v2/demos/images/prism_' +
            (props["price"] < 60000 ? "blue" : "yellow") +
            '.png);"></span></div>'
          );
        },
        unit: "meter",
        rotation: 0,
        alwaysFront: true,
        size: [490 / 2, 222 / 2],
        altitude: 0,
      });

      // 浮动三角
      var triangleZMarker = new Loca.ZMarkerLayer({
        loca: loca,
        zIndex: 119,
        depth: false,
      });
      triangleZMarker.setSource(markerGeo);
      triangleZMarker.setStyle({
        content: (_i: number, feat: any) => {
          return (
            '<div style="width: 120px; height: 120px; background: url(https://a.amap.com/Loca/static/loca-v2/demos/images/triangle_' +
            (feat.properties.price < 60000 ? "blue" : "yellow") +
            '.png);"></div>'
          );
        },
        unit: "meter",
        rotation: 0,
        alwaysFront: true,
        size: [60, 60],
        altitude: 15,
      });
      triangleZMarker.addAnimate({
        key: "altitude",
        value: [0, 1],
        random: true,
        transform: 1000,
        delay: 2000,
        yoyo: true,
        repeat: 999999,
      });

      // 呼吸点 蓝色
      var scatterBlue = new Loca.ScatterLayer({
        loca,
        zIndex: 110,
        opacity: 1,
        visible: true,
        zooms: [2, 26],
        depth: false,
      });

      scatterBlue.setSource(markerGeo);
      scatterBlue.setStyle({
        unit: "meter",
        size: function (_i: number, feat: any) {
          return feat.properties.price < 60000 ? [90, 90] : [0, 0];
        },
        texture:
          "https://a.amap.com/Loca/static/loca-v2/demos/images/scan_blue.png",
        altitude: 20,
        duration: 2000,
        animate: true,
      });

      // 呼吸点 金色
      var scatterYellow = new Loca.ScatterLayer({
        loca,
        zIndex: 110,
        opacity: 1,
        visible: true,
        zooms: [2, 26],
        depth: false,
      });

      scatterYellow.setSource(markerGeo);
      scatterYellow.setStyle({
        unit: "meter",
        size: function (_i: number, feat: any) {
          return feat.properties.price > 60000 ? [90, 90] : [0, 0];
        },
        texture:
          "https://a.amap.com/Loca/static/loca-v2/demos/images/scan_yellow.png",
        altitude: 20,
        duration: 2000,
        animate: true,
      });

      // 启动帧
      loca.animate.start();

      // 默认隐藏楼块，仅在动画中展示
      pl.hide();
    })
    .catch((e) => {
      console.log(e);
    });
});

onUnmounted(() => {
  map?.destroy();
});
</script>
<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}
#map-container {
  width: 100%;
  height: 100%;
  min-width: 400px;
}
.start-btn {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 999;
  padding: 8px 16px;
  background-color: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
.start-btn:hover {
  background-color: #40a9ff;
}
.tour-btn {
  position: absolute;
  top: 60px;
  left: 20px;
  z-index: 999;
  padding: 8px 16px;
  background-color: #52c41a;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
.tour-btn:hover {
  background-color: #73d13d;
}
</style>
