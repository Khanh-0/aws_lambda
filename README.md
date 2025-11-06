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
