import logging
from sqlmodel import SQLModel, Session, create_engine
from app.config import DATABASE_URL

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Create all tables on startup."""
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")


def get_session():
    """Dependency that provides a database session."""
    with Session(engine) as session:
        yield session


def seed_default_prompts():
    """Seed the database with default medical statistics prompt templates."""
    from app.models.prompt import PromptTemplate

    defaults = [
        {
            "name": "描述性统计（基线资料）",
            "category": "descriptive",
            "description": "生成基线资料的描述性统计表，包含均值±标准差、中位数(IQR)、频数(%)等",
            "is_default": True,
            "content": """请对数据集的基线资料进行描述性统计分析：

1. 数值型变量：计算均值±标准差，如不服从正态分布则报告中位数(四分位间距 IQR)
2. 分类变量：计算频数和百分比(%)
3. 按分组变量分别统计（如适用）
4. 生成Table 1论文格式的基线资料表
5. 如有多组间比较，进行组间均衡性检验（t检验/方差分析/卡方检验）
6. 输出结果需包含统计量和P值

请以论文发表的格式输出结果，包含规范的统计描述。""",
        },
        {
            "name": "t检验 / Mann-Whitney U检验",
            "category": "comparison",
            "description": "两组间比较：正态分布用t检验，非正态用Mann-Whitney U检验",
            "is_default": True,
            "content": """请对数据进行两组间差异比较分析：

1. 首先检验数据是否服从正态分布（Shapiro-Wilk检验）
2. 如服从正态分布且方差齐：使用独立样本t检验
3. 不服从正态分布：使用Mann-Whitney U检验
4. 报告格式：统计量(t/U值)、自由度(df)、P值
5. 如P<0.05，标注统计学显著性
6. 生成箱线图或小提琴图展示组间差异
7. 输出论文格式的结果描述（中文），包含：
   - 两组均值/中位数及变异指标
   - 检验统计量及P值
   - 统计结论""",
        },
        {
            "name": "单因素方差分析 (ANOVA)",
            "category": "comparison",
            "description": "三组及以上比较：正态分布用ANOVA，非正态用Kruskal-Wallis检验",
            "is_default": True,
            "content": """请进行单因素方差分析：

1. 检验正态性和方差齐性假设
2. 满足假设：使用单因素ANOVA，报告F值、组间/组内自由度、P值
3. 不满足假设：使用Kruskal-Wallis H检验
4. 如总体差异显著(P<0.05)，进行事后多重比较：
   - 方差齐：Tukey HSD或Bonferroni校正
   - 方差不齐：Games-Howell检验
5. 生成均值±标准误(SE)的柱状图或箱线图
6. 图表标注显著性字母标记（如a, b, c）
7. 输出论文格式的结果描述""",
        },
        {
            "name": "卡方检验 / Fisher精确检验",
            "category": "categorical",
            "description": "分类变量的关联性分析：卡方检验/Fisher精确检验",
            "is_default": True,
            "content": """请进行分类变量的关联性分析：

1. 生成列联表（交叉表），包含行百分比和列百分比
2. 如所有期望频数≥5：使用Pearson卡方检验
3. 如有期望频数<5：使用Fisher精确检验
4. 报告卡方值(χ²)、自由度(df)、P值
5. 计算效应量：Cramer's V 或 φ系数
6. 如需分层分析：进行Cochran-Mantel-Haenszel检验
7. 生成堆叠柱状图或马赛克图
8. 输出论文格式的结果描述""",
        },
        {
            "name": "线性回归分析",
            "category": "regression",
            "description": "单因素和多因素线性回归分析",
            "is_default": True,
            "content": """请进行线性回归分析：

1. 先进行单因素线性回归分析，筛选P<0.1的变量
2. 将单因素分析中有意义的变量纳入多因素线性回归模型
3. 报告回归系数(β)、标准误(SE)、标准化回归系数(β_std)、t值、P值
4. 报告模型的R²和调整R²
5. 检验模型假设：残差正态性、方差齐性、共线性(VIF)
6. 生成残差诊断图（残差vs拟合值、Q-Q图）
7. 生成森林图展示各变量回归系数及95%CI
8. 输出论文格式的三线表结果""",
        },
        {
            "name": "Logistic回归分析",
            "category": "regression",
            "description": "二分类/多分类结局的Logistic回归",
            "is_default": True,
            "content": """请进行Logistic回归分析（二分类结局变量）：

1. 定义结局变量（二分类）和各预测变量
2. 先做单因素Logistic回归，筛选P<0.1的变量
3. 多因素Logistic回归（输入法/逐步回归）
4. 报告OR值、95%置信区间、Wald χ²值、P值
5. 报告模型拟合优度：Hosmer-Lemeshow检验、AUC值
6. 生成ROC曲线图，标注AUC及95%CI
7. 生成列线图(Nomogram)（如适用）
8. 输出论文格式的三线表结果""",
        },
        {
            "name": "生存分析 (Kaplan-Meier + Cox回归)",
            "category": "survival",
            "description": "Kaplan-Meier生存曲线 + Log-rank检验 + Cox比例风险回归",
            "is_default": True,
            "content": """请进行生存分析：

1. 确认数据包含：生存时间变量和结局事件变量(0=删失,1=事件)
2. 估计中位生存时间及95%CI
3. 计算各时间点(1年/3年/5年)的生存率
4. 按分组变量绘制Kaplan-Meier生存曲线
5. Log-rank检验比较组间生存差异
6. Cox比例风险回归：
   - 单因素分析 → 多因素分析
   - 报告HR值、95%CI、P值
7. 检验比例风险假设(Schoenfeld残差检验)
8. 如违反比例风险假设，考虑分层Cox或时变Cox
9. 输出论文格式的结果描述和图表""",
        },
        {
            "name": "相关性分析",
            "category": "correlation",
            "description": "Pearson/Spearman相关 + 相关性热力图",
            "is_default": True,
            "content": """请进行相关性分析：

1. 检验各变量正态性，决定使用Pearson或Spearman相关系数
2. 计算各变量间的相关系数矩阵
3. 报告相关系数r值、P值和95%CI
4. 生成相关性热力图(heatmap)，标注显著性星号
5. 生成散点图矩阵或配对散点图
6. 对于重点变量对，进行偏相关分析（控制协变量）
7. 输出论文格式的结果描述""",
        },
        {
            "name": "ROC曲线与诊断试验评价",
            "category": "diagnosis",
            "description": "ROC曲线绘制、AUC计算、最佳截断值确定",
            "is_default": True,
            "content": """请进行诊断试验评价分析：

1. 以金标准诊断结果为参考，绘制ROC曲线
2. 计算AUC值及95%置信区间
3. 使用Youden指数确定最佳截断值
4. 计算敏感度(Sensitivity)、特异度(Specificity)
5. 计算阳性预测值(PPV)、阴性预测值(NPV)
6. 如有多项诊断指标，比较各指标的AUC(DeLong检验)
7. 输出论文格式的结果描述""",
        },
        {
            "name": "数据清洗与预处理",
            "category": "cleaning",
            "description": "缺失值处理、异常值检测、数据类型转换",
            "is_default": True,
            "content": """请对数据进行清洗和预处理：

1. 检测并报告各变量的缺失值数量和比例
2. 对数值型变量的缺失值：根据数据特征选择均值/中位数/多重插补
3. 对分类变量的缺失值：使用众数填充或创建"缺失"类别
4. 检测异常值（IQR法或Z-score法），标记或处理
5. 检查并报告重复行
6. 检查数据类型是否合理，进行必要的转换
7. 生成数据质量报告，包含清洗前后的对比
8. 输出论文格式的清洗描述""",
        },
    ]

    with Session(engine) as session:
        from sqlmodel import select

        existing = session.exec(select(PromptTemplate)).all()
        if len(existing) == 0:
            for tpl in defaults:
                prompt = PromptTemplate(**tpl)
                session.add(prompt)
            session.commit()
            logger.info(f"Seeded {len(defaults)} default prompt templates")
        else:
            logger.info(f"Database already has {len(existing)} prompt templates, skipping seed")
