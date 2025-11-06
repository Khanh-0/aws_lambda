# 🎨 AWS Lambda + Amazon Bedrock - AI Image Generation

Hệ thống sinh ảnh AI sử dụng **Stability AI SD3.5** thông qua **Amazon Bedrock**, tự động hóa hoàn toàn với AWS Lambda và lưu trữ kết quả trên S3.

## ✨ Tính năng

- 🖼️ **Text-to-Image**: Sinh ảnh từ mô tả văn bản
- 🎨 **Image-to-Image**: Biến đổi ảnh có sẵn theo phong cách mới
- ☁️ **Serverless**: Không cần quản lý server, tự động scale
- 💾 **Auto Storage**: Tự động lưu ảnh lên S3
- 🚀 **Fast**: Xử lý trong vài giây
- 💰 **Cost-effective**: Chỉ trả tiền khi sử dụng

## 📋 Yêu cầu

- AWS Account với Bedrock đã được kích hoạt
- Region: `us-west-2` (Oregon)
- Model: `stability.sd3-5-large-v1:0` đã được enable trong Bedrock
- Quyền tạo: IAM Role, S3 Bucket, Lambda Function

## 🏗️ Kiến trúc hệ thống

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│   Lambda     │─────▶│   Bedrock   │
│ (API/Test)  │      │ aws_gen_pic  │      │   SD3.5     │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                     ┌──────▼────────┐
                     │  S3 Buckets   │
                     │ ├─ Input      │
                     │ └─ Output     │
                     └───────────────┘
```

## 🚀 Hướng dẫn cài đặt

### Bước 1: Tạo S3 Buckets

Tạo 2 bucket để lưu ảnh đầu vào và đầu ra:

```bash
# Bucket cho ảnh đầu vào (Image-to-Image)
aws s3 mb s3://gen-img-input1 --region us-west-2

# Bucket cho ảnh đầu ra
aws s3 mb s3://gen-img-out1 --region us-west-2
```

### Bước 2: Tạo IAM Role

1. Vào **AWS Console → IAM → Roles → Create role**
2. Chọn:
   - **Trusted entity type**: AWS service
   - **Use case**: Lambda
3. Attach policies:
   - `AWSLambdaBasicExecutionRole`
4. Thêm **Inline Policy** sau:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-west-2::foundation-model/stability.sd3-5-large-v1:0"
    },
    {
      "Sid": "S3ReadInput",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::gen-img-input1/*"
    },
    {
      "Sid": "S3WriteOutput",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::gen-img-out1/*"
    }
  ]
}
```

5. Đặt tên role: `lambda-bedrock-image-gen-role`

### Bước 3: Tạo Lambda Function

1. Vào **AWS Console → Lambda → Create function**
2. Cấu hình:
   - **Function name**: `aws_gen_pic`
   - **Runtime**: Python 3.11
   - **Architecture**: x86_64
   - **Execution role**: Chọn role vừa tạo
3. **Configuration**:
   - **Timeout**: 15 seconds
   - **Memory**: 512 MB
4. **Environment variables**:

| Key | Value |
|-----|-------|
| `OUTPUT_BUCKET` | `gen-img-out1` |
| `INPUT_BUCKET` | `gen-img-input1` |

### Bước 4: Deploy Lambda Code

Copy code sau vào Lambda function:

```python
import json
import boto3
import base64
import os
from datetime import datetime

# Initialize AWS clients
bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")
s3 = boto3.client("s3")

# Environment variables
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET", "gen-img-out1")
INPUT_BUCKET = os.environ.get("INPUT_BUCKET", "gen-img-input1")

def lambda_handler(event, context):
    """
    Main Lambda handler for image generation using Stability AI SD3.5
    
    Supports:
    - Text-to-Image: Generate from text prompt
    - Image-to-Image: Transform existing image
    """
    try:
        # Parse request body
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        
        # Extract parameters with defaults
        prompt = body.get("prompt", "a cat wearing sunglasses, digital art")
        aspect_ratio = body.get("aspect_ratio", "16:9")
        seed = int(body.get("seed", 0))
        model = body.get("model", "stability.sd3-5-large-v1:0")
        init_image_s3 = body.get("init_image_s3")  # Optional: for image-to-image
        
        # Build Bedrock request
        request = {
            "mode": "text-to-image" if not init_image_s3 else "image-to-image",
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "seed": seed,
        }
        
        # Load input image if image-to-image mode
        if init_image_s3:
            # Parse S3 path: s3://bucket/key
            bucket, key = init_image_s3.replace("s3://", "").split("/", 1)
            
            # Download image from S3
            image_obj = s3.get_object(Bucket=bucket, Key=key)
            image_bytes = image_obj["Body"].read()
            
            # Encode to base64
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            request["image"] = b64_image
        
        # Invoke Bedrock model
        response = bedrock.invoke_model(
            modelId=model,
            body=json.dumps(request)
        )
        
        # Parse response
        result = json.loads(response["body"].read())
        image_b64 = result["images"][0]
        image_bytes = base64.b64decode(image_b64)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sd35_{timestamp}.jpeg"
        key = f"outputs/{filename}"
        
        # Upload to S3
        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=key,
            Body=image_bytes,
            ContentType="image/jpeg"
        )
        
        # Return success response
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Image generated successfully",
                "s3_url": f"s3://{OUTPUT_BUCKET}/{key}",
                "bucket": OUTPUT_BUCKET,
                "key": key,
                "filename": filename,
                "parameters": {
                    "prompt": prompt,
                    "model": model,
                    "aspect_ratio": aspect_ratio,
                    "seed": seed
                }
            })
        }
    
    except Exception as e:
        # Return error response
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Failed to generate image"
            })
        }
```

## 📝 Cách sử dụng

### Text-to-Image (Sinh ảnh từ văn bản)

**Request JSON:**

```json
{
  "prompt": "a futuristic city at sunset, ultra detailed, cinematic lighting",
  "aspect_ratio": "16:9",
  "seed": 42
}
```

**Response:**

```json
{
  "statusCode": 200,
  "body": {
    "message": "Image generated successfully",
    "s3_url": "s3://gen-img-out1/outputs/sd35_20251106_103022.jpeg",
    "bucket": "gen-img-out1",
    "key": "outputs/sd35_20251106_103022.jpeg",
    "filename": "sd35_20251106_103022.jpeg",
    "parameters": {
      "prompt": "a futuristic city at sunset...",
      "model": "stability.sd3-5-large-v1:0",
      "aspect_ratio": "16:9",
      "seed": 42
    }
  }
}
```

### Image-to-Image (Biến đổi ảnh)

**Bước 1**: Upload ảnh gốc lên S3

```bash
aws s3 cp input.jpg s3://gen-img-input1/sample_input.jpeg
```

**Bước 2**: Gọi Lambda với request

```json
{
  "prompt": "turn this into watercolor painting style",
  "init_image_s3": "s3://gen-img-input1/sample_input.jpeg",
  "aspect_ratio": "1:1",
  "seed": 99
}
```

## 🧪 Test Lambda Function

### Test trong AWS Console

1. Vào **Lambda → Functions → aws_gen_pic**
2. Tab **Test** → Create new test event
3. Copy JSON mẫu ở trên
4. Click **Test**
5. Kiểm tra kết quả trong S3: `s3://gen-img-out1/outputs/`

### Test bằng AWS CLI

```bash
aws lambda invoke \
  --function-name aws_gen_pic \
  --payload '{"prompt":"a cyberpunk cat"}' \
  --region us-west-2 \
  response.json

cat response.json
```

## 🌐 Tích hợp API Gateway (Tuỳ chọn)

Để gọi Lambda qua HTTP API:

### Tạo HTTP API

1. Vào **API Gateway → Create API → HTTP API**
2. **Integrations**: Add integration → Lambda → `aws_gen_pic`
3. **Routes**: Configure route `POST /generate`
4. **Deploy** → Copy Invoke URL

### Test với cURL

```bash
curl -X POST https://abc123.execute-api.us-west-2.amazonaws.com/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a cat astronaut in space, realistic, 4k",
    "aspect_ratio": "16:9",
    "seed": 42
  }'
```

### CORS (cho Frontend)

Nếu gọi từ web app, enable CORS:

1. Trong API Gateway → **CORS**
2. Allowed origins: `*` (hoặc domain cụ thể)
3. Allowed methods: `POST, OPTIONS`

## 📊 Tham số hỗ trợ

| Tham số | Kiểu | Mặc định | Mô tả |
|---------|------|----------|-------|
| `prompt` | string | required | Mô tả ảnh muốn sinh |
| `aspect_ratio` | string | `"16:9"` | Tỷ lệ ảnh: `1:1`, `16:9`, `21:9`, `2:3`, `3:2`, `4:5`, `5:4`, `9:16`, `9:21` |
| `seed` | integer | `0` | Random seed (0 = random) |
| `model` | string | `stability.sd3-5-large-v1:0` | Model ID |
| `init_image_s3` | string | null | S3 path cho image-to-image |

## 💰 Chi phí ước tính

| Dịch vụ | Chi phí | Ghi chú |
|---------|---------|---------|
| **Bedrock SD3.5** | ~$0.01-0.05/ảnh | Theo độ phức tạp |
| **Lambda** | ~$0.00001/request | 512MB, 5s/request |
| **S3 Storage** | $0.023/GB/tháng | Rất thấp |
| **S3 Requests** | $0.0004/1000 PUT | Gần như free |

**Ví dụ**: 1000 ảnh/tháng ≈ **$10-50** (chủ yếu từ Bedrock)

### Tối ưu chi phí

- ✅ Set **S3 Lifecycle Policy** xóa ảnh sau 7-30 ngày
- ✅ Giảm `aspect_ratio` nếu không cần ảnh lớn
- ✅ Cache kết quả cho prompt giống nhau (dùng DynamoDB)
- ✅ Set Lambda timeout = 10s thay vì 15s

## 🔒 Bảo mật

### Best Practices

- ✅ Không để S3 public, dùng presigned URLs để chia sẻ
- ✅ Giới hạn rate limit với API Gateway
- ✅ Enable CloudWatch Logs để monitor
- ✅ Scan prompt để tránh nội dung không phù hợp
- ✅ Set resource-based policy cho Lambda

### Ví dụ Presigned URL

```python
# Tạo link download tạm thời (15 phút)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': OUTPUT_BUCKET, 'Key': key},
    ExpiresIn=900
)
```

## 🐛 Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `AccessDenied` | Thiếu quyền IAM | Kiểm tra IAM policy |
| `ModelNotFound` | Chưa enable model trong Bedrock | Enable model tại Bedrock console |
| `Timeout` | Lambda timeout | Tăng timeout lên 30s |
| `NoSuchBucket` | Bucket không tồn tại | Tạo bucket hoặc sửa tên |
| `InvalidImage` | Ảnh input lỗi | Kiểm tra format: JPEG/PNG |

## 📈 Monitoring & Logs

### CloudWatch Logs

```bash
# Xem logs gần nhất
aws logs tail /aws/lambda/aws_gen_pic --follow
```

### CloudWatch Metrics

- **Invocations**: Số lần gọi Lambda
- **Duration**: Thời gian xử lý
- **Errors**: Số lỗi
- **Throttles**: Số lần bị rate limit

### Tạo CloudWatch Alarm

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-gen-pic-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

## 🚀 Nâng cao

### 1. Frontend Integration (React)

```javascript
const generateImage = async (prompt) => {
  const response = await fetch('https://your-api.execute-api.us-west-2.amazonaws.com/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, aspect_ratio: '16:9' })
  });
  
  const data = await response.json();
  const imageUrl = await getPresignedUrl(data.bucket, data.key);
  return imageUrl;
};
```

### 2. Batch Processing

Sinh nhiều ảnh cùng lúc:

```python
# Dùng SQS Queue + Lambda event source
{
  "Records": [
    {"body": {"prompt": "prompt 1"}},
    {"body": {"prompt": "prompt 2"}}
  ]
}
```

### 3. Add DynamoDB Cache

Lưu metadata ảnh để tái sử dụng:

```python
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('image-cache')

# Save
table.put_item(Item={
    'prompt_hash': hash(prompt),
    's3_url': s3_url,
    'timestamp': timestamp
})
```

## 📚 Tài liệu tham khảo

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Stability AI SD3.5 Model Card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion-stability-sd3.html)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

## 🤝 Đóng góp

Contributions are welcome! Please:

1. Fork repo
2. Tạo feature branch: `git checkout -b feature/amazing`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing`
5. Tạo Pull Request

## 📄 License

MIT License - free to use for personal and commercial projects.

## 👨‍💻 Tác giả

**Khánh**

- Model: `stability.sd3-5-large-v1:0`
- Platform: AWS Lambda + Bedrock + S3
- Version: 1.0.0

---

