<script setup lang="ts">
/**
 * App 根组件
 * 系统的根容器，只保留路由出口
 */
</script>

<template>
	<div class="app-container">
		<router-view></router-view>
	</div>
</template>

<style scoped>
.app-container {
	width: 100%;
	height: 100%;
}
</style>
