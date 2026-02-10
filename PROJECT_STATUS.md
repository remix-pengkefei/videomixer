# VideoMixer 项目进度

## 最后更新: 2025-02-04 21:30

## 项目位置
`/Users/fly/Desktop/VideoMixer`

---

## 已完成功能

### 1. 素材库 (2270个素材)
- 贴纸: 1766个 (`assets/stickers/`)
- 标题框: 182个 (`assets/titles/`)
- 边框: 145个 (`assets/frames/`)
- 动画GIF: 177个 (`assets/animated/`)

### 2. 智能混剪Skill
文件: `src/smart_remix.py`

### 3. 视频分类权重系统
- 支持: 音乐/Vlog/教程/剧情/美食/旅行等类型

---

## 新增：高级混剪能力模块 (2025-02-03)

### 已实现的新模块

| 模块文件 | 能力类型 | 具体功能 |
|---------|---------|----------|
| `src/subtitle_effects.py` | 字幕效果 | 8种字幕样式 |
| `src/background_effects.py` | 背景效果 | 6种背景特效 |
| `src/particle_effects.py` | 粒子特效 | 8种粒子效果 |
| `src/ui_templates.py` | UI模板 | 5种UI叠加 |
| `src/layout_engine.py` | 布局引擎 | 7种视频布局 |
| `src/title_effects.py` | 标题效果 | 9种标题样式 |
| `src/advanced_remix.py` | 高级混剪器 | 统一处理入口 |
| `src/video_analyzer.py` | **智能分析** | 自动视频类型检测 |

---

## 新增：智能视频分析模块 (2025-02-04)

### 自动视频类型检测

系统现在支持**自动分析视频内容**并智能选择最佳混剪策略，无需手动指定视频类型。

#### 分析维度

| 维度 | 分析内容 | 检测方法 |
|------|---------|---------|
| 人脸分析 | 人脸检测、位置、大小、稳定性 | OpenCV级联分类器 |
| 音频分析 | 人声、音乐、静音比例 | FFmpeg音频检测 |
| 视觉分析 | 场景切换、运动强度、画面特征 | FFmpeg/OpenCV |

#### 支持识别的内容类型

| 类型 | 说明 | 映射策略 |
|------|------|---------|
| digital_human | 数字人（AI生成） | 简洁字幕+角标 |
| real_person | 真人说话 | 与数字人相似 |
| handwriting | 手写/打字文字 | 丰富装饰+打字机 |
| music_visual | 音乐可视化/MV | 音乐播放器UI |
| gaming | 游戏录屏 | REC标识+活泼装饰 |
| emotional | 情感/抒情 | 水波纹+粒子效果 |
| slideshow | 图片轮播 | 情感风格 |
| general | 通用 | 基础效果 |

#### 使用方法

```bash
# 命令行 - 自动检测（推荐）
python -m src.advanced_remix video.mp4 --auto
python -m src.advanced_remix video.mp4 --auto --title "我的标题"

# 不指定类型也会自动检测
python -m src.advanced_remix video.mp4
```

```python
# Python代码 - 自动混剪（推荐）
from src.advanced_remix import auto_remix

# 最简单用法 - 系统自动分析并选择策略
result = auto_remix("video.mp4")

# 添加标题
result = auto_remix("video.mp4", title_text="我的标题")

# 春节主题
result = auto_remix("video.mp4", festival="spring_festival")
```

```python
# 单独使用视频分析器
from src.video_analyzer import analyze_video, get_video_type

# 分析视频内容
result = analyze_video("video.mp4")
print(f"类型: {result.content_type.value}")
print(f"置信度: {result.confidence*100:.1f}%")
print(f"推荐策略: {result.recommended_strategy}")

# 快速获取类型
content_type, confidence = get_video_type("video.mp4")
```

---

## 混剪能力清单

### 字幕效果 (8种) ✅ 已实现
| 编号 | 能力 | 状态 |
|------|------|------|
| S1 | 底部横排字幕 | ✅ |
| S2 | 描边字幕 | ✅ |
| S3 | 便签纸字幕 | ✅ |
| S4 | 竖排字幕 | ✅ |
| S5 | 双色高亮字幕 | ✅ |
| S6 | 打字机效果 | ✅ |
| S7 | 歌词同步字幕 | ✅ |
| S8 | 阴影字幕 | ✅ |

### 背景效果 (6种) ✅ 已实现
| 编号 | 能力 | 状态 |
|------|------|------|
| B1 | 动态背景切换 | ✅ |
| B2 | 水波纹特效 | ✅ |
| B3 | 墨迹流动 | ✅ |
| B4 | 模糊边框 | ✅ |
| B5 | 科幻背景替换 | ✅ |
| B6 | 渐变天空 | ✅ |

### 粒子特效 (8种) ✅ 已实现
| 编号 | 能力 | 状态 |
|------|------|------|
| P1 | 闪光星星 | ✅ |
| P2 | 雪花飘落 | ✅ |
| P3 | 樱花飘落 | ✅ |
| P4 | 烟花绽放 | ✅ |
| P5 | 气泡上升 | ✅ |
| P6 | 心形漂浮 | ✅ |
| P7 | 星星闪烁 | ✅ |
| P8 | 灰尘光点 | ✅ |

### UI模板 (5种) ✅ 已实现
| 编号 | 能力 | 状态 |
|------|------|------|
| U1 | 音乐播放器UI | ✅ |
| U2 | 关注引导UI | ✅ |
| U3 | 进度条 | ✅ |
| U4 | REC录制标识 | ✅ |
| U5 | 水印 | ✅ |

### 布局引擎 (7种) ✅ 已实现
| 编号 | 能力 | 状态 |
|------|------|------|
| L1 | 画中画(PIP) | ✅ |
| L2 | 上下分割 | ✅ |
| L3 | 左右分割 | ✅ |
| L4 | 2x2网格 | ✅ |
| L5 | 3x3网格 | ✅ |
| L6 | 边框装饰 | ✅ |
| L7 | 中心浮动(背景模糊) | ✅ |

### 标题效果 (9种) ✅ 已实现
| 编号 | 能力 | 状态 |
|------|------|------|
| T1 | 简单标题 | ✅ |
| T2 | 3D立体标题 | ✅ |
| T3 | 霓虹灯标题 | ✅ |
| T4 | 发光描边标题 | ✅ |
| T5 | 阴影深度标题 | ✅ |
| T6 | 书名号标题《》 | ✅ |
| T7 | 金属质感标题 | ✅ |
| T8 | 手写风格标题 | ✅ |
| T9 | 渐变标题 | ✅ |

---

## 混剪策略 (5种) ✅ 已实现

| 策略 | 适用类型 | 配置函数 |
|------|---------|---------|
| 数字人策略 | 数字人视频 | `remix_digital_human()` |
| 手写策略 | 手写文字视频 | `remix_handwriting()` |
| 音乐播放器策略 | 音乐视频 | `remix_music_player()` |
| 游戏录屏策略 | 游戏视频 | 通过 `get_strategy_for_type()` |
| 情感类策略 | 情感视频 | `remix_emotional()` |

---

## 能力统计

| 类别 | 原有 | 新增 | 总计 |
|------|------|------|------|
| 字幕效果 | 3 | 5 | 8 |
| 背景效果 | 0 | 6 | 6 |
| 粒子特效 | 2 | 6 | 8 |
| UI模板 | 0 | 5 | 5 |
| 布局引擎 | 0 | 7 | 7 |
| 标题效果 | 2 | 7 | 9 |
| 策略模板 | 1 | 4 | 5 |
| **智能分析** | **0** | **8** | **8** |
| **总计** | **8** | **48** | **56** |

### 智能分析能力 (8种)
| 编号 | 能力 | 状态 |
|------|------|------|
| A1 | 人脸检测 | ✅ |
| A2 | 人脸位置/大小分析 | ✅ |
| A3 | 人脸稳定性检测（数字人特征） | ✅ |
| A4 | 音频音乐/人声检测 | ✅ |
| A5 | 场景切换率分析 | ✅ |
| A6 | 运动强度分析 | ✅ |
| A7 | 视频类型评分算法 | ✅ |
| A8 | 策略自动映射 | ✅ |

---

## 使用方法

### 命令行使用

```bash
cd /Users/fly/Desktop/VideoMixer

# ========== 推荐：自动检测模式 ==========
# 系统自动分析视频内容并选择最佳策略
python -m src.advanced_remix video.mp4 --auto
python -m src.advanced_remix video.mp4 --auto --title "我的标题"
python -m src.advanced_remix video.mp4  # 不指定参数也会自动检测

# ========== 手动指定模式 ==========
# 数字人视频混剪
python -m src.advanced_remix video.mp4 --type digital_human

# 手写文字视频混剪（带标题）
python -m src.advanced_remix video.mp4 --type handwriting --title "翻身号角"

# 音乐播放器风格混剪
python -m src.advanced_remix video.mp4 --type music_player --title "前程似锦"

# 情感类视频混剪（春节主题）
python -m src.advanced_remix video.mp4 --type emotional --festival spring_festival

# 指定输出路径
python -m src.advanced_remix video.mp4 --type digital_human --output output.mp4
```

### Python代码使用

```python
# ========== 推荐：自动混剪 ==========
from src.advanced_remix import auto_remix

# 最简单用法 - 系统自动分析并选择最佳策略
result = auto_remix("video.mp4")

# 添加标题和字幕
result = auto_remix("video.mp4", title_text="我的标题", subtitle_text="字幕内容")

# 节日主题
result = auto_remix("video.mp4", festival="spring_festival")

# ========== 视频分析 ==========
from src.video_analyzer import analyze_video, get_video_type

# 分析视频内容
analysis = analyze_video("video.mp4")
print(f"类型: {analysis.content_type.value}")
print(f"置信度: {analysis.confidence*100:.1f}%")
print(f"推荐策略: {analysis.recommended_strategy}")
print(f"原因: {analysis.strategy_reason}")

# ========== 指定类型混剪 ==========
from src.advanced_remix import (
    advanced_remix, AdvancedRemixConfig,
    remix_digital_human, remix_handwriting,
    remix_music_player, remix_emotional,
    get_strategy_for_type, VideoType
)

# 快捷函数
result = remix_digital_human("video.mp4", subtitle_text="测试字幕")
result = remix_music_player("video.mp4", song_title="前程似锦")
result = remix_emotional("video.mp4", title_text="感动时刻", festival="spring_festival")

# 自定义配置
config = get_strategy_for_type(VideoType.HANDWRITING, "spring_festival")
config.title_config.text = "我的标题"
config.particle_enabled = True
result = advanced_remix("video.mp4", config=config)
```

---

## 文档列表

| 文档 | 路径 | 描述 |
|------|------|------|
| 项目状态 | `PROJECT_STATUS.md` | 当前文档 |
| 混剪能力清单 | `docs/REMIX_CAPABILITIES.md` | 能力详细说明 |
| 混剪策略指南 | `docs/REMIX_STRATEGIES.md` | 策略配置指南 |
| 超强混剪指南 | `docs/ENHANCED_REMIX_GUIDE.md` | 过审级混剪指南 |
| 去重技术知识库 | `docs/VIDEO_DEDUP_KNOWLEDGE.md` | 网络学习的去重知识 |

---

## 核心文件

### 原有模块
- `src/smart_remix.py` - 智能混剪主程序
- `src/video_classifier_v2.py` - 视频分类器
- `src/video_effects.py` - 视频特效
- `src/overlay_effects.py` - 叠加特效

### 新增模块 (2025-02-03)
- `src/subtitle_effects.py` - 高级字幕效果
- `src/background_effects.py` - 高级背景效果
- `src/particle_effects.py` - 粒子特效系统
- `src/ui_templates.py` - UI模板系统
- `src/layout_engine.py` - 布局引擎
- `src/title_effects.py` - 标题效果系统
- `src/advanced_remix.py` - 高级混剪处理器

### 新增模块 (2025-02-04)
- `src/video_analyzer.py` - 智能视频分析器（自动类型检测）
- `src/enhanced_handwriting.py` - 手写类视频超强混剪
- `src/enhanced_emotional.py` - 情感类视频超强混剪
- `src/enhanced_health.py` - 养生类视频超强混剪
- `src/video_dedup.py` - 视频去重模块（11项去重技术）
- `src/super_remix.py` - 超级混剪（视觉+去重一体化）

---

---

## 超强混剪模块 (2025-02-04 21:10)

### 三种视频风格处理器

| 模块 | 适用类型 | 配色风格 |
|------|---------|---------|
| `enhanced_handwriting.py` | 手写/文案 | 深蓝黑 + 彩虹色 |
| `enhanced_emotional.py` | 情感/励志 | 深蓝黑 + 粉紫暖色 |
| `enhanced_health.py` | 养生/健康 | 深绿 + 绿橙棕自然色 |

### 过审级效果清单

| 效果 | 参数 |
|------|------|
| 贴纸 | 20个 (来自19000素材库) |
| 顶部遮罩 | 220px + 4层渐变 |
| 底部遮罩 | 240px + 4层渐变 |
| 左右边框 | 双层彩色 (25px+8px) |
| 侧边色块 | 左右各6条 |
| 中间色块 | 4条横向装饰 |
| 角落装饰 | 8个彩色方块 |
| 横线装饰 | 顶部3条 + 底部3条 |
| 闪烁粒子 | 50个 |
| 边缘光晕 | 左右柔和光效 |
| 调色 | 亮度/对比度/饱和度微调 |

### 使用方法

```bash
# 手写类
python -m src.enhanced_handwriting video.mp4 output.mp4

# 情感类
python -m src.enhanced_emotional video.mp4 output.mp4

# 养生类
python -m src.enhanced_health video.mp4 output.mp4
```

### 推荐贴纸素材文件夹

- `19000 免抠贴纸素材/105 中式传统图案/`
- `19000 免抠贴纸素材/611 花花草草/`
- `19000 免抠贴纸素材/200 可爱装饰/`
- `19000 免抠贴纸素材/100 蕾丝花边/`
- `19000 免抠贴纸素材/38 花/`

---

---

## 去重功能 (2025-02-04 21:30 已完成)

### 高优先级 ✅ 已完成
| 功能 | 说明 | 状态 |
|------|------|------|
| 画中画透明叠加 | 自动添加1-4%透明度噪点 | ✅ 已完成 |
| 智能抽帧 | 每10-15帧删除1帧，破坏抽帧检测 | ✅ 已完成 |
| 变速组合 | 先减速→抽帧→再加速 | ✅ 已完成 |
| 动态水印 | 跑马灯效果，位置随时间变化 | ✅ 已完成 |

### 中优先级 ✅ 已完成
| 功能 | 说明 | 状态 |
|------|------|------|
| 自动掐头去尾 | 删除前后0.5-2秒 | ✅ 已完成 |
| 镜像翻转 | 可选左右翻转 | ✅ 已完成 |
| 随机微旋转 | 1-2度随机旋转 | ✅ 已完成 |
| 分辨率微调 | 缩小后放大，改变像素 | ✅ 已完成 |

### 低优先级 ✅ 已完成
| 功能 | 说明 | 状态 |
|------|------|------|
| 帧率自动调整 | 随机调整28-32fps | ✅ 已完成 |
| 调色处理 | 亮度/对比度/饱和度微调 | ✅ 已完成 |

### 新增模块
- `src/video_dedup.py` - 视频去重模块 (11项去重技术)
- `src/super_remix.py` - 超级混剪 (视觉效果+去重一体化)

---

## 去重知识要点

### 平台查重原理
1. MD5校验（已过时，改任何内容都会变）
2. 元数据检测（标题、描述、封面、时长）
3. **抽帧对比**（片头+片尾+中间若干帧）
4. 图像相似度（>65%判定重复）
5. 音频指纹

### 高效去重方法
1. ⭐⭐⭐⭐⭐ 画中画透明叠加 (1-4%)
2. ⭐⭐⭐⭐⭐ 大面积遮罩 (200px+)
3. ⭐⭐⭐⭐⭐ 大量贴纸 (15-20个)
4. ⭐⭐⭐⭐⭐ 抽帧处理
5. ⭐⭐⭐⭐ 变速 (0.9x-1.1x)

### 需修改30%以上内容才能过审

---

---

## 新增功能模块 (2025-02-04 22:00 已完成)

### 转场效果 ✅ 已完成
文件: `src/transitions.py`

| 功能 | FFmpeg滤镜 | 状态 |
|------|-----------|------|
| 淡入淡出 | xfade=fade | ✅ 已完成 |
| 白场闪烁 | xfade=fadewhite | ✅ 已完成 |
| 黑场过渡 | xfade=fadeblack | ✅ 已完成 |
| 擦除转场 | xfade=wipeleft/right/up/down | ✅ 已完成 |
| 滑动转场 | xfade=slideleft/right/up/down | ✅ 已完成 |
| 圆形裁切 | xfade=circlecrop | ✅ 已完成 |
| 溶解效果 | xfade=dissolve | ✅ 已完成 |
| 像素化 | xfade=pixelize | ✅ 已完成 |
| 径向转场 | xfade=radial | ✅ 已完成 |
| 闪白/闪黑效果 | drawbox enable | ✅ 已完成 |
| 多视频转场拼接 | concat_with_transitions | ✅ 已完成 |

### 分屏效果 ✅ 已完成
文件: `src/split_screen.py`

| 功能 | 说明 | 状态 |
|------|------|------|
| 左右分屏 | hstack 两视频 | ✅ 已完成 |
| 上下分屏 | vstack 两视频 | ✅ 已完成 |
| 2x2网格 | 四视频网格 | ✅ 已完成 |
| 3x3网格 | 九视频网格 | ✅ 已完成 |
| 三分屏(横向) | 三视频水平 | ✅ 已完成 |
| 三分屏(纵向) | 三视频垂直 | ✅ 已完成 |
| 画中画-右上 | PIP overlay | ✅ 已完成 |
| 画中画-左上 | PIP overlay | ✅ 已完成 |
| 画中画-右下 | PIP overlay | ✅ 已完成 |
| 画中画-左下 | PIP overlay | ✅ 已完成 |

### 背景虚化填充 ✅ 已完成
文件: `src/background_blur.py`

| 功能 | 说明 | 状态 |
|------|------|------|
| 基础模糊背景 | 自动画幅转换 | ✅ 已完成 |
| 渐变模糊背景 | 带上下渐变暗角 | ✅ 已完成 |
| 彩色模糊背景 | 带色调偏移 | ✅ 已完成 |
| 镜像模糊背景 | 左右镜像填充 | ✅ 已完成 |
| 横转竖 | 16:9 → 9:16 | ✅ 已完成 |
| 竖转横 | 9:16 → 16:9 | ✅ 已完成 |
| 方转竖 | 1:1 → 9:16 | ✅ 已完成 |

### 文字动画效果 ✅ 已完成
文件: `src/text_effects.py`

| 功能 | 说明 | 状态 |
|------|------|------|
| 静态文字 | 带描边阴影 | ✅ 已完成 |
| 打字机效果 | 逐字显示 | ✅ 已完成 |
| 滚动字幕 | 左/右/上/下滚动 | ✅ 已完成 |
| 跑马灯 | 循环滚动 | ✅ 已完成 |
| 弹跳文字 | 正弦波弹跳 | ✅ 已完成 |
| 淡入淡出 | alpha渐变 | ✅ 已完成 |
| 字幕序列 | 多条字幕时间轴 | ✅ 已完成 |
| 卡拉OK效果 | 逐字高亮 | ✅ 已完成 |

### 综合效果处理器 ✅ 已完成
文件: `src/all_effects.py`

| 功能 | 说明 | 状态 |
|------|------|------|
| 效果整合 | 统一接口 | ✅ 已完成 |
| 批量处理 | 多视频处理 | ✅ 已完成 |
| 预设配置 | light/medium/strong/extreme | ✅ 已完成 |
| 快速处理 | quick_process() | ✅ 已完成 |

---

## 使用新功能

### 转场效果
```python
from src.transitions import TransitionType, add_transition, concat_with_transitions

# 两视频添加转场
add_transition("v1.mp4", "v2.mp4", "out.mp4", TransitionType.FADE, duration=1.0)

# 多视频拼接带转场
concat_with_transitions(["v1.mp4", "v2.mp4", "v3.mp4"], "out.mp4", duration=0.5)

# 添加闪白效果
add_flash_effect("input.mp4", "out.mp4", flash_times=[2.0, 5.0, 8.0], flash_type="white")
```

### 分屏效果
```python
from src.split_screen import create_horizontal_split, create_grid_2x2, create_pip

# 左右分屏
create_horizontal_split("left.mp4", "right.mp4", "out.mp4")

# 2x2网格
create_grid_2x2(["v1.mp4", "v2.mp4", "v3.mp4", "v4.mp4"], "out.mp4")

# 画中画
create_pip("main.mp4", "small.mp4", "out.mp4", position="top_right", pip_scale=0.3)
```

### 背景虚化
```python
from src.background_blur import create_blur_background, create_gradient_blur_background

# 横屏转竖屏（带模糊背景）
create_blur_background("横屏.mp4", "竖屏.mp4", target_width=720, target_height=1280)

# 带渐变的模糊背景
create_gradient_blur_background("input.mp4", "out.mp4", blur_strength=25)
```

### 文字动画
```python
from src.text_effects import add_typewriter_text, add_scroll_text, add_fade_text

# 打字机效果
add_typewriter_text("input.mp4", "out.mp4", "Hello World", x=100, y=100)

# 跑马灯
add_scroll_text("input.mp4", "out.mp4", "滚动文字", direction="left", speed=100)

# 淡入淡出文字
add_fade_text("input.mp4", "out.mp4", "标题", start_time=1.0, fade_duration=1.0)
```

---

## 能力统计更新

| 类别 | 数量 | 新增 |
|------|------|------|
| 字幕效果 | 8 | - |
| 背景效果 | 6 | - |
| 粒子特效 | 8 | - |
| UI模板 | 5 | - |
| 布局引擎 | 7 | - |
| 标题效果 | 9 | - |
| 策略模板 | 5 | - |
| 智能分析 | 8 | - |
| 去重技术 | 11 | - |
| **转场效果** | **20+** | ✅ |
| **分屏效果** | **10** | ✅ |
| **背景虚化** | **7** | ✅ |
| **文字动画** | **8** | ✅ |
| **总计** | **112+** | |

---

## 新增模块清单 (2025-02-04)

| 模块文件 | 功能 | 状态 |
|---------|------|------|
| `src/transitions.py` | 20+种转场效果 | ✅ 已完成 |
| `src/split_screen.py` | 10种分屏效果 | ✅ 已完成 |
| `src/background_blur.py` | 7种背景虚化 | ✅ 已完成 |
| `src/text_effects.py` | 8种文字动画 | ✅ 已完成 |
| `src/all_effects.py` | 综合效果处理器 | ✅ 已完成 |
| `src/video_dedup.py` | 11项去重技术 | ✅ 已完成 |
| `src/super_remix.py` | 超级混剪器 | ✅ 已完成 |
| `src/enhanced_handwriting.py` | 手写类超强处理 | ✅ 已完成 |
| `src/enhanced_emotional.py` | 情感类超强处理 | ✅ 已完成 |
| `src/enhanced_health.py` | 养生类超强处理 | ✅ 已完成 |

---

---

## 视频类型混剪策略 (2025-02-04 全网学习)

### 新增模块
文件: `src/editing_strategy.py`

### 支持的视频类型 (12种)

| 类型 | 名称 | 节奏 | 贴纸 | 遮罩 | 特点 |
|------|------|------|------|------|------|
| digital_human | 数字人/口播 | 舒缓 | 8 | 120px | 简洁专业 |
| handwriting | 手写/文案 | 中等 | 20 | 220px | 丰富装饰 |
| emotional | 情感/励志 | 变速 | 15 | 200px | 情绪导向 |
| knowledge | 知识/教程 | 中等 | 6 | 100px | 清晰专业 |
| music | 音乐/MV | 极快 | 10 | 150px | 节拍主导 |
| gaming | 游戏/直播 | 快速 | 12 | 100px | 活泼动感 |
| food | 美食/ASMR | 舒缓 | 5 | 80px | 沉浸体验 |
| travel | 旅行/Vlog | 中等 | 8 | 100px | 电影感 |
| fitness | 健身/运动 | 快速 | 8 | 120px | 高能量 |
| product | 产品/电商 | 中等 | 5 | 80px | 展示转化 |
| health | 养生/健康 | 舒缓 | 12 | 180px | 舒缓自然 |
| general | 通用 | 中等 | 15 | 180px | 适用多数 |

### 节奏类型对照表

| 节奏 | 切片长度 | 每分钟切换 | 适用场景 |
|------|---------|-----------|---------|
| 极快 | 0.5-1秒 | 60次 | 音乐、预告 |
| 快速 | 1-2秒 | 30次 | 游戏、运动 |
| 中等 | 3-5秒 | 15次 | Vlog、教程 |
| 舒缓 | 5-10秒 | 8次 | 情感、ASMR |
| 变速 | 2-8秒 | 12次 | 剧情、创意 |

### 转场类型推荐

| 视频类型 | 推荐转场 |
|---------|---------|
| 数字人 | fade |
| 手写 | wipe, dissolve |
| 情感 | fadeblack, fadewhite, circlecrop |
| 音乐 | flash, pixelize, radial |
| 游戏 | zoom, pixelize |
| 美食 | fade, dissolve |
| 旅行 | dissolve |
| 健身 | flash |

### 使用方法

```python
from src.editing_strategy import (
    VideoType, get_strategy, describe_strategy,
    adjust_strategy_intensity, EffectIntensity
)

# 获取策略
strategy = get_strategy(VideoType.HANDWRITING)
print(describe_strategy(strategy))

# 调整强度
strong_strategy = adjust_strategy_intensity(strategy, EffectIntensity.STRONG)
```

---

## 知识库文档

| 文档 | 路径 | 内容 |
|------|------|------|
| 视频去重知识库 | `docs/VIDEO_DEDUP_KNOWLEDGE.md` | 平台检测原理、去重技术 |
| **混剪策略知识库** | `docs/VIDEO_TYPE_EDITING_STRATEGIES.md` | 12种视频类型的混剪策略 |
| 超强混剪指南 | `docs/ENHANCED_REMIX_GUIDE.md` | 过审级效果配置 |

---

*文档版本: 9.0*
*更新时间: 2025-02-04 22:30*
