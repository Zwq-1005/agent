<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const steps = [
  {
    number: 1,
    title: '导入医学数据',
    description: '上传 CSV、Excel、JSON、SPSS、Stata 格式的临床研究数据，系统自动解析表头。定义每个字段的类型（数值/分类/等级/日期），设置显示名称和水平标签。',
  },
  {
    number: 2,
    title: '数据清洗与预处理',
    description: '检测缺失值与异常值，自动生成数据质量报告。支持缺失值填充、异常值剔除、重复行删除等清洗操作。',
  },
  {
    number: 3,
    title: '套用统计 Prompt 模版',
    description: '从预设的医学统计模板库中选择分析方法（t检验、ANOVA、卡方检验、回归分析、生存分析等），编辑 Prompt 后复制到剪贴板。',
  },
  {
    number: 4,
    title: 'AI 自动统计分析',
    description: '粘贴 Prompt 到分析工作台，AI 自动生成 Python 分析代码并执行，实时返回统计结果、图表和论文格式的描述文本。',
  },
  {
    number: 5,
    title: '导出统计报告',
    description: '分析完成后，一键下载 Word 或 PDF 格式的统计分析报告，直接用于论文撰写。',
  },
]

const features = [
  { title: '描述性统计', desc: '基线资料表、均值±SD、中位数(IQR)、频数(%)', icon: '📊' },
  { title: '组间比较', desc: 't检验、Mann-Whitney U、ANOVA、Kruskal-Wallis', icon: '🔬' },
  { title: '回归分析', desc: '线性回归、Logistic回归、Cox比例风险模型', icon: '📈' },
  { title: '生存分析', desc: 'Kaplan-Meier曲线、Log-rank检验、Cox回归', icon: '⏱️' },
  { title: '相关性分析', desc: 'Pearson/Spearman相关、偏相关、热力图', icon: '🔗' },
  { title: '分类变量分析', desc: '卡方检验、Fisher精确检验、Cochran-Mantel-Haenszel检验', icon: '📋' },
  { title: '诊断试验', desc: 'ROC曲线、AUC计算、最佳截断值、敏感度/特异度', icon: '🎯' },
  { title: '数据可视化', desc: '箱线图、森林图、列线图、小提琴图、热力图', icon: '🎨' },
]

function goToImport() {
  router.push('/import')
}
</script>

<template>
  <div class="home-page">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">医学统计<span class="gradient-text">AI助手</span></h1>
        <p class="hero-subtitle">
          基于 AI + LangGraph 的智能医学统计分析平台。<br/>
          上传临床数据 → 数据清洗 → 自然语言描述需求 → 自动生成论文级统计结果
        </p>
        <div class="hero-actions">
          <n-button type="primary" size="large" round @click="goToImport">
            开始分析
            <template #icon>
              <n-icon>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
                </svg>
              </n-icon>
            </template>
          </n-button>
          <n-button type="primary" size="large" round @click="router.push('/prompts')">
            查看统计模板
          </n-button>
        </div>
        <div class="hero-tags">
          <n-tag type="info" round>描述性统计</n-tag>
          <n-tag type="info" round>t检验 / ANOVA</n-tag>
          <n-tag type="info" round>卡方检验</n-tag>
          <n-tag type="info" round>Logistic回归</n-tag>
          <n-tag type="info" round>生存分析</n-tag>
          <n-tag type="info" round>ROC曲线</n-tag>
        </div>
      </div>
    </section>

    <!-- How to use -->
    <section class="usage-section">
      <div class="section-inner">
        <div class="steps-panel">
          <h2 class="section-title">使用方法（5 步流程）</h2>
          <div class="steps-list">
            <div v-for="step in steps" :key="step.number" class="step-item">
              <div class="step-number">{{ step.number }}</div>
              <div class="step-body">
                <h4>{{ step.title }}</h4>
                <p>{{ step.description }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="info-panel">
          <div class="info-card">
            <h3>⚠️ 维护时间</h3>
            <p>服务器每日凌晨 <strong>4:00 - 4:10</strong> 重启维护，请及时保存统计结果文档。</p>
          </div>
          <div class="info-card">
            <h3>📦 数据限制</h3>
            <p>基础版支持 <strong>1MB</strong> 以内数据文件，VIP 版支持 <strong>20MB</strong>。支持 CSV、Excel、JSON、SPSS、Stata 格式。</p>
          </div>
          <div class="info-card">
            <h3>🤖 AI 引擎</h3>
            <p>基于大语言模型 + <strong>LangGraph</strong> 工作流编排，自动编写和执行 Python 统计分析代码。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="features-section">
      <h2 class="section-title center">支持的统计方法</h2>
      <div class="features-grid">
        <div v-for="feat in features" :key="feat.title" class="feature-card">
          <div class="feature-icon">{{ feat.icon }}</div>
          <h4>{{ feat.title }}</h4>
          <p>{{ feat.desc }}</p>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="home-footer">
      <p>医学统计 AI 助手 · Powered by AI + LangGraph + FastAPI</p>
    </footer>
  </div>
</template>

<style scoped>
.home-page { min-height: 100vh; }

.hero {
  padding: 80px 24px 60px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background: radial-gradient(ellipse at 50% 0%, rgba(99, 226, 183, 0.08) 0%, transparent 60%);
  pointer-events: none;
}

.hero-content {
  position: relative; z-index: 1;
  max-width: 800px; margin: 0 auto;
  display: flex; flex-direction: column; align-items: center; gap: 20px;
}

.hero-title {
  font-size: 40px;
  font-weight: 800;
  color: #e8edf2;
  white-space: nowrap;
}

.gradient-text {
  background: linear-gradient(135deg, #63e2b7, #4db8e8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle { font-size: 17px; color: #88929d; line-height: 1.7; max-width: 560px; }

.hero-actions { display: flex; gap: 12px; }

.hero-tags {
  display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 8px;
}

/* Usage */
.usage-section { padding: 40px 24px 60px; }

.section-inner {
  max-width: 1200px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: start;
}

.section-title { font-size: 22px; font-weight: 700; color: #e8edf2; margin-bottom: 24px; }
.section-title.center { text-align: center; }

.steps-panel {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px; padding: 32px;
}

.steps-list { display: flex; flex-direction: column; gap: 24px; }

.step-item { display: flex; gap: 16px; align-items: flex-start; }

.step-number {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, #63e2b7, #3db894);
  color: #000; font-weight: 700; font-size: 16px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}

.step-body h4 { font-size: 15px; font-weight: 600; color: #e0e4e9; margin-bottom: 4px; }
.step-body p { font-size: 13px; color: #7d8692; line-height: 1.6; }

.info-panel { display: flex; flex-direction: column; gap: 16px; padding-top: 52px; }

.info-card {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 20px;
}

.info-card h3 { font-size: 15px; font-weight: 600; color: #e0e4e9; margin-bottom: 8px; }
.info-card p { font-size: 13px; color: #7d8692; line-height: 1.6; }

/* Features grid */
.features-section { padding: 40px 24px 80px; max-width: 1200px; margin: 0 auto; }

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.feature-card {
  min-height: 180px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 28px 20px;
  text-align: center;
  transition: border-color 0.2s, transform 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.feature-card:hover { border-color: rgba(99,226,183,0.2); transform: translateY(-2px); }

.feature-icon { font-size: 32px; margin-bottom: 10px; }
.feature-card h4 { font-size: 15px; font-weight: 600; color: #e0e4e9; margin-bottom: 8px; }
.feature-card p { font-size: 13px; color: #7d8692; line-height: 1.5; }

.home-footer {
  padding: 24px; text-align: center;
  border-top: 1px solid rgba(255,255,255,0.05);
}

.home-footer p { font-size: 13px; color: #5c6672; }

@media (max-width: 768px) {
  .hero-title { font-size: 28px; }
  .section-inner { grid-template-columns: 1fr; }
  .features-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
  .hero-title { font-size: 24px; }
  .features-grid { grid-template-columns: 1fr; }
}
</style>
