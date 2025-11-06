

* Tạo Lambda
* Cấu hình IAM role
* Tạo và gán quyền S3
* Gọi model Stability SD3.5 qua Bedrock
* Ví dụ JSON cho `text-to-image` và `image-to-image`


````markdown
# 🧠 AWS Lambda + Bedrock Stable Diffusion 3.5 Image Generator

Một project mẫu cho phép sinh ảnh từ prompt (Text-to-Image) hoặc biến đổi ảnh (Image-to-Image) thông qua **AWS Lambda** và **Amazon Bedrock (Stability.ai)**.

---

## 🚀 1. Yêu cầu ban đầu

- AWS account đã bật dịch vụ **Bedrock**
- Có quyền tạo **S3 buckets** và **Lambda function**
- AWS CLI hoặc giao diện console
- Python 3.11

---

## 🏗️ 2. Tạo S3 Buckets

Tạo hai bucket (có thể đổi tên):

| Bucket | Vai trò |
|--------|----------|
| `gen-img-input1` | Nơi chứa ảnh gốc khi dùng Image-to-Image |
| `gen-img-out1`   | Nơi lưu ảnh kết quả sau khi sinh hoặc biến đổi |

> ⚠️ Lưu ý: mỗi bucket phải ở cùng region với Lambda, ví dụ `us-west-2`.

---

## 🔐 3. Tạo IAM Role cho Lambda

1. Truy cập **IAM → Roles → Create role**
2. Chọn **Trusted entity type: AWS Service**
3. Chọn **Use case: Lambda**
4. Nhấn **Next**, gán các quyền sau:

### Chính sách 1️⃣ – Quyền gọi Bedrock
```json
{
  "Effect": "Allow",
  "Action": ["bedrock:InvokeModel"],
  "Resource": "arn:aws:bedrock:us-west-2::foundation-model/stability.sd3-5-large-v1:0"
}
````

### Chính sách 2️⃣ – Quyền S3 Input/Output

```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject"],
  "Resource": "arn:aws:s3:::gen-img-input1/*"
},
{
  "Effect": "Allow",
  "Action": ["s3:PutObject"],
  "Resource": "arn:aws:s3:::gen-img-out1/*"
}
```

### Chính sách 3️⃣ – Quyền ghi log (CloudWatch)

```json
{
  "Effect": "Allow",
  "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "arn:aws:logs:*:*:*"
}
```

---

## ⚙️ 4. Tạo Lambda Function

1. Truy cập **AWS Lambda → Create function**
2. Chọn:

   * **Runtime:** Python 3.11
   * **Architecture:** x86_64
   * **Role:** chọn IAM role vừa tạo ở trên
3. Sau khi tạo xong, tăng:

   * **Timeout:** 1 phút
   * **Memory:** 512 MB
4. Trong tab **Configuration → Environment variables**, thêm:

   ```
   OUTPUT_BUCKET = gen-img-out1
   ```

---

## 📦 5. Triển khai code Lambda

### 📁 File structure

```
.
├── lambda_function.py
├── requirements.txt
├── README.md
```

### requirements.txt

```txt
boto3>=1.28.0
```

### Deploy script (nếu dùng CLI)

```bash
#!/bin/bash
mkdir lambda_package
cd lambda_package

cp ../lambda_function.py .
pip install -r ../requirements.txt -t .

zip -r ../sd35-lambda.zip .
aws lambda update-function-code \
  --function-name sd35-image-generator \
  --zip-file fileb://../sd35-lambda.zip
```

---

## 🧠 6. Cấu trúc JSON Model Stability SD3.5

### 🖼️ Text-to-Image

```json
{
  "model": "stability.sd3-5-large-v1:0",
  "taskType": "TEXT_TO_IMAGE",
  "textToImageParams": {
    "text": "a cyberpunk cat in neon city, digital art",
    "negativeText": "blurry, low quality",
    "aspectRatio": "16:9",
    "cfgScale": 7.5,
    "seed": 42,
    "steps": 30,
    "style": "digital-art"
  },
  "outputFormat": "jpeg"
}
```

### 🔁 Image-to-Image

```json
{
  "model": "stability.sd3-5-large-v1:0",
  "taskType": "IMAGE_TO_IMAGE",
  "imageToImageParams": {
    "image": "s3://gen-img-input1/inputs/source_cat.jpg",
    "text": "turn this into a watercolor painting",
    "strength": 0.7,
    "cfgScale": 7.5,
    "steps": 30
  },
  "outputFormat": "jpeg"
}
```

---

## 🧩 7. Ví dụ event JSON dùng cho Lambda test

### 1️⃣ Text-to-Image

```json
{
  "prompt": "a cat wearing sunglasses, digital art",
  "aspect_ratio": "16:9",
  "output_s3": {
    "bucket": "gen-img-out1",
    "key": "outputs/"
  }
}
```

### 2️⃣ Image-to-Image

```json
{
  "prompt": "transform this photo into watercolor style",
  "mode": "image-to-image",
  "strength": 0.7,
  "aspect_ratio": "1:1",
  "input_image_s3": {
    "bucket": "gen-img-input1",
    "key": "inputs/source_cat.jpg"
  },
  "output_s3": {
    "bucket": "gen-img-out1",
    "key": "transformed/"
  }
}
```

---

## ✅ 8. Kết quả mẫu

Khi chạy test event thành công, Lambda trả về:

```json
{
  "statusCode": 200,
  "body": {
    "message": "Image generated successfully",
    "s3_url": "s3://gen-img-out1/outputs/sd35_20251106_103022.jpeg",
    "bucket": "gen-img-out1",
    "key": "outputs/sd35_20251106_103022.jpeg"
  }
}
```

---

## 📊 9. CloudWatch Logs Query (debug lỗi)

```sql
fields @timestamp, @message
| filter @message like /Error/
| sort @timestamp desc
| limit 20
```

---

## 🧹 10. Dọn dẹp & tiết kiệm chi phí

* Bật **Lifecycle rule** cho bucket `gen-img-out1` để tự xóa ảnh sau 30 ngày
  *(S3 → Management → Lifecycle rules → Add rule → Delete after 30 days)*
* Không bật **versioning** nếu không cần.
* Nếu ít dùng, tổng chi phí chỉ vài nghìn đồng mỗi tháng.

---

## ✨ Credits

* **Model:** Stability.ai SD3.5 Large (Amazon Bedrock)
* **Author:** Khanh
* **Runtime:** AWS Lambda + Python 3.11

```

