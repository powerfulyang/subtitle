# SRT字幕生成器

一个基于OpenAI Whisper的音频/视频文件自动字幕生成工具，提供RESTful API接口，支持多种媒体格式，自动生成SRT格式字幕文件。

## 功能特性

- 🎬 支持音频和视频文件的字幕生成
- 🌐 提供RESTful API接口，便于集成
- 🚀 基于faster-whisper，提供高性能推理
- 💾 自动临时文件管理和清理
- 🔧 支持GPU和CPU运行环境
- 📝 输出标准SRT格式字幕文件
- 🌍 支持多语言音频识别

## 系统要求

### 基础环境
- Python 3.10 或更高版本
- Windows 10+ / Linux / macOS

### 硬件要求
- **推荐配置**: NVIDIA GPU (支持CUDA)
- **最低配置**: CPU (性能较低但可运行)

## 安装说明

### 1. 克隆项目

```bash
git clone <repository-url>
cd subtitle
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 安装PyTorch (关键步骤)

**⚠️ 重要提示**: 请根据您的硬件配置选择合适的PyTorch版本

#### GPU版本 (推荐，需要NVIDIA显卡)

如果您的电脑有NVIDIA显卡，请安装GPU版本以获得最佳性能：

1. **检查CUDA版本**:
   ```bash
   nvidia-smi
   ```

2. **安装对应的PyTorch版本**:
   
   **CUDA 11.8**:
   ```bash
   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
   
   **CUDA 12.6**:
   ```bash
   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
   ```

   **CUDA 12.8**:
   ```bash
   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
   ```

#### CPU版本 (无显卡或显卡不兼容时使用)

如果您的电脑没有NVIDIA显卡或希望仅使用CPU：

```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**注意**: CPU版本的处理速度明显慢于GPU版本，建议用于测试或轻量使用场景。

### 4. 安装 audio-separator 用于分离人声和背景音乐

```bash
pip install audio-separator
```

### 5. 验证安装

运行以下Python代码验证PyTorch安装：

```python
import torch
print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA版本: {torch.version.cuda}")
    print(f"GPU数量: {torch.cuda.device_count()}")
    print(f"当前GPU: {torch.cuda.get_device_name(0)}")
```

## 使用方法

### 方式一：直接启动 (开发/测试)

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

### 方式二：Windows服务部署 (生产环境推荐)

🎯 **推荐用于生产环境**：将应用部署为Windows系统服务，具有自动启动、后台运行、故障恢复等企业级特性。

#### 快速安装

**以管理员身份**运行PowerShell或命令提示符，然后执行：

```powershell
# 一键安装并启动服务
.\install_service.ps1

# 或使用批处理脚本
install_service.bat
```

#### 手动安装

```bash
# 1. 安装Windows服务依赖
pip install pywin32

# 2. 安装服务
python service.py install

# 3. 启动服务
python service.py start
```

#### 服务管理

```bash
# 查看服务状态
python service.py status

# 启动服务
python service.py start
net start SubtitleGenerationService

# 停止服务
python service.py stop
net stop SubtitleGenerationService

# 卸载服务
python service.py remove

# 调试模式运行
python service.py debug
```

**Windows服务优势**：
- ✅ 系统启动时自动运行
- ✅ 后台运行，无需用户登录
- ✅ 服务故障自动重启
- ✅ 集成Windows事件日志
- ✅ 专业的服务管理界面

> 详细的Windows服务部署说明请参考：[SERVICE_README.md](SERVICE_README.md)

### API接口

#### 生成字幕

**端点**: `POST /generate_subtitle/`

**参数**:
- `file`: 音频或视频文件 (multipart/form-data)

**示例请求**:

```bash
curl -X POST "http://localhost:8002/generate_subtitle/" \
     -F "file=@your_video.mp4"
```

**响应**: 返回SRT格式的字幕文件下载

### 支持的文件格式

- **音频**: MP3, WAV, FLAC, AAC, OGG
- **视频**: MP4, AVI, MOV, MKV, WMV

## 配置说明

### 模型配置

项目默认使用 `large-v2` 模型，您可以在 `app/subtitle.py` 中修改：

```python
MODEL_SIZE = "large-v2"  # 可选: tiny, base, small, medium, large-v2, large-v3
```

**模型选择建议**:
- `large-v2`: 推荐，性能稳定，适用于多种语言
- `large-v3`: 最新版本，精度更高但需要更多计算资源
- `medium`: 平衡性能和速度的选择
- `base/small`: 速度快但精度较低

### 设备配置

系统会自动检测并选择最佳设备：
- 有NVIDIA GPU: 自动使用CUDA加速
- 仅有CPU: 自动降级到CPU模式

## 性能优化建议

1. **GPU内存优化**: 如遇显存不足，可降低模型大小或使用CPU模式
2. **批处理**: 对于大量文件，建议分批处理
3. **模型缓存**: 首次运行会下载模型，后续使用会自动加载缓存

## 故障排除

### 常见问题

1. **CUDA错误**:
   ```
   解决方案: 重新安装对应CUDA版本的PyTorch
   ```

2. **内存不足**:
   ```
   解决方案: 使用较小的模型或CPU模式
   ```

3. **模型下载失败**:
   ```
   解决方案: 检查网络连接，模型会自动下载到缓存目录
   ```

### 日志查看

应用启动后会显示详细的设备和模型加载信息，有助于诊断问题。

## 项目结构

```
subtitle/
├── app/
│   ├── logger_config.py     # 日志配置
│   └── subtitle.py          # 核心字幕生成逻辑
├── main.py                  # FastAPI应用入口
├── service.py               # Windows服务实现
├── install_service.bat      # Windows服务安装脚本 (批处理)
├── install_service.ps1      # Windows服务安装脚本 (PowerShell)
├── requirements.txt         # Python依赖
├── README.md               # 项目说明
├── SERVICE_README.md       # Windows服务详细说明
├── Dockerfile              # Docker容器配置
└── temp/                   # 临时文件目录 (自动创建)
```

## 技术栈

- **后端框架**: FastAPI
- **AI模型**: OpenAI Whisper (via faster-whisper)
- **深度学习**: PyTorch
- **API文档**: 自动生成 (访问 `/docs`)

## 许可证

本项目采用开源许可证，详见项目根目录的LICENSE文件。

## 支持与反馈

如遇问题或有改进建议，欢迎提交Issue或Pull Request。

---

**注意**: 首次使用时，系统会自动下载Whisper模型文件，请确保网络连接正常。GPU版本可显著提升处理速度，强烈推荐有NVIDIA显卡的用户安装GPU版本的PyTorch。
