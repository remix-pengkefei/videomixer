# 视频去重技术知识库

## 更新时间: 2025-02-04

## 来源
- [TaoKeShow - 12种去重技巧](https://www.taokeshow.com/56301.html)
- [CSDN - 视频去重深度解析](https://blog.csdn.net/asd12583/article/details/124387185)
- [高羽网创 - 短剧去重十二步法则](https://www.gaoyuip.com/33528.html)
- [腾讯云 - 20种去重方法](https://cloud.tencent.com/developer/news/1173301)
- [知乎 - FFmpeg overlay滤镜](https://zhuanlan.zhihu.com/p/612910045)
- [FFmpeg官方文档](https://ffmpeg.org/ffmpeg-filters.html)

---

## 一、平台查重原理

### 1.1 检测流程
1. **MD5校验** - 最快速的初筛（但改动任何内容MD5都会变）
2. **元数据检测** - 标题、描述、标签、封面、时长、分辨率、BGM
3. **抽帧对比** - 片头几秒 + 片尾几秒 + 中间若干帧
4. **图像相似度** - 对比抽取的帧画面相似度
5. **音频指纹** - 检测背景音乐和音频特征

### 1.2 判定标准
- 相似度高于 **65%** 会被判定为重复
- 需要修改至少 **30%** 的内容才能通过审核

---

## 二、去重技术分类

### 2.1 画面调整类

| 技术 | 说明 | FFmpeg实现 |
|------|------|-----------|
| 镜像翻转 | 左右翻转画面 | `hflip` |
| 旋转 | 旋转一定角度 | `rotate=angle*PI/180` |
| 缩放 | 改变分辨率 | `scale=w:h` |
| 裁剪 | 去除边缘 | `crop=w:h:x:y` |
| 调色 | 亮度/对比度/饱和度 | `eq=brightness=0.1:contrast=1.1:saturation=1.2` |
| 滤镜 | 色调变化 | `colorbalance`, `hue` |

### 2.2 时间调整类

| 技术 | 说明 | 推荐参数 |
|------|------|---------|
| 变速 | 加速或减速 | 0.8x - 1.2x |
| 抽帧 | 删除部分帧 | 每10-15帧删1帧 |
| 改帧率 | 修改FPS | 25-60fps |
| 掐头去尾 | 删除片头片尾 | 删除3-5秒 |

### 2.3 叠加类

| 技术 | 说明 | 重要程度 |
|------|------|---------|
| 水印 | 添加logo | ⭐⭐⭐ |
| 贴纸 | 装饰元素 | ⭐⭐⭐⭐⭐ |
| 字幕 | 文字叠加 | ⭐⭐⭐⭐ |
| 画中画 | 透明叠加层 | ⭐⭐⭐⭐⭐ |
| 边框 | 装饰边框 | ⭐⭐⭐⭐ |
| 遮罩 | 顶底遮挡 | ⭐⭐⭐⭐⭐ |

### 2.4 音频类

| 技术 | 说明 |
|------|------|
| 换BGM | 更换背景音乐 |
| 变调 | 调整音调 |
| 变速 | 音频加速减速 |
| 配音 | 添加解说 |
| 音效 | 添加音效 |

---

## 三、关键技术详解

### 3.1 抽帧技术
```
原理：把视频拉到最大，每隔10-15帧分割一次，删去1帧
效果：改变关键帧，破坏抽帧检测
注意：抽帧越细致越好，至少抽20-30帧
```

### 3.2 画中画技术（重要！）
```
方法1：导入自己拍的图片/纯色视频
       - 布满整个视频画面
       - 混合模式选择"叠加"
       - 不透明度调到 1-4%

方法2：导入自己拍的实拍视频（天空、花草）
       - 不透明度调到 1-2%
       - 肉眼看不到，但平台会识别到画面有重叠
```

### 3.3 动态遮罩/蒙版
```
- 随机动态蒙版
- 随机动态缩放
- 蒙版倒置
- 边框虚化背景
```

### 3.4 变速组合技巧
```
步骤：
1. 导入视频，常规变速 0.9x
2. 进行抽帧处理
3. 导出后再加速 1.1x
4. 最终时长接近原视频，但帧完全不同
```

---

## 四、FFmpeg 实用命令

### 4.1 画中画叠加
```bash
# 基础画中画
ffmpeg -i main.mp4 -i overlay.mp4 -filter_complex "[0:v][1:v]overlay=x=20:y=20" output.mp4

# 控制显示时间
ffmpeg -i main.mp4 -i sub.mp4 -filter_complex "[0:v][1:v]overlay=enable='between(t,2,15)'" output.mp4

# 半透明叠加
ffmpeg -i main.mp4 -i overlay.png -filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.3[over];[0:v][over]overlay" output.mp4
```

### 4.2 动态水印/跑马灯
```bash
# 文字跑马灯
ffmpeg -i input.mp4 -vf "drawtext=text='hello':x=mod(100*t,w):y=abs(sin(t))*h*0.7" output.mp4

# 图片水印移动
ffmpeg -i input.mp4 -vf "movie=logo.png[wm];[in][wm]overlay=x=mod(50*t,main_w):y=abs(sin(t))*h*0.7" output.mp4
```

### 4.3 综合去重滤镜
```bash
ffmpeg -i input.mp4 -vf "
  hflip,
  eq=brightness=0.05:contrast=1.05:saturation=1.1,
  scale=720:1280
" -r 30 output.mp4
```

---

## 五、去重效果优先级

### 高效果（必做）
1. ✅ 画中画透明叠加 (1-4%)
2. ✅ 大面积遮罩 (200px+)
3. ✅ 大量贴纸 (15-20个)
4. ✅ 抽帧处理
5. ✅ 变速 (0.9x-1.1x)

### 中等效果
1. ⚡ 添加边框
2. ⚡ 色块装饰
3. ⚡ 调色处理
4. ⚡ 换BGM
5. ⚡ 添加字幕

### 低效果（辅助）
1. 💡 滤镜效果
2. 💡 修改分辨率
3. 💡 修改帧率
4. 💡 MD5修改（已过时）

---

## 六、注意事项

### 6.1 避免的做法
- ❌ 只改MD5
- ❌ 只加滤镜
- ❌ 用去水印软件（会留下模糊痕迹）
- ❌ 短时间发大量相似内容
- ❌ 直接搬运有明显水印的视频

### 6.2 推荐做法
- ✅ 组合多种去重方法
- ✅ 找冷门素材
- ✅ 加自己的配音/解说
- ✅ 重新制作片头片尾
- ✅ 控制发布频率

---

## 七、待实现功能

根据学习到的知识，以下功能可以添加到VideoMixer：

### 高优先级
- [ ] 画中画透明叠加 (自动添加1-4%透明度的实拍素材)
- [ ] 智能抽帧 (每10-15帧删除1帧)
- [ ] 变速组合 (先减速→抽帧→再加速)
- [ ] 动态水印/跑马灯效果

### 中优先级
- [ ] 自动掐头去尾 (删除前后3-5秒)
- [ ] 镜像翻转选项
- [ ] 随机旋转微调 (1-3度)
- [ ] 边缘裁剪后放大

### 低优先级
- [ ] 帧率自动调整
- [ ] 码率随机化
- [ ] 音频变调处理

---

---

## 八、转场效果 (FFmpeg xfade)

### 8.1 基本用法
```bash
ffmpeg -i v1.mp4 -i v2.mp4 -filter_complex "xfade=transition=fade:duration=1:offset=4" output.mp4
```

### 8.2 支持的转场类型
| 转场 | 效果 | 推荐场景 |
|------|------|---------|
| fade | 淡入淡出 | 通用 |
| fadeblack | 黑场过渡 | 场景切换 |
| fadewhite | 白场闪烁 | 高能时刻 |
| wipeleft | 向左擦除 | 时间流逝 |
| wiperight | 向右擦除 | 时间流逝 |
| wipeup | 向上擦除 | 揭示效果 |
| wipedown | 向下擦除 | 揭示效果 |
| slideleft | 向左滑动 | 场景切换 |
| slideright | 向右滑动 | 场景切换 |
| circlecrop | 圆形裁切 | 聚焦效果 |
| rectcrop | 矩形裁切 | 分屏过渡 |
| distance | 距离变换 | 创意转场 |
| dissolve | 溶解效果 | 柔和过渡 |

### 8.3 GL-Transition (76种高级转场)
需要编译支持 OpenGL 的 FFmpeg 版本，可实现模糊、波浪、像素化等高级特效。

---

## 九、分屏效果

### 9.1 FFmpeg 分屏命令
```bash
# 左右分屏
ffmpeg -i left.mp4 -i right.mp4 -filter_complex "[0:v]scale=360:640[l];[1:v]scale=360:640[r];[l][r]hstack" output.mp4

# 上下分屏
ffmpeg -i top.mp4 -i bottom.mp4 -filter_complex "[0:v]scale=720:640[t];[1:v]scale=720:640[b];[t][b]vstack" output.mp4

# 2x2网格
ffmpeg -i 1.mp4 -i 2.mp4 -i 3.mp4 -i 4.mp4 -filter_complex "[0:v]scale=360:320[v0];[1:v]scale=360:320[v1];[2:v]scale=360:320[v2];[3:v]scale=360:320[v3];[v0][v1]hstack[top];[v2][v3]hstack[bottom];[top][bottom]vstack" output.mp4
```

---

## 十、背景虚化填充

### 10.1 竖屏转横屏（模糊背景）
```bash
ffmpeg -i input.mp4 -vf "split[original][blur];[blur]scale=1920:1080,boxblur=20:20[blurred];[blurred][original]overlay=(W-w)/2:(H-h)/2" output.mp4
```

### 10.2 横屏转竖屏（模糊背景）
```bash
ffmpeg -i input.mp4 -vf "split[original][blur];[blur]scale=720:1280,boxblur=20:20[blurred];[blurred][original]overlay=(W-w)/2:(H-h)/2" output.mp4
```

---

## 十一、文字动画效果

### 11.1 打字机效果
```bash
# 逐字显示
ffmpeg -i input.mp4 -vf "drawtext=text='Hello':fontsize=48:fontcolor=white:x=100:y=100:enable='gte(t,1)'" output.mp4
```

### 11.2 跑马灯/滚动字幕
```bash
# 从右向左滚动
ffmpeg -i input.mp4 -vf "drawtext=text='滚动文字':fontsize=36:fontcolor=white:x=w-mod(t*100\,w+tw):y=h-60" output.mp4
```

---

## 十二、卡点与节奏

### 12.1 卡点要点
- 快节奏：1-2秒切换一次镜头
- 慢节奏：3-5秒切换一次镜头
- 在鼓点处添加转场
- 配合闪白/闪黑效果

### 12.2 变速卡点
- 高能时刻：0.5x慢放
- 过渡部分：1.5x加速
- 结合音乐节奏自动变速

---

## 十三、待实现新功能

### 高优先级
- [ ] xfade转场效果 (fade/wipe/slide/circle)
- [ ] 分屏效果 (左右/上下/九宫格)
- [ ] 背景虚化填充 (横竖屏转换)
- [ ] 文字打字机效果

### 中优先级
- [ ] 闪白/闪黑转场
- [ ] 滚动字幕/跑马灯
- [ ] 动态贴纸叠加
- [ ] 音乐卡点自动切换

### 低优先级
- [ ] GL-Transition高级转场
- [ ] 蒙版追踪
- [ ] 关键帧动画

---

*文档版本: 2.0*
*更新时间: 2025-02-04*

## Sources
- [FFmpeg xfade转场](https://blog.csdn.net/xiaolixi199311/article/details/138913135)
- [分屏效果详解](https://miao.wondershare.cn/video-creative-tips/what-is-split-screen.html)
- [背景虚化技巧](https://www.zhihu.com/question/51062628)
- [爱剪辑文字动画](https://www.ijianji.com/article/wenzidonghua.htm)
- [万兴喵影字幕特效](https://miao.wondershare.cn/features/text-animation.html)
