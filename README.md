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

1. Vào **Lambda → Configuration → Permissions → Role name**
   Ví dụ: `bedrockapi-role-llgc03ti`

2. Click **Add permissions → Attach policies**

3. Tìm và chọn **AmazonBedrockFullAccess** + (nếu chưa có) **AWSLambdaBasicExecutionRole**

4. Apply là xong, Lambda sẽ có quyền **invoke Bedrock model** + **ghi logs CloudWatch** 

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

###  API Gateway

---

## 🌐 Tích hợp REST API Gateway cho Lambda

### 1️⃣ Tạo REST API

1. Vào **AWS Console → API Gateway → Create API → REST API → Build**
2. Đặt tên: `AIImageGenREST`
3. API Type: `Regional`

---

### 2️⃣ Tạo Resource & Method

1. **Resource path**: `/pro/gen`
2. Chọn **Create Resource** → Enable “API Gateway CORS” nếu frontend gọi trực tiếp từ browser.
3. Thêm **Method**: `POST` → Integration type: Lambda Function → chọn `aws_gen_pic`

**Configuration**:

| Resource   | Method | Lambda Function | Mô tả                        |
| ---------- | ------ | --------------- | ---------------------------- |
| `/pro/gen` | POST   | `aws_gen_pic`   | Sinh ảnh trực tiếp từ prompt |

> Lưu ý: Lambda sẽ tự phân biệt **Text2Image** vs **Image2Image** dựa vào `init_image_s3`.

---

### 3️⃣ Enable CORS (Frontend Call)

* Chọn resource `/pro/gen` → Actions → Enable CORS
* Allow methods: `POST`
* Allow headers: `Content-Type`
* Save và **Deploy API**

---

### 4️⃣ Deploy API

1. Chọn **Actions → Deploy API**
2. Stage name: `prod`
3. Sau khi deploy, bạn sẽ có **Invoke URL** dạng:

   ```
   https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen
   ```

---

### 5️⃣ Cấu trúc JSON request (REST API)

**Text-to-Image trực tiếp**:

```bash
curl -X POST https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a dragon flying over mountains","aspect_ratio":"16:9"}'
```

**Text-to-Image có enhancement**:

```bash
curl -X POST https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a cat","enhance_prompt":true,"aspect_ratio":"16:9"}'
```

**Image-to-Image**:

```bash
curl -X POST https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen \
  -H "Content-Type: application/json" \
  -d '{"prompt":"make it look like a watercolor","init_image_s3":"s3://gen-img-input1/input.jpg","enhance_prompt":true,"aspect_ratio":"1:1"}'
```

---

### 6️⃣ Ví dụ gọi từ Frontend (React / Next.js)

```javascript
async function generateImageREST(prompt, initImage = null, useEnhancement = true) {
  const payload = {
    prompt,
    enhance_prompt: useEnhancement,
    aspect_ratio: "16:9"
  };
  
  if (initImage) {
    payload.init_image_s3 = initImage;
  }

  const res = await fetch("https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await res.json();
  return {
    imageUrl: data.s3_url,
    originalPrompt: data.original_prompt,
    enhancedPrompt: data.enhanced_prompt
  };
}

// Usage
const result = await generateImageREST("a futuristic city", null, true);
console.log(result);
```

---

### 7️⃣ Notes

1. `/pro/gen` dùng **REST API POST** cho cả Text2Image & Image2Image.
2. Lambda tự phân biệt mode dựa vào `img2ing`,text2ing.
3. `enhance_prompt` = `true` → Lambda sẽ nâng prompt bằng Nova Pro trước khi sinh ảnh.
4. `aspect_ratio` mặc định `"16:9"`.
5. `seed` có thể dùng để sinh ảnh cố định cùng prompt.

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


