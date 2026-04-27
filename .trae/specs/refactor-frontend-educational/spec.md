# 前端界面重构规范文档

## Why
当前前端界面虽然功能完整，但视觉设计较为简陋，缺乏统一的设计语言和用户体验优化。为了提升编程教育系统的专业感和用户学习体验，需要对前端进行全面重构，采用教育清新风格，同时保持所有现有功能完全可用。

## What Changes
- **UI设计体系重构**：建立统一的教育清新风格设计系统，包括色彩、字体、间距、圆角等
- **页面布局优化**：重新设计6个核心页面的布局和交互
- **组件化封装**：提取可复用组件（导航、卡片、按钮、表单等）
- **动画与过渡**：添加适度的微动画提升用户体验
- **代码编辑器美化**：优化Monaco编辑器的集成和样式
- **响应式基础**：保持桌面端优先，确保基础响应式支持
- **性能优化**：优化CSS和JS加载，减少渲染阻塞

**BREAKING**: 所有现有API接口保持不变，后端无需修改

## Impact
- Affected specs: 用户认证、学习中心、题库系统、AI对话、个人中心
- Affected code: 
  - `server/static/index.html` - 登录页
  - `server/static/chat.html` - 对话页
  - `server/static/learn.html` - 学习中心
  - `server/static/profile.html` - 个人中心
  - `server/static/questions.html` - 题库大全
  - `server/static/question_detail.html` - 做题页
  - `server/static/edu_ide.css` - 编辑器样式
  - `server/static/edu_ide.js` - 编辑器功能

## ADDED Requirements

### Requirement: 设计系统规范
The system SHALL provide统一的设计系统规范

#### Scenario: 色彩系统
- **WHEN** 用户浏览任意页面
- **THEN** 看到一致的色彩应用：
  - 主色：#4F46E5（靛蓝）- 用于主要按钮、链接、强调
  - 辅助色：#10B981（翠绿）- 用于成功状态、通过标识
  - 警告色：#F59E0B（琥珀）- 用于警告、进行中状态
  - 错误色：#EF4444（红色）- 用于错误、未通过状态
  - 背景色：#F8FAFC（浅灰蓝）- 页面背景
  - 卡片色：#FFFFFF（纯白）- 卡片背景
  - 文字主色：#1E293B（深 slate）- 主要文字
  - 文字辅色：#64748B（中 slate）- 次要文字

#### Scenario: 字体系统
- **WHEN** 用户阅读页面内容
- **THEN** 看到清晰的字体层级：
  - 标题字体：系统默认无衬线字体栈
  - 正文字号：14-16px
  - 小字字号：12-13px
  - 行高：1.5-1.75

#### Scenario: 间距系统
- **WHEN** 用户浏览页面布局
- **THEN** 看到一致的间距：
  - 基础单位：4px
  - 卡片内边距：20-24px
  - 卡片间距：16-20px
  - 页面边距：24-32px
  - 圆角：12-16px（大卡片），8px（小元素）

#### Scenario: 阴影系统
- **WHEN** 用户看到卡片和浮动元素
- **THEN** 看到柔和的阴影效果：
  - 小阴影：0 1px 3px rgba(0,0,0,0.1)
  - 中阴影：0 4px 6px -1px rgba(0,0,0,0.1)
  - 大阴影：0 10px 15px -3px rgba(0,0,0,0.1)

### Requirement: 登录页重构
The system SHALL provide美观的登录/注册页面

#### Scenario: 页面布局
- **WHEN** 用户访问登录页
- **THEN** 看到：
  - 左侧：品牌展示区域，包含系统Logo、名称、功能亮点
  - 右侧：登录/注册表单卡片
  - 整体：居中对齐，最大宽度限制，渐变背景

#### Scenario: 表单设计
- **WHEN** 用户填写登录信息
- **THEN** 看到：
  - 输入框：圆角、聚焦时主色边框、图标前缀
  - 按钮：渐变背景、悬停效果、加载状态
  - 切换：登录/注册标签页切换
  - 提示：清晰的成功/错误状态提示

### Requirement: 导航组件
The system SHALL provide统一的顶部导航栏

#### Scenario: 导航布局
- **WHEN** 用户登录后浏览各页面
- **THEN** 看到固定的顶部导航：
  - 左侧：Logo + 系统名称
  - 中间：主导航链接（学习中心、题库、对话、个人中心）
  - 右侧：用户头像下拉菜单（设置、退出）
  - 当前页面：导航项高亮显示

#### Scenario: 移动端适配
- **WHEN** 用户在较小屏幕上浏览
- **THEN** 导航折叠为汉堡菜单

### Requirement: 学习中心页面重构
The system SHALL provide清晰的学习中心界面

#### Scenario: 课程目录
- **WHEN** 用户查看学习中心
- **THEN** 看到：
  - 左侧：章节树形导航，支持展开/折叠
  - 进度指示：已完成、进行中、未开始状态
  - 当前选中：高亮显示当前学习的小节

#### Scenario: 内容展示
- **WHEN** 用户学习某个知识点
- **THEN** 看到：
  - 顶部：面包屑导航 + 标题
  - 来源标注：清晰的教材来源信息
  - 知识点卡片：分点讲解，代码示例
  - 划词提问：选中文本后弹出询问按钮

#### Scenario: 练习区域
- **WHEN** 用户完成知识点学习
- **THEN** 看到：
  - 题目描述：清晰的题目要求
  - 代码编辑器：深色主题、语法高亮
  - 操作按钮：提交、重置、查看提示
  - 反馈区域：判题结果、得分、详细反馈

### Requirement: 题库页面重构
The system SHALL provide直观的题库浏览界面

#### Scenario: 筛选区域
- **WHEN** 用户浏览题库
- **THEN** 看到：
  - 筛选栏：主题、难度、类型、关键词
  - 统计卡片：总题数、已完成、当前水平
  - 快速操作：生成小测按钮

#### Scenario: 题目列表
- **WHEN** 用户查看题目
- **THEN** 看到：
  - 卡片布局：题目标题、难度标签、完成状态
  - 推荐标识：个性化推荐题目高亮
  - 快捷操作：直接进入做题

#### Scenario: 章节目录
- **WHEN** 用户按章节浏览
- **THEN** 看到：
  - 章节导航：左侧或顶部章节列表
  - 完成进度：每章完成率可视化
  - 题目分组：按知识点分组展示

### Requirement: 做题页面重构
The system SHALL provide专注的做题环境

#### Scenario: 布局设计
- **WHEN** 用户做题
- **THEN** 看到左右分栏：
  - 左侧（40%）：题目描述、示例、提示
  - 右侧（60%）：代码编辑器、操作按钮

#### Scenario: 题目信息
- **WHEN** 用户阅读题目
- **THEN** 看到：
  - 标题栏：题目名称 + 标签
  - 描述区：清晰的题目要求
  - 示例区：输入输出示例
  - 提示区：可展开的提示列表

#### Scenario: 编辑器区域
- **WHEN** 用户编写代码
- **THEN** 看到：
  - 工具栏：重置、恢复上次、查看答案
  - 编辑器：Monaco编辑器，支持Python语法
  - 提交区：提交按钮、状态显示
  - 结果区：判题结果、测试用例详情

### Requirement: AI对话页面重构
The system SHALL provide友好的对话界面

#### Scenario: 布局设计
- **WHEN** 用户与AI对话
- **THEN** 看到：
  - 左侧边栏：历史对话列表
  - 右侧主区：消息展示 + 输入框
  - 顶部：当前对话标题

#### Scenario: 消息展示
- **WHEN** 用户查看对话历史
- **THEN** 看到：
  - 用户消息：右侧气泡，主色背景
  - AI消息：左侧气泡，白色背景
  - 时间戳：消息发送时间
  - 代码块：语法高亮、复制按钮

#### Scenario: 输入区域
- **WHEN** 用户发送消息
- **THEN** 看到：
  - 类型选择：问答、练习、评估、建议
  - 输入框：多行文本、支持快捷键
  - 发送按钮：主色按钮、加载状态

### Requirement: 个人中心页面重构
The system SHALL provide全面的个人数据展示

#### Scenario: 数据概览
- **WHEN** 用户查看个人中心
- **THEN** 看到：
  - 顶部：用户信息卡片（头像、昵称、等级）
  - 统计卡片：完成数、提交数、平均得分等
  - 能力画像：雷达图或条形图展示

#### Scenario: 学习进度
- **WHEN** 用户查看学习进度
- **THEN** 看到：
  - 章节进度：各章节完成率可视化
  - 推荐路径：下一步学习建议
  - 最近活动：最近练习记录

#### Scenario: 资料编辑
- **WHEN** 用户编辑资料
- **THEN** 看到：
  - 表单区域：昵称、头像、简介
  - 学习偏好：目标、方式、节奏
  - 保存按钮：表单验证、成功提示

### Requirement: 组件库封装
The system SHALL provide可复用的CSS组件库

#### Scenario: 按钮组件
- **WHEN** 开发者使用按钮
- **THEN** 提供以下样式类：
  - `.btn` - 基础按钮
  - `.btn-primary` - 主按钮
  - `.btn-secondary` - 次按钮
  - `.btn-ghost` - 幽灵按钮
  - `.btn-sm` / `.btn-lg` - 尺寸变体
  - `.btn-loading` - 加载状态

#### Scenario: 卡片组件
- **WHEN** 开发者使用卡片
- **THEN** 提供以下样式类：
  - `.card` - 基础卡片
  - `.card-hover` - 悬停效果
  - `.card-interactive` - 可点击卡片

#### Scenario: 表单组件
- **WHEN** 开发者使用表单
- **THEN** 提供以下样式类：
  - `.input` - 输入框
  - `.select` - 下拉选择
  - `.textarea` - 文本域
  - `.form-group` - 表单组
  - `.form-error` - 错误状态

#### Scenario: 状态标识
- **WHEN** 开发者展示状态
- **THEN** 提供以下样式类：
  - `.badge` - 基础标签
  - `.badge-success` - 成功
  - `.badge-warning` - 警告
  - `.badge-error` - 错误
  - `.badge-info` - 信息

#### Scenario: 布局工具
- **WHEN** 开发者布局页面
- **THEN** 提供以下样式类：
  - `.container` - 容器
  - `.flex` / `.flex-col` - Flex布局
  - `.grid` - Grid布局
  - `.gap-*` - 间距
  - `.p-*` / `.m-*` - 内边距/外边距

### Requirement: 代码编辑器美化
The system SHALL provide美观的代码编辑体验

#### Scenario: 编辑器主题
- **WHEN** 用户使用代码编辑器
- **THEN** 看到：
  - 深色主题：与VS Code类似的深色背景
  - 语法高亮：Python关键字、字符串、注释等
  - 行号显示：清晰的行号
  - 当前行高亮：当前编辑行高亮

#### Scenario: 编辑器工具栏
- **WHEN** 用户操作编辑器
- **THEN** 看到：
  - 操作按钮：运行、重置、格式化
  - 状态显示：行数、字符数、语言模式
  - 主题切换：可选明暗主题

### Requirement: 动画与过渡
The system SHALL provide适度的动画效果

#### Scenario: 页面过渡
- **WHEN** 用户切换页面或交互
- **THEN** 看到：
  - 卡片悬停：轻微上浮 + 阴影增强
  - 按钮点击：缩放反馈
  - 页面加载：骨架屏或淡入效果
  - 消息发送：滑入动画

#### Scenario: 微交互
- **WHEN** 用户进行细微操作
- **THEN** 看到：
  - 输入框聚焦：边框颜色过渡
  - 切换开关：平滑滑动
  - 加载状态：旋转动画
  - 成功提示：淡入淡出

## MODIFIED Requirements

### Requirement: 现有功能保持
The system SHALL maintain所有现有功能

#### Scenario: API兼容性
- **WHEN** 重构后的前端调用后端API
- **THEN** 所有现有API调用保持不变
- **AND** 请求参数和响应处理不变

#### Scenario: 功能完整性
- **WHEN** 用户使用重构后的界面
- **THEN** 可以完成所有原有操作：
  - 登录/注册
  - 浏览学习中心
  - 完成练习题
  - 与AI对话
  - 浏览题库
  - 做题提交
  - 查看个人数据

## REMOVED Requirements
无移除的功能需求
