Chắc rồi! Mình sẽ giúp bạn **chỉnh lại README theo kiến trúc API mới**, bỏ Nova Pro và S3 nếu không dùng nữa, đồng thời giữ đầy đủ hướng dẫn Lambda, IAM, gọi mô hình Claude 3 trong code, cấu trúc JSON chuẩn cho web coder, kèm note dễ hiểu. Mình viết lại toàn bộ theo style gọn, rõ ràng, dễ áp dụng:

---

# 🎨 AWS Lambda + Amazon Bedrock - AI Image Generation API

Hệ thống sinh ảnh AI sử dụng **Amazon Bedrock** với **Stability AI SD3.5** hoặc **Claude 3**. Không còn sử dụng Nova Pro hay S3 mặc định. API hoàn toàn **serverless**, dễ tích hợp frontend.

---

## ✨ Tính năng

* 🖼️ **Text-to-Image**: Sinh ảnh từ mô tả văn bản
* 🎨 **Image-to-Image**: Biến đổi ảnh có sẵn (tùy chọn)
* ☁️ **Serverless**: Tự động scale, không cần quản lý server
* 🚀 **Fast**: Xử lý vài giây
* 💰 **Cost-effective**: Chỉ trả tiền khi sử dụng
* 🌐 **API-ready**: Dễ tích hợp frontend/web

---

## 📋 Yêu cầu

* AWS Account với **Bedrock** đã enable
* Region: `us-west-2` (Oregon)
* Models enable trong Bedrock:

  * `stability.sd3-5-large-v1:0` (sinh ảnh)
  * `anthropic.claude-v2-100k:3` (LLM, nếu cần xử lý text/logic)
* Lambda Runtime: Python 3.11
* IAM Role: quyền invoke Bedrock model và Lambda

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────┐      ┌───────────────┐
│   Client    │─────▶│ Lambda API     │─────▶ Bedrock Model
│ (Web/API)   │      │ (aws_gen_pic) │      │ SD3.5 / Claude 3
└─────────────┘      └───────────────┘
```

* Client gửi **JSON request** → Lambda → Bedrock → trả JSON với **base64 image hoặc URL**.

---

## 📝 Cấu trúc JSON Request

| Field               | Type   | Required | Notes                                                                     |
| ------------------- | ------ | -------- | ------------------------------------------------------------------------- |
| `prompt`            | string | ✅        | Mô tả nội dung hình ảnh                                                   |
| `mode`              | string | ❌        | `"text2img"` (default) hoặc `"img2img"`                                   |
| `init_image_base64` | string | ❌        | Chỉ dùng `"img2img"`; base64 ảnh đầu vào                                  |
| `aspect_ratio`      | string | ❌        | `"1:1"` (default), `"16:9"`, `"9:16"`, `"21:9"`                           |
| `model`             | string | ❌        | `"stability.sd3-5-large-v1:0"` (default) hoặc Claude 3 nếu dùng cho logic |
| `seed`              | int    | ❌        | Tùy chọn, dùng để sinh ngẫu nhiên cố định                                 |
| `enhance_prompt`    | bool   | ❌        | Nếu true, Lambda có thể tự xử lý logic prompt (tuỳ cài đặt)               |

---

### Ví dụ JSON

**Text-to-Image**

```json
{
  "prompt": "a futuristic cyberpunk city, neon lights, raining, cinematic",
  "mode": "text2img",
  "aspect_ratio": "16:9",
  "seed": 42
}
```

**Image-to-Image**

```json
{
  "prompt": "make it look like an oil painting",
  "mode": "img2img",
  "init_image_base64": "<base64_image_here>",
  "aspect_ratio": "1:1"
}
```

**Với Claude 3 logic (ví dụ thêm tags)**

```json
{
  "prompt": "a cat",
  "mode": "text2img",
  "model": "anthropic.claude-v2-100k:3",
  "enhance_prompt": true
}
```

---

## 🚀 Hướng dẫn triển khai Lambda

### 1️⃣ IAM Role

Tạo Role cho Lambda với quyền:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-west-2::foundation-model/stability.sd3-5-large-v1:0",
        "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-v2-100k:3"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

* Role này attach trực tiếp cho Lambda function.

---

### 2️⃣ Lambda Function (`aws_gen_pic.py`)

* Lambda nhận **JSON request**
* Gọi Bedrock model (SD3.5 hoặc Claude 3)
* Trả JSON gồm:

```json
{
  "statusCode": 200,
  "body": {
    "message": "Image generated successfully",
    "image_base64": "<base64_image>",
    "parameters": {
      "prompt": "...",
      "model": "...",
      "aspect_ratio": "...",
      "seed": 42
    }
  }
}
```

**Ghi chú**:

* `mode="img2img"` → gửi `init_image_base64`
* `mode="text2img"` → chỉ cần `prompt`
* Nếu dùng Claude 3 cho logic → Lambda có thể tạo prompt phức tạp trước khi gửi SD3.5

---

### 3️⃣ Web Integration (Frontend)

**Fetch API example (React/Next.js)**

```javascript
const generateImage = async (prompt, mode='text2img') => {
  const response = await fetch("https://your-api.execute-api.us-west-2.amazonaws.com/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, mode, aspect_ratio: "16:9" })
  });
  const data = await response.json();
  return data.body.image_base64; // decode để hiển thị
};
```

* **Note:** Frontend coder chỉ cần gửi JSON chuẩn như trên.
* Không cần quan tâm S3 hay Nova Pro nữa.

---

### 4️⃣ Test Lambda

**Test Event JSON**

```json
{
  "body": "{\"prompt\": \"a dragon flying over mountains\", \"mode\": \"text2img\"}"
}
```

* Chạy Test → kiểm tra logs CloudWatch
* Kiểm tra response JSON trả về `image_base64`

---

### 5️⃣ Optional: API Gateway

* Tạo HTTP API → POST `/generate`
* Lambda integration → `aws_gen_pic`
* Frontend gọi trực tiếp endpoint này

---

## 🐛 Troubleshooting

| Lỗi               | Nguyên nhân               | Giải pháp                    |
| ----------------- | ------------------------- | ---------------------------- |
| `Model not found` | Model chưa enable         | Enable trong Bedrock console |
| `Timeout`         | Request nặng              | Tăng timeout Lambda 30 → 60s |
| `Invalid base64`  | Ảnh img2img bị lỗi encode | Kiểm tra base64              |

---

## 💡 Notes for Web Coder

* **JSON request chuẩn**: prompt, mode, aspect_ratio, init_image_base64 (img2img), seed
* **JSON response chuẩn**: statusCode, body → image_base64 + parameters
* Không cần xử lý S3 hoặc Nova Pro
* Nếu muốn logic prompt → dùng Claude 3

---

## 📚 References

* [Amazon Bedrock Docs](https://docs.aws.amazon.com/bedrock/)
* [Stability AI SD3.5 Model](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion-stability-sd3.html)
* [Claude 3 Model](https://www.anthropic.com/)

---

Nếu bạn muốn, mình có thể làm **version README hoàn chỉnh có hình minh họa luồng request/response JSON, note riêng phần web coder** nữa, để copy-paste trực tiếp vào repo.

Bạn có muốn mình làm luôn không?
