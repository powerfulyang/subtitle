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
git clone https://github.com/powerfulyang/subtitle.git
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
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
   
   **CUDA 12.6**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
   ```

   **CUDA 12.8**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
   ```
#### CPU版本 (无显卡或显卡不兼容时使用)

如果您的电脑没有NVIDIA显卡或希望仅使用CPU：

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**注意**: CPU版本的处理速度明显慢于GPU版本，建议用于测试或轻量使用场景。

### 4. 安装 audio-separator

主要应对音频分离需求，如音频中包含多种音轨（如音乐和人声）时，使用音频分离器可以提高字幕生成的准确性。

如果您希望使用CPU版本的音频分离器（适用于无GPU或显卡不兼容的情况）：
```bash
pip install "audio-separator[cpu]"
```

如果您希望使用GPU版本的音频分离器（推荐）：
```bash
pip install "audio-separator[gpu]"
```


## 使用方法

### 方式一：直接启动 (开发/测试)

```bash
python main.py
```

服务将在 `http://localhost:8002` 启动。

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
