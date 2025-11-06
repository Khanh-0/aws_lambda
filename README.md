# 🎨 AWS Lambda + Amazon Bedrock - AI Image Generation with Prompt Enhancement

Hệ thống sinh ảnh AI sử dụng **Stability AI SD3.5** thông qua **Amazon Bedrock**, với tính năng **tự động tối ưu prompt** bằng **Amazon Nova Pro** trước khi sinh ảnh.

## ✨ Tính năng

- 🖼️ **Text-to-Image**: Sinh ảnh từ mô tả văn bản
- 🎨 **Image-to-Image**: Biến đổi ảnh có sẵn theo phong cách mới
- 🧠 **AI Prompt Enhancement**: Tự động cải thiện prompt bằng Nova Pro (tuỳ chọn)
- ☁️ **Serverless**: Không cần quản lý server, tự động scale
- 💾 **Auto Storage**: Tự động lưu ảnh lên S3
- 🚀 **Fast**: Xử lý trong vài giây
- 💰 **Cost-effective**: Chỉ trả tiền khi sử dụng

## 📋 Yêu cầu

- AWS Account với Bedrock đã được kích hoạt
- Region: `us-west-2` (Oregon)
- Models đã enable trong Bedrock:
  - `stability.sd3-5-large-v1:0` (sinh ảnh)
  - `amazon.nova-pro-v1:0` (tối ưu prompt)
- Quyền tạo: IAM Role, S3 Bucket, Lambda Function

## 🏗️ Kiến trúc hệ thống

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│   Client    │─────▶│ Lambda: Enhancer │─────▶│  Nova Pro   │
│ (API/Test)  │      │ (enhance_prompt) │      │  (LLM)      │
└─────────────┘      └────────┬─────────┘      └─────────────┘
                              │
                              │ Enhanced Prompt
                              ▼
                     ┌──────────────────┐      ┌─────────────┐
                     │ Lambda: GenImage │─────▶│  Bedrock    │
                     │ (aws_gen_pic)    │      │  SD3.5      │
                     └────────┬─────────┘      └─────────────┘
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

### Bước 2: Tạo IAM Role cho Lambda

1. Vào **AWS Console → IAM → Roles → Create role**
2. Chọn:
   - **Trusted entity type**: AWS service
   - **Use case**: Lambda
3. Attach policies:
   - `AWSLambdaBasicExecutionRole`
4. Thêm **Inline Policy** sau (cho cả 2 Lambda):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeModels",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-west-2::foundation-model/stability.sd3-5-large-v1:0",
        "arn:aws:bedrock:us-west-2::foundation-model/amazon.nova-pro-v1:0"
      ]
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
    },
    {
      "Sid": "LambdaInvoke",
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-west-2:*:function:aws_gen_pic"
    }
  ]
}
```

5. Đặt tên role: `lambda-bedrock-image-gen-role`

### Bước 3: Tạo Lambda Function #1 - Generate Image

1. Vào **AWS Console → Lambda → Create function**
2. Cấu hình:
   - **Function name**: `aws_gen_pic`
   - **Runtime**: Python 3.11
   - **Architecture**: x86_64
   - **Execution role**: Chọn role vừa tạo
3. **Configuration**:
   - **Timeout**: 30 seconds
   - **Memory**: 512 MB
4. **Environment variables**:

| Key | Value |
|-----|-------|
| `OUTPUT_BUCKET` | `gen-img-out1` |
| `INPUT_BUCKET` | `gen-img-input1` |

**Code cho Lambda #1** (`aws_gen_pic`):

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
        original_prompt = body.get("original_prompt")  # Track original if enhanced
        
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
        
        # Build response
        response_data = {
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
        }
        
        # Include original prompt if it was enhanced
        if original_prompt:
            response_data["original_prompt"] = original_prompt
            response_data["enhanced_prompt"] = prompt
        
        # Return success response
        return {
            "statusCode": 200,
            "body": json.dumps(response_data)
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

### Bước 4: Tạo Lambda Function #2 - Enhance Prompt

1. Vào **AWS Console → Lambda → Create function**
2. Cấu hình:
   - **Function name**: `enhance_prompt`
   - **Runtime**: Python 3.11
   - **Architecture**: x86_64
   - **Execution role**: Dùng chung role vừa tạo
3. **Configuration**:
   - **Timeout**: 30 seconds
   - **Memory**: 512 MB
4. **Environment variables**:

| Key | Value |
|-----|-------|
| `GEN_IMAGE_LAMBDA` | `aws_gen_pic` |

**Code cho Lambda #2** (`enhance_prompt`):

```python
import json
import boto3
import os

# Initialize AWS clients
bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")
lambda_client = boto3.client("lambda", region_name="us-west-2")

# Environment variables
GEN_IMAGE_LAMBDA = os.environ.get("GEN_IMAGE_LAMBDA", "aws_gen_pic")

# System prompt for Nova Pro to enhance image generation prompts
ENHANCEMENT_SYSTEM_PROMPT = """You are an expert at writing prompts for Stable Diffusion image generation models.

Your task is to transform user's simple prompts into detailed, high-quality prompts that will generate better images.

Guidelines:
- Keep the core concept from the original prompt
- Add artistic details: lighting, style, mood, quality descriptors
- Be specific about composition, camera angles, colors
- Include quality tags like: "highly detailed", "8k", "professional", "masterpiece"
- Keep it under 100 words
- Do NOT add unwanted elements the user didn't ask for
- Output ONLY the enhanced prompt, no explanations

Example transformations:
Input: "a cat"
Output: "a majestic orange tabby cat sitting on a windowsill, golden hour lighting, soft bokeh background, highly detailed fur texture, professional photography, 8k, warm tones"

Input: "cyberpunk city"
Output: "futuristic cyberpunk city at night, neon lights reflecting on wet streets, towering skyscrapers with holographic billboards, flying cars, cinematic composition, vibrant purple and blue color palette, highly detailed, 8k, ultra realistic"

Now enhance the user's prompt below."""

def enhance_prompt_with_nova(user_prompt):
    """
    Use Amazon Nova Pro to enhance the user's prompt
    """
    try:
        # Build request for Nova Pro (Converse API)
        request = {
            "modelId": "amazon.nova-pro-v1:0",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": user_prompt}
                    ]
                }
            ],
            "system": [
                {"text": ENHANCEMENT_SYSTEM_PROMPT}
            ],
            "inferenceConfig": {
                "maxTokens": 200,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        # Invoke Nova Pro using Converse API
        response = bedrock.converse(
            modelId="amazon.nova-pro-v1:0",
            messages=request["messages"],
            system=request["system"],
            inferenceConfig=request["inferenceConfig"]
        )
        
        # Extract enhanced prompt
        enhanced_prompt = response["output"]["message"]["content"][0]["text"].strip()
        
        return enhanced_prompt
    
    except Exception as e:
        print(f"Error enhancing prompt: {str(e)}")
        # Fallback to original prompt if enhancement fails
        return user_prompt

def lambda_handler(event, context):
    """
    Main handler: Enhance prompt with Nova Pro, then call image generation Lambda
    """
    try:
        # Parse request body
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        
        # Extract parameters
        original_prompt = body.get("prompt", "a beautiful landscape")
        enhance = body.get("enhance_prompt", True)  # Default: enable enhancement
        aspect_ratio = body.get("aspect_ratio", "16:9")
        seed = body.get("seed", 0)
        init_image_s3 = body.get("init_image_s3")
        
        # Step 1: Enhance prompt if requested
        if enhance:
            print(f"Original prompt: {original_prompt}")
            enhanced_prompt = enhance_prompt_with_nova(original_prompt)
            print(f"Enhanced prompt: {enhanced_prompt}")
        else:
            enhanced_prompt = original_prompt
        
        # Step 2: Build request for image generation Lambda
        gen_request = {
            "body": json.dumps({
                "prompt": enhanced_prompt,
                "aspect_ratio": aspect_ratio,
                "seed": seed,
                "init_image_s3": init_image_s3,
                "original_prompt": original_prompt if enhance else None
            })
        }
        
        # Step 3: Invoke image generation Lambda
        response = lambda_client.invoke(
            FunctionName=GEN_IMAGE_LAMBDA,
            InvocationType="RequestResponse",
            Payload=json.dumps(gen_request)
        )
        
        # Parse response from image generation Lambda
        response_payload = json.loads(response["Payload"].read())
        
        # Return combined response
        return {
            "statusCode": response_payload.get("statusCode", 200),
            "body": response_payload.get("body")
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Failed to enhance prompt and generate image"
            })
        }
```

## 📝 Cách sử dụng

### Option 1: Sinh ảnh KHÔNG cải thiện prompt

Gọi trực tiếp `aws_gen_pic`:

```json
{
  "prompt": "a cat",
  "aspect_ratio": "16:9",
  "seed": 42
}
```

### Option 2: Sinh ảnh CÓ cải thiện prompt ⭐ (Recommended)

Gọi `enhance_prompt` (sẽ tự động gọi `aws_gen_pic`):

```json
{
  "prompt": "a cat",
  "enhance_prompt": true,
  "aspect_ratio": "16:9",
  "seed": 42
}
```

**Response mẫu**:

```json
{
  "statusCode": 200,
  "body": {
    "message": "Image generated successfully",
    "s3_url": "s3://gen-img-out1/outputs/sd35_20251106_103022.jpeg",
    "filename": "sd35_20251106_103022.jpeg",
    "original_prompt": "a cat",
    "enhanced_prompt": "a majestic orange tabby cat sitting on a windowsill, golden hour lighting, soft bokeh background, highly detailed fur texture, professional photography, 8k, warm tones",
    "parameters": {
      "prompt": "a majestic orange tabby cat...",
      "model": "stability.sd3-5-large-v1:0",
      "aspect_ratio": "16:9",
      "seed": 42
    }
  }
}
```

### Option 3: Tắt tính năng cải thiện prompt

```json
{
  "prompt": "a detailed prompt you already wrote yourself",
  "enhance_prompt": false,
  "aspect_ratio": "1:1"
}
```

### Image-to-Image với Prompt Enhancement

```json
{
  "prompt": "make it look like a painting",
  "enhance_prompt": true,
  "init_image_s3": "s3://gen-img-input1/input.jpg",
  "aspect_ratio": "1:1"
}
```

## 🧪 Test Lambda Functions

### Test Lambda #2 (Enhance + Generate)

1. Vào **Lambda → enhance_prompt → Test**
2. Tạo test event:

```json
{
  "body": "{\"prompt\": \"a dragon\", \"enhance_prompt\": true}"
}
```

3. Click **Test** → xem logs để thấy prompt được cải thiện
4. Kiểm tra ảnh trong S3

### Test Lambda #1 (Direct Generate)

```json
{
  "body": "{\"prompt\": \"a detailed cyberpunk dragon with neon scales, 8k\"}"
}
```

## 🌐 Tích hợp API Gateway

### Tạo 2 Endpoints

1. **API Gateway → Create API → HTTP API**
2. Tạo 2 routes:

| Route | Lambda | Mô tả |
|-------|--------|-------|
| `POST /generate` | `aws_gen_pic` | Sinh ảnh trực tiếp |
| `POST /generate-enhanced` | `enhance_prompt` | Cải thiện prompt + sinh ảnh |

3. **Deploy** → Copy Invoke URL

### Test với cURL

**Endpoint thường**:
```bash
curl -X POST https://abc123.execute-api.us-west-2.amazonaws.com/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "detailed cyberpunk cat"}'
```

**Endpoint có AI enhancement** ⭐:
```bash
curl -X POST https://abc123.execute-api.us-west-2.amazonaws.com/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cat", "enhance_prompt": true}'
```

### Frontend Integration

```javascript
// React/Next.js example
const generateImage = async (userPrompt, useEnhancement = true) => {
  const endpoint = useEnhancement 
    ? 'https://your-api.com/generate-enhanced'
    : 'https://your-api.com/generate';
  
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: userPrompt,
      enhance_prompt: useEnhancement,
      aspect_ratio: '16:9'
    })
  });
  
  const data = await response.json();
  
  return {
    imageUrl: data.s3_url,
    originalPrompt: data.original_prompt,
    enhancedPrompt: data.enhanced_prompt
  };
};

// Usage
const result = await generateImage("a cat", true);
console.log("Original:", result.originalPrompt);
console.log("Enhanced:", result.enhancedPrompt);
```

## 📊 So sánh 2 Workflows

| Tính năng | Direct (`aws_gen_pic`) | Enhanced (`enhance_prompt`) |
|-----------|----------------------|--------------------------|
| **Prompt quality** | Phụ thuộc user | Tự động cải thiện ✨ |
| **Tốc độ** | Nhanh (~5s) | Chậm hơn (~8-10s) |
| **Chi phí** | Thấp | Cao hơn ~$0.01/request |
| **Use case** | Prompt đã tốt | Prompt đơn giản |
| **Output quality** | Tốt | Xuất sắc ⭐ |

## 💰 Chi phí ước tính

| Dịch vụ | Không Enhancement | Có Enhancement |
|---------|-------------------|----------------|
| **Nova Pro LLM** | $0 | ~$0.01/request |
| **Bedrock SD3.5** | ~$0.03/ảnh | ~$0.03/ảnh |
| **Lambda** | ~$0.00001 | ~$0.00002 |
| **Tổng/ảnh** | **~$0.03** | **~$0.04** |

**Ví dụ**: 1000 ảnh/tháng với enhancement ≈ **$40**

## 🎨 Ví dụ Prompt Enhancement

### Example 1: Simple → Detailed

| Original | Enhanced by Nova Pro |
|----------|---------------------|
| "a house" | "a cozy two-story Victorian house with a white picket fence, surrounded by blooming rose gardens, warm sunset lighting, autumn season, highly detailed architecture, professional real estate photography, 8k, inviting atmosphere" |

### Example 2: Basic → Cinematic

| Original | Enhanced by Nova Pro |
|----------|---------------------|
| "space battle" | "epic space battle scene with massive starships exchanging laser fire, explosions lighting up the cosmos, debris floating in zero gravity, cinematic wide angle shot, dramatic lighting from nearby star, highly detailed spacecraft, 8k, Blade Runner meets Star Wars aesthetic" |

### Example 3: Character → Professional

| Original | Enhanced by Nova Pro |
|----------|---------------------|
| "a warrior" | "a battle-hardened female warrior with intricate armor, holding a glowing sword, standing on a cliff overlooking a fantasy landscape, dramatic storm clouds, volumetric lighting, dynamic pose, highly detailed textures, fantasy art style, 8k, heroic composition" |

## 🔧 Tuning System Prompt

Bạn có thể chỉnh `ENHANCEMENT_SYSTEM_PROMPT` trong `enhance_prompt` Lambda để thay đổi style:

### Style 1: Photography Focus

```python
ENHANCEMENT_SYSTEM_PROMPT = """You enhance prompts for photorealistic images.
Add: camera settings, lighting, lens type, photography style.
Example: "portrait of a woman" → "portrait of a woman, 85mm lens, f/1.4, natural window lighting, soft focus background, professional headshot, sharp details on eyes, warm color grading, editorial photography style"
"""
```

### Style 2: Artistic Focus

```python
ENHANCEMENT_SYSTEM_PROMPT = """You enhance prompts for artistic, painterly images.
Add: art style, medium, famous artists' techniques, color palette.
Example: "mountain" → "majestic mountain landscape in the style of Albert Bierstadt, oil painting technique, dramatic lighting with god rays, romantic era composition, rich earth tones with vibrant sky, highly detailed brushwork, masterpiece quality"
"""
```

### Style 3: Minimal Enhancement

```python
ENHANCEMENT_SYSTEM_PROMPT = """Add only essential quality tags.
Keep user's original concept 100% unchanged.
Add only: "highly detailed, 8k, professional"
"""
```

## 🐛 Troubleshooting

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `Model not found: nova-pro` | Chưa enable Nova Pro | Enable tại Bedrock console |
| `Lambda timeout` | Nova Pro + SD3.5 chậm | Tăng timeout lên 60s |
| `Invoke Lambda permission denied` | Thiếu quyền `lambda:InvokeFunction` | Thêm vào IAM policy |
| `Enhanced prompt too long` | Nova Pro xuất quá dài | Giảm `maxTokens` xuống 150 |

## 📈 Monitoring

### CloudWatch Logs

```bash
# Xem logs Lambda #1
aws logs tail /aws/lambda/aws_gen_pic --follow

# Xem logs Lambda #2 (có prompt enhancement)
aws logs tail /aws/lambda/enhance_prompt --follow
```

### Custom Metrics

Thêm vào Lambda để track:

```python
import boto3
cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='ImageGeneration',
    MetricData=[{
        'MetricName': 'PromptEnhancementTime',
        'Value': enhancement_duration,
        'Unit': 'Seconds'
    }]
)
```

## 🚀 Nâng cao

### 1. A/B Testing: Enhanced vs Non-Enhanced

```python
import random

def lambda_handler(event, context):
    # 50% traffic gets enhancement
    use_enhancement = random.choice([True, False])
    
    # Track in DynamoDB for comparison
    save_ab_test_result(use_enhancement, image_url, user_feedback)
```

### 2. Caching Enhanced Prompts

```python
import hashlib

def get_cached_enhancement(original_prompt):
    cache_key = hashlib.md5(original_prompt.encode()).hexdigest()
    
    # Check DynamoDB cache
    cached = dynamodb_table.get_item(Key={'prompt_hash': cache_key})
    
    if cached:
        return cached['enhanced_prompt']
    
    # If not cached, enhance and save
    enhanced = enhance_prompt_with_nova(original_prompt)
    dynamodb_table.put_item(Item={
        'prompt_hash': cache_key,
        'original': original_prompt,
        'enhanced': enhanced,
        'timestamp': datetime.now().isoformat()
    })
    
    return enhanced
```

### 3. Multiple Enhancement Styles

```json
{
  "prompt": "a cat",
  "enhance_prompt": true,
  "enhancement_style": "photorealistic",
  "styles": ["cinematic", "artistic", "photorealistic", "anime"]
}
```

## 📚 Tài liệu tham khảo

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Amazon Nova Pro Model](https://aws.amazon.com/bedrock/nova/)
- [Stability AI SD3.5 Model Card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion-stability-sd3.html)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

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

- Models: 
  - `amazon.nova-pro-v1:0` (Prompt Enhancement)
  - `stability.sd3-5-large-v1:0` (Image Generation)
- Platform: AWS Lambda + Bedrock + S3
- Version: 2.0.0

---

⭐ Nếu project này hữu ích, hãy cho một star nhé!
