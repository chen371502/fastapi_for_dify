# LMStudio FastAPI 聊天接口服务

这个项目提供了一个 FastAPI 后端服务，用于包装 LMStudio 的 OpenAI API 接口，支持流式和非流式聊天补全功能。

## 🚀 功能特性

- ✅ **支持流式输出** - 实时返回生成内容
- ✅ **非流式响应** - 一次性返回完整结果  
- ✅ **健康检查** - 监控 LMStudio 连接状态
- ✅ **模型列表** - 获取可用模型信息
- ✅ **OpenAI SDK 集成** - 使用官方 SDK 简化开发

## 📁 项目结构

```
.
├── main.py          # FastAPI 主应用程序
├── requirements.txt # Python 依赖列表
├── test_simple.py   # 基础功能测试脚本
├── test_stream.py   # 流式输出测试脚本
└── README.md        # 项目说明文档
```

## 🔧 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 LMStudio

确保 LMStudio 正在运行，并记下 API 地址：
- **本地运行**: `http://localhost:1234/v1`
- **局域网运行**: `http://192.168.10.41:1234/v1`

### 3. 启动服务

```bash
# 使用默认配置启动
python main.py

# 或者自定义 LMStudio 地址
LMSTUDIO_BASE_URL="http://localhost:1234/v1" python main.py
```

服务将在 `http://localhost:8000` 启动。

## 📡 API 接口

### 1. 聊天补全 (支持流式)
**POST** `/chat/completions`

#### 流式输出示例：
```bash
curl -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "请写一段Python的快速排序代码"}
    ],
    "temperature": 0.7,
    "max_tokens": 200,
    "stream": true
  }'
```

#### 非流式输出示例：
```bash
curl -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好，请自我介绍"}
    ],
    "temperature": 0.7,
    "max_tokens": 100,
    "stream": false
  }'
```

### 2. 健康检查
**GET** `/health`

```bash
curl http://localhost:8000/health
```

### 3. 获取模型列表
**GET** `/models`

```bash
curl http://localhost:8000/models
```

## 🧪 测试脚本

### 基础测试
```bash
python test_simple.py
```
测试：服务器连接、健康检查、基础聊天功能

### 流式输出测试
```bash
python test_stream.py
```
测试：流式聊天补全功能，实时显示生成内容

## ⚙️ 配置选项

通过环境变量配置：

```bash
# LMStudio API 地址
export LMSTUDIO_BASE_URL="http://localhost:1234/v1"

# 默认模型名称
export MODEL_NAME="qwen/qwen3-coder-30b"
```

## 🔍 常见问题

### 1. 连接超时
- 确保 LMStudio 正在运行
- 检查 IP 地址和端口是否正确
- 验证防火墙设置

### 2. 模型未找到
- 确认模型已正确加载到 LMStudio
- 检查模型名称是否正确

### 3. 响应格式错误
- 确保 LMStudio 版本支持 OpenAI API 格式
- 检查返回的 JSON 结构

## 📊 请求参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `messages` | array | - | 对话消息列表 |
| `model` | string | qwen/qwen3-coder-30b | 模型名称 |
| `temperature` | float | 0.7 | 生成温度 (0-2) |
| `max_tokens` | int | 1000 | 最大生成token数 |
| `top_p` | float | 1.0 | 核采样参数 |
| `stream` | bool | false | 是否启用流式输出 |

## 🎯 使用场景

- **Web应用集成** - 为前端提供统一的API接口
- **开发测试** - 快速验证LMStudio功能
- **微服务架构** - 作为独立的聊天服务
- **原型开发** - 快速构建AI应用原型