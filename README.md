# PRTS-SAM (Point-click Region Tracking Software)

利用 Segment Anything (SAM) 模型进行快速标注的集成工具套件

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green.svg)
![SAM](https://img.shields.io/badge/SAM-Meta-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🤔 这是什么？

这是一个基于 **Meta Segment Anything Model (SAM)** 的**图像处理与标注工具套件**，集成了数据处理、嵌入向量生成、模型导出和标注功能。

**核心特点**：一站式解决 SAM 相关任务，从数据预处理到模型部署，再到交互式标注

## ✨ 特性

- 📊 **数据预处理**：批量图片缩放、格式转换、数据集划分和分组存储
- 🧠 **嵌入向量预计算**：批量生成图像嵌入向量，加速后续标注
- ⚡ **ONNX 模型导出**：将 SAM 模型转换为 ONNX 格式，支持量化优化
- 🖱️ **交互式标注**：点几下鼠标，SAM 帮你找出目标（待集成）
- 🔧 **模块化设计**：每个功能独立，可按需使用
- 💾 **配置持久化**：自动保存用户设置和偏好

## 🏗️ 工具套件

### 📷 图片批量处理工具
- 支持等比例缩放、拉伸、裁剪三种模式
- 自动划分训练集和验证集
- 智能分组存储，避免单文件夹文件过多
- 统一重命名和编号

### 🧠 SAM 嵌入向量生成工具
- 支持传统模式和分组模式扫描
- 递归处理子文件夹中的 images 目录
- 实时进度显示和剩余时间预估
- 自动创建 embeddings 目录结构

### ⚡ ONNX 模型导出工具
- PyTorch 模型转换为 ONNX 格式
- 支持 8 位量化（减小模型大小）
- 动态形状支持（可变点数输入）
- 分阶段进度显示

### 🎯 SAM 标注工具（待集成）
- 基于原 salt 项目的交互式标注功能
- 支持前景/背景点标注
- 实时掩码预测和调整

## 📸 界面概览

```
┌─────────────────────────────────────────────────────────────┐
│  PRTS-SAM 工具套件 v1.0                                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │  📷 图片处理  🧠 SAM嵌入向量  ⚡ ONNX导出  🎯 SAM标注 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  1. 图片处理：输入 → 缩放 → 输出 → 开始处理                │
│  2. 嵌入向量：模型设置 → 数据集设置 → 开始生成             │
│  3. ONNX导出：输入设置 → 输出设置 → 开始导出              │
│  4. SAM标注：加载模型 → 选择图片 → 交互标注 → 保存        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ 安装

### 环境要求

- Python 3.8+
- PyTorch 1.12+ (推荐 2.0+)
- 支持 CUDA 的显卡（可选，但推荐）

### 安装步骤

```bash
# 1. 克隆本项目
git clone https://github.com/你的用户名/PRTS-SAM.git
cd PRTS-SAM

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载 SAM 模型权重（选一个）
# vit_h 版本（2.4GB）
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth

# vit_l 版本（1.2GB）
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth

# vit_b 版本（375MB）
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
```

## 🚀 使用方法

### 启动程序
```bash
python main.py
```

### 三步式工作流程

#### 1. 数据准备（图片处理工具）
```
选择图片目录 → 设置缩放参数 → 配置输出 → 开始处理
```

**输出结构**：
```
dataset/ieee_apple_dataset/
├── train/
│   ├── train_001/images/train_00001.png
│   └── ...
└── val/
    ├── val_001/images/val_02001.png
    └── ...
```

#### 2. 嵌入向量预计算（嵌入向量工具）
- **传统模式**：处理单层 images 目录
- **分组模式**：递归处理多层子文件夹

**输出结构**：
```
dataset/ieee_apple_dataset/
├── train_001/
│   ├── images/train_00001.png
│   └── embeddings/train_00001.npy
└── ...
```

#### 3. 模型导出（ONNX 导出工具）
- 选择 PyTorch 模型权重
- 设置输出路径和参数
- 可选 8 位量化

#### 4. 交互式标注（待集成）
- 加载预计算的嵌入向量
- 使用 ONNX 模型进行实时推理
- 点选标注并保存结果

## 📁 项目结构

```
PRTS-SAM/
├── main.py                 # 程序入口
├── ui/                     # 用户界面
│   ├── main_window.py      # 主窗口
│   ├── image_resize.py     # 图片处理界面
│   ├── sam_embeddings.py   # 嵌入向量界面
│   ├── onnx_export.py      # ONNX导出界面
│   └── sam_annotator.py    # 标注界面（待集成）
├── utils/                  # 工具模块
│   ├── image_resize/       # 图片处理核心
│   ├── sam_embeddings/     # 嵌入向量核心
│   └── onnx_export/        # ONNX导出核心
└── requirements.txt        # 依赖列表
```

## 📝 常见问题

### Q: 需要多大的显存？
- **图片处理**：不需要显存，纯 CPU 处理
- **嵌入向量生成**：需要显存加载 SAM 模型（vit_h 约 6GB，vit_b 约 2GB）
- **ONNX 导出**：需要显存加载模型进行转换
- 话是这么说，但是，我的RTX 3050 + 12500H + 16GB RAM都能跑，不会真的有人跑不起来吧

### Q: 支持哪些图片格式？
- 支持所有常见格式：`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp`

### Q: 量化后的模型效果如何？
- 量化后模型文件大小减少约 160 倍(2.4GB->15MB)
- 推理速度可能提升(自信点，提升的非常大)
- 精度略有损失，但通常可接受(没关系的，拿来生成掩膜而已)

### Q: 为什么不用 SAM2？
- 去看我仓库的另一个项目吧，那个是SAM2的
- 这个是基于[salt](https://github.com/anuragxel/salt)和[SAM-Tool](https://github.com/zhouayi/SAM-Tool)重构的，加入了部分图形化支持
- 用别怕，怕别用，但是不要相信我，我都不相信自己
- 总之经常保存是对的

## ⚠️ 免责声明

- 🎓 **这是个人毕设工具**，功能够用就行，不追求完美
- 🐛 **Bug？什么 Bug？** 那叫 特性！无限水在MC里不就是特性吗！
- 📮 **Issue？** 看心情回复，大概率不会回
- 🍴 **要新功能？** Fork 一个自己加吧，代码都给你了
- 💥 **用出问题了？** 自己 Debug，我相信你可以的

## 🤝 贡献

欢迎 Fork！但 PR 我可能不会合并，因为：

1. 我懒
2. 毕设做完这项目就归档了
3. 真的懒
4. 我真的懒


## 🤝 致谢

- [Meta SAM](https://github.com/facebookresearch/segment-anything) - 没有 SAM 就没有这个工具
- [salt](https://github.com/anuragxel/salt) - 提供了交互式标注的灵感和基础代码
- [SAM-Tool](https://github.com/zhouayi/SAM-Tool) - salt的本地化版本，本项目的基础，不喜欢gui的用这个，好用，爱用
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
- 师兄 - 提供项目需求和指导
- 我的电脑 - 承受了无数次"python main.py"和 CUDA 内存不足的折磨

## 📄 License

MIT License - 随便用，但用出问题别找我  
还是那句话，用别怕，怕别用  
记得常保存

## 🙏 使用建议

1. **数据预处理很重要**：统一图片尺寸和格式能显著提升后续处理效率
2. **嵌入向量预计算**：标注前先批量生成嵌入向量，节省实时计算时间
3. **模型量化权衡**：如果显存紧张，使用量化模型；如果追求精度，用原版模型
4. **常保存配置**：程序会自动保存设置，但手动保存预设更保险

---

**如果这个工具帮到了你，给个 Star ⭐ 呗（虽然我可能不会看）**

> **最后更新**：2026年1月10日
> 
> **当前状态**：图片处理 ✓ | 嵌入向量 ✓ | ONNX导出 ✓ | SAM标注 ⏳
> 
> **下一目标**：集成交互式标注功能，完成完整的 SAM 工具链