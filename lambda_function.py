import json
import boto3
import base64

bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")
# ====================== MODEL ID MẶC ĐỊNH ======================
MODEL_PROMPT_ENHANCER = "anthropic.claude-3-haiku-20240307-v1:0"
MODEL_IMAGE_GEN = "stability.sd3-5-large-v1:0"


def lambda_handler(event, context):
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        # ================== 🔧 CẤU HÌNH NGƯỜI DÙNG ==================
        prompt = body.get("prompt", "")
        regen_prompt = body.get("regen_prompt", True)
        mode = body.get("mode", "text2img")
        aspect_ratio = body.get("aspect_ratio", "1:1")
        strength = body.get("strength", 0.7)
        model_id = body.get("model_id", MODEL_IMAGE_GEN)
        prompt_language = body.get("prompt_language", "en")

        init_image_b64 = body.get("init_image", None)

        if not prompt:
            return _response(400, {"error": "Missing prompt"})

        # ================== TỐI ƯU PROMPT ==================
        enhanced_prompt = prompt

        if regen_prompt:
            prompt_enhance_text = (
                f"""You are a professional AI prompt engineer.
Please rewrite the following {prompt_language.upper()} prompt
into the best possible English version for an AI image generation model.
Make it rich in visual details and cinematic tone.

Original prompt: {prompt}
"""
            )

            # CẤU TRÚC CHUẨN CHO CONVERSE API
            content_items = [{"text": prompt_enhance_text}]

            # Nếu có ảnh, thêm vào content với format chuẩn
            if init_image_b64:
                content_items.append({
                    "image": {
                        "format": "png",
                        "source": {
                            "bytes": base64.b64decode(init_image_b64)
                        }
                    }
                })

            # DÙNG CONVERSE API
            try:
                nova_response = bedrock.converse(
                    modelId=MODEL_PROMPT_ENHANCER,
                    messages=[
                        {
                            "role": "user",
                            "content": content_items
                        }
                    ],
                    inferenceConfig={
                        "maxTokens": 400,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                )

                # Lấy kết quả từ converse API
                enhanced_prompt = nova_response["output"]["message"]["content"][0]["text"]

            except Exception as nova_error:
                # Fallback: nếu converse fail, dùng invoke_model
                print(f"Converse API failed, using invoke_model: {str(nova_error)}")
                nova_payload = {
                    "messages": [
                        {
                            "role": "user",
                            "content": content_items
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": 400,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                }
                nova_response = bedrock.invoke_model(
                    modelId=MODEL_PROMPT_ENHANCER,
                    body=json.dumps(nova_payload),
                    contentType="application/json",
                    accept="application/json"
                )
                nova_result = json.loads(nova_response["body"].read())
                enhanced_prompt = nova_result.get("output", {}).get("message", {}).get("content", [{}])[0].get("text",
                                                                                                               prompt)

        # ================== SINH ẢNH ==================
        payload = {
            "prompt": enhanced_prompt,
            "output_format": "png"
            # "aspect_ratio": aspect_ratio,
        }

        # Xử lý mode sinh ảnh
        if mode == "img2img":
            if not init_image_b64:
                return _response(400, {"error": "img2img mode requires init_image"})
            payload["mode"] = "image-to-image"
            payload["image"] = init_image_b64
            payload["strength"] = strength
        else:
            payload["mode"] = "text-to-image"
            payload["aspect_ratio"] = aspect_ratio

        # Gọi model sinh ảnh
        image_response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json"
        )

        result = json.loads(image_response["body"].read())
        base64_image = result.get("images", [None])[0] or result.get("artifacts", [{}])[0].get("base64")

        if not base64_image:
            return _response(500, {"error": "Model did not return image"})

        # ==================KẾT QUẢ ==================
        return _response(200, {
            "message": "Image generated successfully",
            "enhanced_prompt": enhanced_prompt,
            "config_used": {
                "mode": mode,
                "regen_prompt": regen_prompt,
                "model_id": model_id,
                "aspect_ratio": aspect_ratio,
                "strength": strength,
                "prompt_language": prompt_language
            },
            "image_base64": base64_image
        })

    except Exception as e:
        import traceback
        return _response(500, {
            "error": str(e),
            "traceback": traceback.format_exc()
        })


# ================== HÀM HỖ TRỢ ==================
def _response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }
