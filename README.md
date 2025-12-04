# Titan Image Generator G1 V2 - API Documentation

## 📋 Mục lục
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Thông tin API](#thông-tin-api)
- [Các chế độ hoạt động](#các-chế-độ-hoạt-động)
- [Cấu trúc Request](#cấu-trúc-request)
- [Ví dụ JSON Config](#ví-dụ-json-config)
- [Response Format](#response-format)
- [Error Handling](#error-handling)

---

## 🏗️ Kiến trúc hệ thống

### Tổng quan Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT APPLICATION                         │
│  ┌──────────────┐         ┌──────────────┐         ┌─────────────┐ │
│  │   Web App    │         │  Mobile App  │         │  Desktop    │ │
│  └──────┬───────┘         └──────┬───────┘         └──────┬──────┘ │
│         │                        │                        │         │
│         └────────────────────────┼────────────────────────┘         │
│                                  │                                  │
│                         ┌────────▼────────┐                         │
│                         │  JSON Payload   │                         │
│                         │  + Base64 Image │                         │
│                         └────────┬────────┘                         │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │
                                   │ HTTPS POST
                                   │
                    ┌──────────────▼───────────────┐
                    │   AWS API Gateway            │
                    │   (API Endpoint)             │
                    │   /pro/gen                   │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │   AWS Lambda Function        │
                    │   (Request Handler)          │
                    │                              │
                    │   • Validate Request         │
                    │   • Parse Parameters         │
                    │   • Route by Mode            │
                    └──────┬────────────┬──────────┘
                           │            │
              ┌────────────┘            └────────────┐
              │                                      │
    ┌─────────▼─────────┐                 ┌─────────▼──────────┐
    │ Claude Sonnet 4   │                 │ Amazon Bedrock     │
    │ (Anthropic API)   │                 │ Runtime            │
    │                   │                 │                    │
    │ • Prompt          │                 └─────────┬──────────┘
    │   Enhancement     │                           │
    │ • Vietnamese      │                           │
    │   Translation     │              ┌────────────┴────────────┐
    │ • Quality         │              │                         │
    │   Optimization    │    ┌─────────▼─────────┐   ┌──────────▼──────────┐
    └─────────┬─────────┘    │ Stability AI      │   │ Amazon Titan        │
              │              │ SDXL 1.0          │   │ Image Generator V2  │
              │              │                   │   │                     │
              │              │ • Text-to-Image   │   │ • Image-to-Image    │
              │              │ • High Quality    │   │ • Inpainting        │
              │              │ • Multiple Styles │   │ • Outpainting       │
              │              └─────────┬─────────┘   └──────────┬──────────┘
              │                        │                        │
              │ Enhanced Prompt        │                        │
              └──────────┐             │                        │
                         │             │                        │
                    ┌────▼─────────────▼────────────────────────▼────┐
                    │        Image Generation Pipeline               │
                    │                                                │
                    │   IF mode = "text2img":                        │
                    │   ├─ Use Claude enhanced prompt                │
                    │   ├─ Route to Stability AI SDXL 1.0            │
                    │   ├─ Apply aspect_ratio                        │
                    │   ├─ cfg_scale, steps configuration            │
                    │   └─ Generate from scratch                     │
                    │                                                │
                    │   IF mode = "img2img":                         │
                    │   ├─ Validate init_image                       │
                    │   ├─ Check dimensions (÷64)                    │
                    │   ├─ Route to Amazon Titan V2                  │
                    │   ├─ Apply similarity_strength                 │
                    │   └─ Transform with Titan                      │
                    └──────────────┬─────────────────────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │  Generated Image  │
                         │  (Base64 Encoded) │
                         └─────────┬─────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │   Response Construction      │
                    │                              │
                    │   {                          │
                    │     "status": "success",     │
                    │     "image_base64": "...",   │
                    │     "enhanced_prompt": "..." │
                    │     "model_used": "..."      │
                    │   }                          │
                    └──────────────┬───────────────┘
                                   │
                                   │ JSON Response
                                   │
                         ┌─────────▼─────────┐
                         │   CLIENT RECEIVES │
                         │   • Decode Base64 │
                         │   • Display Image │
                         │   • Save to Disk  │
                         └───────────────────┘
```

### Component Details

#### 1. **API Gateway**
- **Endpoint:** ``
- **Method:** POST
- **Region:** us-east-1
- **Function:** Entry point, request routing, CORS handling

#### 2. **Lambda Function (Request Handler)**
- **Runtime:** Python 3.x
- **Timeout:** 120 seconds
- **Responsibilities:**
  - Request validation
  - Parameter parsing
  - **Mode-based routing** (text2img → Stability AI, img2img → Titan)
  - Service orchestration
  - Error handling
  - Response formatting

#### 3. **Claude Sonnet 4 (Prompt Enhancement)**
- **Model:** claude-sonnet-4-20250514
- **API:** Anthropic API
- **Use Cases:**
  - Enhance short/simple prompts
  - Translate Vietnamese → English
  - Add quality keywords (8k, detailed, etc.)
  - Optimize for AI image models
- **Token Limit:** 512 tokens (prompts may be truncated)

#### 4. **Stability AI SDXL 1.0** ⭐ (Text-to-Image)
- **Model ID:** `stability.stable-diffusion-xl-v1`
- **Service:** AWS Bedrock
- **Use Case:** `mode = "text2img"`
- **Capabilities:**
  - High-quality text-to-image generation
  - Multiple artistic styles
  - Fine-tuned control (cfg_scale, steps)
  - Resolution up to 1024x1024

#### 5. **Amazon Titan Image Generator V2** 🎨 (Image-to-Image)
- **Model ID:** `amazon.titan-image-generator-v2:0`
- **Service:** AWS Bedrock
- **Use Case:** `mode = "img2img"`
- **Capabilities:**
  - Image-to-Image transformation
  - Similarity strength control
  - Inpainting & Outpainting
  - Multiple aspect ratios (up to 2048px)

### Data Flow

#### Text-to-Image Flow (Stability AI)
```
User Prompt → [Claude Enhancement?] → Stability AI SDXL 1.0 → Base64 Image → Response
```

#### Image-to-Image Flow (Amazon Titan)
```
User Prompt + Init Image → [Resize Check] → [Claude Enhancement?] 
→ Amazon Titan V2 (with similarity_strength) → Base64 Image → Response
```

### Model Selection Logic

| Mode | Model Used | Service | Strengths |
|------|-----------|---------|-----------|
| **text2img** | Stability AI SDXL 1.0 | AWS Bedrock | High quality, artistic styles, fast generation |
| **img2img** | Amazon Titan V2 | AWS Bedrock | Better transformation control, similarity strength |

### Key Technical Constraints

| Component | Constraint | Impact |
|-----------|-----------|--------|
| **Claude API** | 512 token limit | Long prompts truncated |
| **Stability AI** | 1024x1024 max | Text2img size limited |
| **Titan Image** | Dimensions ÷ 64 | **MUST resize before sending** |
| **Titan Image** | 512-2048px range | Large images rejected |
| **Lambda** | 120s timeout | Complex generations may timeout |
| **API Gateway** | 10MB payload | Large base64 images may fail |

### Supported Aspect Ratios

#### Text-to-Image (Stability AI SDXL)
| Ratio | Dimensions | Claude Enhancement | Common Use |
|-------|-----------|-------------------|------------|
| 1:1 | 1024x1024 | ✅ | Square, general purpose |
| 16:9 | 1024x576 | ✅ | Landscape, banner |
| 9:16 | 576x1024 | ✅ | Portrait, mobile |

#### Image-to-Image (Amazon Titan V2)
| Ratio | Dimensions | Claude Enhancement | Common Use |
|-------|-----------|-------------------|------------|
| 1:1 | 1024x1024 | ✅ | Profile, thumbnail |
| 16:9 | 1216x640 | ✅ | Landscape, banner |
| 9:16 | 640x1216 | ✅ | Portrait, mobile |
| 3:2 | 1152x768 | ✅ | Photography |
| 3:5 | 768x1280 | ✅ | Portrait extended |

---

## 🌐 Thông tin API

**API Endpoint:**
```
POST https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen
```

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Timeout:** 120 seconds

---

## 🎨 Các chế độ hoạt động

### 1. Text-to-Image (text2img)
Tạo ảnh từ mô tả văn bản

### 2. Image-to-Image (img2img)
Biến đổi ảnh có sẵn theo hướng dẫn văn bản

---

## 📝 Cấu trúc Request

### Text-to-Image Request

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|----------|-------|
| `mode` | string | ✅ | Chế độ: `"text2img"` |
| `prompt` | string | ✅ | Mô tả ảnh muốn tạo |
| `regen_prompt` | boolean | ❌ | `true`: Tự động cải thiện prompt bằng Claude AI<br>`false`: Dùng prompt gốc (mặc định) |
| `prompt_language` | string | ❌ | Ngôn ngữ prompt: `"vi"` (tiếng Việt), `"en"` (English) |
| `aspect_ratio` | string | ❌ | Tỷ lệ ảnh: `"1:1"`, `"16:9"`, `"9:16"`, `"3:2"`, `"3:5"`<br>Mặc định: `"1:1"` |

### Image-to-Image Request

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|----------|-------|
| `mode` | string | ✅ | Chế độ: `"img2img"` |
| `prompt` | string | ✅ | Hướng dẫn biến đổi ảnh |
| `init_image` | string | ✅ | Ảnh gốc (base64 encoded) |
| `similarity_strength` | float | ❌ | Độ giống ảnh gốc: `0.0` - `1.0`<br>- `0.7-0.9`: Giữ gần giống ảnh gốc<br>- `0.3-0.5`: Thay đổi nhiều<br>Mặc định: `0.5` |
| `negative_prompt` | string | ❌ | Mô tả những gì KHÔNG muốn có trong ảnh |
| `regen_prompt` | boolean | ❌ | Tự động cải thiện prompt |
| `aspect_ratio` | string | ❌ | Tỷ lệ ảnh (như text2img) |

### ⚠️ Yêu cầu kỹ thuật cho init_image

- **Định dạng:** PNG/JPEG được encode base64
- **Kích thước:** Width và Height phải:
  - Chia hết cho 64
  - Trong khoảng 512-2048 pixels
- **⚠️ BẮT BUỘC PHẢI RESIZE:** API sẽ báo lỗi nếu ảnh không đúng kích thước. Bạn PHẢI resize ảnh trước khi gửi lên API.

### 🔧 Cách Resize Ảnh Đúng Chuẩn Titan

API không tự động resize, bạn cần resize ảnh theo đúng quy cách sau:

**Kích thước chuẩn theo Aspect Ratio:**

| Aspect Ratio | Width | Height | Use Case |
|--------------|-------|--------|----------|
| `1:1` | 1024 | 1024 | Ảnh vuông, profile, thumbnail |
| `16:9` | 1216 | 640 | Landscape, banner, wallpaper |
| `9:16` | 640 | 1216 | Portrait, mobile, story |
| `3:2` | 1152 | 768 | Photography standard |
| `3:5` | 768 | 1280 | Portrait extended |

**Python Code để Resize:**

```python
from PIL import Image

def resize_for_titan(img_path, aspect_ratio="1:1"):
    """
    Resize ảnh theo đúng chuẩn Titan Image Generator
    """
    ratio_map = {
        "1:1": (1024, 1024),
        "16:9": (1216, 640),
        "9:16": (640, 1216),
        "3:2": (1152, 768),
        "3:5": (768, 1280),
    }
    
    target_width, target_height = ratio_map.get(aspect_ratio, (1024, 1024))
    
    # Đảm bảo chia hết cho 64 và trong range 512-2048
    target_width = min(max(512, target_width - target_width % 64), 2048)
    target_height = min(max(512, target_height - target_height % 64), 2048)
    
    # Resize ảnh
    img = Image.open(img_path)
    resized_img = img.resize((target_width, target_height))
    
    return resized_img

# Sử dụng
resized = resize_for_titan("input.jpg", "16:9")
resized.save("resized_output.png")
```

---

## 📄 Ví dụ JSON Config

### 1. Text-to-Image - Cơ bản với Claude Enhancement

```json
{
  "prompt": "a beautiful sunset over mountains",
  "regen_prompt": true,
  "mode": "text2img",
  "aspect_ratio": "16:9"
}
```

### 2. Text-to-Image - Prompt chi tiết, không cần enhance

```json
{
  "prompt": "a futuristic city with flying cars, neon lights, cyberpunk style, 8k, ultra detailed, dramatic lighting, cinematic composition",
  "regen_prompt": false,
  "mode": "text2img",
  "aspect_ratio": "1:1"
}
```

### 3. Text-to-Image - Tiếng Việt

```json
{
  "prompt": "một cô gái áo dài đang đi trên cầu Nhật Bản, hoàng hôn đẹp",
  "regen_prompt": true,
  "mode": "text2img",
  "prompt_language": "vi",
  "aspect_ratio": "9:16"
}
```

### 4. Image-to-Image - Giữ gần giống ảnh gốc

```json
{
  "prompt": "turn this into a watercolor painting",
  "negative_prompt": "blurry, low quality, distorted, watermark, text, ugly, deformed",
  "regen_prompt": true,
  "mode": "img2img",
  "init_image": "iVBORw0KGgoAAAANSUhEUgAA...[base64_string]",
  "similarity_strength": 0.7,
  "aspect_ratio": "1:1"
}
```

### 5. Image-to-Image - Thay đổi mạnh

```json
{
  "prompt": "make it look like a comic book illustration, bold colors, graphic novel style",
  "negative_prompt": "blurry, low quality, distorted, watermark, text, ugly, deformed",
  "regen_prompt": true,
  "mode": "img2img",
  "init_image": "iVBORw0KGgoAAAANSUhEUgAA...[base64_string]",
  "similarity_strength": 0.3,
  "aspect_ratio": "1:1"
}
```

### 6. Image-to-Image - Với Negative Prompt mạnh

```json
{
  "prompt": "professional portrait photo, studio lighting, high quality, sharp focus",
  "negative_prompt": "blurry, low quality, distorted, watermark, text, ugly, deformed, bad anatomy, disfigured",
  "regen_prompt": true,
  "mode": "img2img",
  "init_image": "iVBORw0KGgoAAAANSUhEUgAA...[base64_string]",
  "similarity_strength": 0.5,
  "aspect_ratio": "1:1"
}
```

### 7. Image-to-Image - Aspect Ratio 16:9

```json
{
  "prompt": "epic cinematic landscape, dramatic lighting, golden hour",
  "negative_prompt": "blurry, low quality, distorted, watermark, text",
  "regen_prompt": true,
  "mode": "img2img",
  "init_image": "iVBORw0KGgoAAAANSUhEUgAA...[base64_string]",
  "similarity_strength": 0.6,
  "aspect_ratio": "16:9"
}
```

---

## 📤 Response Format

### Success Response (200)

```json
{
  "status": "success",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...[base64_encoded_image]",
  "enhanced_prompt": "A breathtaking sunset over majestic mountains...",
  "metadata": {
    "model": "amazon.titan-image-generator-v2:0",
    "aspect_ratio": "16:9",
    "dimensions": "1173x640"
  }
}
```

### Error Response (400/500)

```json
{
  "status": "error",
  "error": "Missing required parameter: prompt",
  "details": "The 'prompt' field is required for text2img mode"
}
```

---

## ⚠️ Error Handling

### Common Error Codes

| Status Code | Ý nghĩa | Giải pháp |
|-------------|---------|-----------|
| 400 | Bad Request | Kiểm tra lại các tham số bắt buộc |
| 500 | Internal Server Error | Thử lại sau hoặc liên hệ support |
| 504 | Timeout | Request quá lâu, thử giảm độ phức tạp |

### Validation Errors

- **Missing prompt:** Thiếu tham số `prompt`
- **Invalid mode:** `mode` phải là `"text2img"` hoặc `"img2img"`
- **Invalid aspect_ratio:** Phải là một trong các giá trị: `"1:1"`, `"16:9"`, `"9:16"`, `"3:2"`, `"3:5"`
- **Missing init_image:** Chế độ `img2img` cần tham số `init_image`
- **Invalid similarity_strength:** Giá trị phải từ 0.0 đến 1.0

---

## 💡 Best Practices

### 1. Prompt Engineering

**Tốt:**
```
"professional portrait photo, studio lighting, bokeh background, 50mm lens, high quality"
```

**Tránh:**
```
"make a photo"
```

### 2. Sử dụng regen_prompt

- ✅ Bật khi prompt ngắn, đơn giản
- ❌ Tắt khi prompt đã chi tiết, kỹ thuật

### 3. Negative Prompts hiệu quả

Luôn thêm các từ khóa phổ biến:
```
"blurry, low quality, distorted, watermark, text, ugly, deformed, bad anatomy"
```

### 4. Similarity Strength Guidelines

| Giá trị | Khi nào dùng |
|---------|--------------|
| 0.8-0.9 | Chỉ thay đổi nhẹ (màu sắc, style nhẹ) |
| 0.5-0.7 | Thay đổi vừa phải (watercolor, illustration) |
| 0.3-0.5 | Thay đổi mạnh (comic, hoàn toàn khác phong cách) |

---

## 🔧 Code Example (Python)

### Text-to-Image Example

```python
import requests
import base64

# Text-to-Image
response = requests.post(
    "https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen",
    json={
        "prompt": "a serene lake at sunset",
        "regen_prompt": True,
        "mode": "text2img",
        "aspect_ratio": "16:9"
    },
    headers={"Content-Type": "application/json"},
    timeout=120
)

if response.status_code == 200:
    data = response.json()
    image_base64 = data["image_base64"]
    
    # Lưu ảnh
    with open("output.png", "wb") as f:
        f.write(base64.b64decode(image_base64))
    print("✅ Image saved!")
else:
    print(f"❌ Error: {response.json()}")
```

### Image-to-Image Example (Đầy đủ với Resize)

```python
import requests
import base64
from PIL import Image
from io import BytesIO

def resize_for_titan(img_path, aspect_ratio="1:1"):
    """Resize ảnh theo đúng chuẩn Titan"""
    ratio_map = {
        "1:1": (1024, 1024),
        "16:9": (1216, 640),
        "9:16": (640, 1216),
        "3:2": (1152, 768),
        "3:5": (768, 1280),
    }
    
    target_width, target_height = ratio_map.get(aspect_ratio, (1024, 1024))
    target_width = min(max(512, target_width - target_width % 64), 2048)
    target_height = min(max(512, target_height - target_height % 64), 2048)
    
    img = Image.open(img_path)
    resized_img = img.resize((target_width, target_height))
    
    # Convert to base64
    buf = BytesIO()
    resized_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# Resize và encode ảnh
init_image_b64 = resize_for_titan("input.jpg", "1:1")

# Gọi API
response = requests.post(
    "https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen",
    json={
        "prompt": "turn this into a watercolor painting",
        "negative_prompt": "blurry, low quality, distorted",
        "regen_prompt": True,
        "mode": "img2img",
        "init_image": init_image_b64,
        "similarity_strength": 0.7,
        "aspect_ratio": "1:1"
    },
    headers={"Content-Type": "application/json"},
    timeout=120
)

if response.status_code == 200:
    data = response.json()
    # Lưu ảnh kết quả
    with open("output.png", "wb") as f:
        f.write(base64.b64decode(data["image_base64"]))
    print("✅ Image saved!")
else:
    print(f"❌ Error: {response.json()}")
```

---

## 📞 Support

Nếu gặp vấn đề, vui lòng kiểm tra:
1. ✅ Tham số bắt buộc đã đủ chưa
2. ✅ **Init image đã RESIZE đúng kích thước chưa** (BẮT BUỘC cho img2img)
3. ✅ Init image đã encode base64 đúng format chưa
4. ✅ Timeout đã đủ lớn chưa (khuyến nghị 120s)
5. ✅ Response status code để xác định lỗi

### ⚠️ Lỗi Thường Gặp với img2img

**"Invalid image dimensions"** hoặc **"Image size must be divisible by 64"**
- ✅ **Giải pháp:** Bạn PHẢI resize ảnh trước khi gửi, API không tự động resize
- ✅ Dùng hàm `resize_for_titan()` ở phần Code Example

**"Image too large"** hoặc timeout
- ✅ **Giải pháp:** Đảm bảo width/height trong khoảng 512-2048px

---

**Version:** 2.0  
**Last Updated:** December 2024
