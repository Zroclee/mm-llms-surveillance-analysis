<template>
	<div class="home">
		<header class="header">
			<div class="logo">MM-LLMs 监控分析系统</div>
			<nav class="nav">
				<!-- 顶部导航栏，目前仅作为占位，实际功能通过下方按钮触发 -->
				<span>首页</span>
			</nav>
		</header>

		<main class="main-content">
			<div class="welcome-section">
				<h1>欢迎使用监控分析系统</h1>
				<p>请选择您要进入的功能模块</p>
			</div>

			<div class="navigation-cards">
				<div class="card monitor-card" @click="navigateTo('/monitor')">
					<h2>监控中心</h2>
					<p>实时查看监控画面与分析结果</p>
					<button class="nav-btn">进入监控页</button>
				</div>

				<div class="card house-card" @click="navigateTo('/house')">
					<h2>房源管理</h2>
					<p>管理房源信息与相关数据</p>
					<button class="nav-btn">进入房源页</button>
				</div>
			</div>
		</main>
	</div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

/**
 * Home 组件
 * 包含 Header、导航栏以及主要功能入口
 */

const router = useRouter();

/**
 * 页面跳转函数
 * @param path 路由路径
 */
const navigateTo = (path: string) => {
	router.push(path);
};
</script>

<style scoped>
.home {
	display: flex;
	flex-direction: column;
	min-height: 100vh;
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 1rem 2rem;
	background-color: #1a1a1a;
	color: white;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logo {
	font-size: 1.5rem;
	font-weight: bold;
}

.main-content {
	flex: 1;
	padding: 2rem;
	max-width: 1200px;
	margin: 0 auto;
	width: 100%;
	box-sizing: border-box;
}

.welcome-section {
	text-align: center;
	margin-bottom: 3rem;
}

.navigation-cards {
	display: flex;
	justify-content: center;
	gap: 2rem;
	flex-wrap: wrap;
}

.card {
	background-color: #2a2a2a;
	padding: 2rem;
	border-radius: 8px;
	width: 300px;
	text-align: center;
	cursor: pointer;
	transition: transform 0.2s, box-shadow 0.2s;
	border: 1px solid #333;
}

.card:hover {
	transform: translateY(-5px);
	box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
	border-color: #646cff;
}

.card h2 {
	margin-top: 0;
	color: #fff;
}

.card p {
	color: #aaa;
	margin-bottom: 1.5rem;
}

.nav-btn {
	padding: 0.5rem 1rem;
	background-color: #646cff;
	color: white;
	border: none;
	border-radius: 4px;
	cursor: pointer;
	font-size: 1rem;
}

.nav-btn:hover {
	background-color: #535bf2;
}

@media (prefers-color-scheme: light) {
	.header {
		background-color: #fff;
		color: #213547;
		border-bottom: 1px solid #eee;
	}

	.card {
		background-color: #f9f9f9;
		border-color: #eee;
	}

	.card h2 {
		color: #213547;
	}

	.card p {
		color: #666;
	}
}
</style>
