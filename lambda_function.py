import json
import boto3
import base64

bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")

# ====================== MODEL ID ======================
MODEL_PROMPT_ENHANCER = "anthropic.claude-3-haiku-20240307-v1:0"
MODEL_IMAGE_GEN = "stability.sd3-5-large-v1:0"
MODEL_TITAN_IMG2IMG = "amazon.titan-image-generator-v2:0"


def lambda_handler(event, context):
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        # ================== INPUT ==================
        prompt = body.get("prompt", "")
        negative_prompt = body.get("negative_prompt", "")
        regen_prompt = body.get("regen_prompt", True)
        mode = body.get("mode", "text2img")
        aspect_ratio = body.get("aspect_ratio", "1:1")
        strength = body.get("strength", 0.7)
        model_id = body.get("model_id", MODEL_IMAGE_GEN)
        prompt_language = body.get("prompt_language", "en")
        init_image_b64 = body.get("init_image")

        if not prompt:
            return _response(400, {"error": "Missing prompt"})

        # ================== PROMPT ENHANCE ==================
        enhanced_prompt = prompt

        if regen_prompt:
            prompt_enhance_text = f"""
You are an advanced AI specialized in visual analysis and professional prompt engineering.
Reply within 300 characters only.

Rewrite the following {prompt_language.upper()} prompt into the best possible English version.

Original Prompt:
{prompt}
"""

            content_items = [{"text": prompt_enhance_text}]
            if init_image_b64:
                content_items.append({
                    "image": {
                        "format": "png",
                        "source": {"bytes": base64.b64decode(init_image_b64)}
                    }
                })

            try:
                nova_response = bedrock.converse(
                    modelId=MODEL_PROMPT_ENHANCER,
                    messages=[{"role": "user", "content": content_items}],
                    inferenceConfig={"maxTokens": 400, "temperature": 0.7, "topP": 0.9}
                )
                enhanced_prompt = nova_response["output"]["message"]["content"][0]["text"]

            except Exception:
                fallback = bedrock.invoke_model(
                    modelId=MODEL_PROMPT_ENHANCER,
                    body=json.dumps({
                        "messages": [{"role": "user", "content": content_items}],
                        "inferenceConfig": {"maxTokens": 400}
                    })
                )
                enhanced_prompt = json.loads(fallback["body"].read()).get(
                    "output", {}
                ).get("message", {}).get("content", [{}])[0].get("text", prompt)

        # ================== IMAGE GENERATION ==================
        config_used = {
            "mode": mode,
            "aspect_ratio": aspect_ratio,
            "strength": strength,
            "model_id": model_id,
        }
        base64_image = None

        # -------------------------------------------------------
        # ================== 🔥 AMAZON TITAN IMG2IMG FIXED 🔥
        if mode == "img2img":
            similarity_strength = max(0.2, min(1.0, body.get("similarity_strength", strength)))
            if not init_image_b64:
                return _response(400, {"error": "img2img requires init_image"})

            width, height = _parse_aspect_ratio(aspect_ratio)

            titan_payload = {
                "taskType": "IMAGE_VARIATION",
                "imageVariationParams": {
                    "text": enhanced_prompt,
                    "negativeText": negative_prompt or "",
                    "images": [init_image_b64],            # ✅ sửa: dùng list base64 string
                    "similarityStrength": similarity_strength  # ✅ sửa: đúng key Titan
                },
                "imageGenerationConfig": {
                    "cfgScale": 8.0,
                    "seed": 42,
                    "width": width,
                    "height": height,
                    "numberOfImages": 1
                }
            }

            titan_response = bedrock.invoke_model(
                modelId=MODEL_TITAN_IMG2IMG,
                body=json.dumps(titan_payload),
                contentType="application/json",
                accept="application/json"
            )

            data = json.loads(titan_response["body"].read())
            base64_image = data.get("images", [None])[0]
            
            if base64_image:
                # ✅ decode base64 trước khi trả về
                image_bytes = base64.b64decode(base64_image)
            else:
                return _response(500, {"error": "Titan model did not return image"})

            config_used["titan_width"] = width
            config_used["titan_height"] = height
            config_used["sigma"] = similarity_strength


        else:
            # ============= Stable Diffusion TEXT2IMG giữ nguyên ==================
            payload = {
                "prompt": enhanced_prompt,
                "output_format": "png",
                "mode": "text-to-image",
                "aspect_ratio": aspect_ratio
            }

            sd_response = bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json"
            )

            result = json.loads(sd_response["body"].read())
            base64_image = result.get("images", [None])[0] or \
                           result.get("artifacts", [{}])[0].get("base64")

        if not base64_image:
            return _response(500, {"error": "Model did not return image"})

        return _response(200, {
            "message": "Image generated successfully",
            "enhanced_prompt": enhanced_prompt,
            "config_used": config_used,
            "image_base64": base64_image
        })

    except Exception as e:
        import traceback
        return _response(500, {"error": str(e), "trace": traceback.format_exc()})


# ================== SUPPORT ==================
def _response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }


# ================== ✔ NEW TITAN ASPECT RATIO TABLE ==================
def _parse_aspect_ratio(ar):
    titan_map = {
        "1:1": (1024, 1024),
        "768": (768, 768),  # fallback
        "16:9": (1173, 640),
        "9:16": (640, 1173),
        "2:3": (768, 1152),
        "3:2": (1152, 768),
        "3:5": (768, 1280),
        "5:3": (1280, 768),
        "7:9": (896, 1152),
        "9:7": (1152, 896),
        "6:11": (768, 1408),
        "11:6": (1408, 768),
        "5:11": (640, 1408),
        "11:5": (1408, 640),
        "9:5": (1152, 640),
        "16:9_wide": (1173, 640),
        "16:9_tall": (640, 1173),
    }

    return titan_map.get(ar, (1024, 1024))
