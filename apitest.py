import requests
import json
import base64
from PIL import Image
from io import BytesIO
import os

# ================== HELPER FUNCTIONS ==================
def log_prompt_info(prompt, model_name="Claude"):
    print(f"💡 {model_name} model note: Prompt may be truncated if > 512 tokens")
    print(f"📜 Prompt length: {len(prompt)} characters")

def resize_for_titan(img: Image.Image, target_ratio="1:1"):
    """
    Titan yêu cầu: width/height chia hết cho 64, trong khoảng 512-2048
    """
    ratio_map = {
        "1:1": (1024, 1024),
        "16:9": (1173, 640),
        "3:2": (1152, 768),
        "3:5": (768, 1280),
    }
    width, height = ratio_map.get(target_ratio, (1024, 1024))
    width = min(max(512, width - width % 64), 2048)
    height = min(max(512, height - height % 64), 2048)
    resized_img = img.resize((width, height))
    return resized_img, width, height

def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        return base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        print(f"❌ Lỗi đọc ảnh: {str(e)}")
        return None

def save_image(base64_str, filename):
    try:
        img_data = base64.b64decode(base64_str)
        img = Image.open(BytesIO(img_data))
        os.makedirs("output", exist_ok=True)
        path = f"output/{filename}"
        img.save(path)
        print(f"✅ Saved image: {path} ({img.width}x{img.height})")
        return path
    except Exception as e:
        print(f"❌ Lỗi lưu ảnh: {str(e)}")
        return None

# ================== MAIN TESTER CLASS ==================
class TitanImageGenTester:
    def __init__(self, api_url):
        self.api_url = api_url
        self.results = []

    def test_request(self, test_name, payload, expected_status=200):
        print("\n" + "="*60)
        print(f"🧪 TEST: {test_name}")
        print("="*60)

        # Ghi chú Claude token limit nếu có regen_prompt
        if payload.get("regen_prompt", False):
            prompt = ""
            if payload.get("mode") == "text2img":
                prompt = payload.get("prompt", "")
            elif payload.get("mode") == "img2img":
                prompt = payload.get("prompt", "")
            if prompt:
                log_prompt_info(prompt, "Claude")

        # Display payload (ẩn base64)
        display_payload = {
            k: (f"[BASE64_IMAGE - {len(v)//1024}KB]" if k in ["init_image", "images"] and v else v)
            for k,v in payload.items()
        }
        print(f"📤 Payload:\n{json.dumps(display_payload, indent=2, ensure_ascii=False)}")

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type":"application/json"},
                timeout=120
            )
            print(f"📊 Status Code: {response.status_code}")
            
            try:
                data = response.json()
                print(f"📥 Response:\n{json.dumps({k:v for k,v in data.items() if k != 'image_base64'}, indent=2, ensure_ascii=False)}")
            except:
                data = {"error":"Cannot parse JSON", "raw": response.text[:300]}
                print(f"📥 Response: {data}")

            if response.status_code == expected_status:
                if expected_status == 200 and data.get("image_base64"):
                    filename = f"{test_name.replace(' ', '_').lower()}.png"
                    save_image(data["image_base64"], filename)
                print(f"✅ PASS")
                self.results.append({"test": test_name, "status":"PASS", "response":data})
                return True
            else:
                print(f"❌ FAIL: Expected {expected_status}, got {response.status_code}")
                print(f"Error details: {data}")
                self.results.append({"test": test_name, "status":"FAIL", "error":data})
                return False

        except Exception as e:
            print(f"⚠️ EXCEPTION: {str(e)}")
            self.results.append({"test": test_name, "status":"ERROR", "error":str(e)})
            return False

    def run_all_tests(self, init_image_path=None):
        print("\n🚀 BẮT ĐẦU TESTING TITAN IMAGE GENERATOR G1 V2")
        
        # ================== TEXT2IMG ==================
        print("\n" + "="*60)
        print("📝 TEXT TO IMAGE TESTS")
        print("="*60)
        
        self.test_request(
            "Test-1-Text2Img-Basic-Enhancement",
            {
                "prompt": "a beautiful sunset over mountains",
                "regen_prompt": True,
                "mode": "text2img",
                "aspect_ratio": "16:9"
            }
        )
        
        self.test_request(
            "Test-2-Text2Img-No-Enhancement",
            {
                "prompt": "a futuristic city with flying cars, neon lights, cyberpunk style, 8k, ultra detailed",
                "regen_prompt": False,
                "mode": "text2img",
                "aspect_ratio": "1:1"
            }
        )
        
        self.test_request(
            "Test-3-Text2Img-Vietnamese",
            {
                "prompt": "một cô gái áo dài đang đi trên cầu Nhật Bản, hoàng hôn đẹp",
                "regen_prompt": True,
                "mode": "text2img",
                "prompt_language": "vi",
                "aspect_ratio": "9:16"
            }
        )

        # ================== IMG2IMG ==================
        if init_image_path and os.path.exists(init_image_path):
            print("\n" + "="*60)
            print("🖼️ IMAGE TO IMAGE TESTS (FIXED)")
            print("="*60)
            
            init_b64 = image_to_base64(init_image_path)
            if not init_b64:
                print("❌ Không thể load init image, bỏ qua img2img tests")
            else:
                img = Image.open(init_image_path)
                
                # Test với 1:1
                resized_img, width, height = resize_for_titan(img, "1:1")
                buf = BytesIO()
                resized_img.save(buf, format="PNG")
                init_b64_resized = base64.b64encode(buf.getvalue()).decode("utf-8")

                # ✅ Test-5: Low Similarity (giống ảnh gốc)
                self.test_request(
                    "Test-5-Img2Img-Low-Similarity-Watercolor",
                    {
                        "prompt": "turn this into a watercolor painting",
                        "negative_prompt": "blurry, low quality, distorted, watermark, text, ugly, deformed",
                        "regen_prompt": True,
                        "mode": "img2img",
                        "init_image": init_b64_resized,
                        "similarity_strength": 0.7,  # ✅ ĐÚNG tên tham số
                        "aspect_ratio": "1:1"
                    }
                )

                # ✅ Test-6: High Similarity (khác ảnh gốc nhiều)
                self.test_request(
                    "Test-6-Img2Img-High-Similarity-Comic",
                    {
                        "prompt": "make it look like a comic book illustration, bold colors",
                        "negative_prompt": "blurry, low quality, distorted, watermark, text, ugly, deformed",
                        "regen_prompt": True,
                        "mode": "img2img",
                        "init_image": init_b64_resized,
                        "similarity_strength": 0.3,  # ✅ Giá trị thấp = khác nhiều
                        "aspect_ratio": "1:1"
                    }
                )

                # ✅ Test-7: Với Negative Prompt
                self.test_request(
                    "Test-7-Img2Img-With-Negative-Prompt",
                    {
                        "prompt": "professional portrait photo, studio lighting, high quality",
                        "negative_prompt": "blurry, low quality, distorted, watermark, text, ugly, deformed",
                        "regen_prompt": True,
                        "mode": "img2img",
                        "init_image": init_b64_resized,
                        "similarity_strength": 0.5,
                        "aspect_ratio": "1:1"
                    }
                )

                # ✅ Test-8: Aspect ratio khác (16:9)
                resized_img_16_9, width_16_9, height_16_9 = resize_for_titan(img, "16:9")
                buf_16_9 = BytesIO()
                resized_img_16_9.save(buf_16_9, format="PNG")
                init_b64_16_9 = base64.b64encode(buf_16_9.getvalue()).decode("utf-8")

                self.test_request(
                    "Test-8-Img2Img-Aspect-16-9",
                    {
                        "prompt": "epic cinematic landscape, dramatic lighting",
                        "negative_prompt": "blurry, low quality, distorted, watermark, text, ugly, deformed",
                        "regen_prompt": True,
                        "mode": "img2img",
                        "init_image": init_b64_16_9,
                        "similarity_strength": 0.6,
                        "aspect_ratio": "16:9"
                    }
                )

        # ================== ERROR HANDLING ==================
        print("\n" + "="*60)
        print("🚨 ERROR HANDLING TESTS")
        print("="*60)
        
        self.test_request(
            "Test-11-Error-Missing-Prompt",
            {
                "regen_prompt": True,
                "mode": "text2img"
            },
            expected_status=400
        )
        
        self.test_request(
            "Test-12-Error-Invalid-Mode",
            {
                "prompt": "test",
                "mode": "invalid_mode"
            },
            expected_status=400
        )

    def print_summary(self):
        print("\n" + "="*60)
        print("📊 KẾT QUẢ TỔNG HỢP")
        print("="*60)
        
        passed = sum(1 for r in self.results if r["status"]=="PASS")
        failed = sum(1 for r in self.results if r["status"]=="FAIL")
        errors = sum(1 for r in self.results if r["status"]=="ERROR")
        total = len(self.results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {failed}/{total}")
        print(f"⚠️ Errors: {errors}/{total}")
        
        if failed > 0 or errors > 0:
            print("\n" + "="*60)
            print("❌ FAILED/ERROR TESTS:")
            print("="*60)
            for r in self.results:
                if r["status"] in ["FAIL", "ERROR"]:
                    print(f"\n{r['test']}:")
                    print(f"  Status: {r['status']}")
                    if "error" in r:
                        print(f"  Error: {json.dumps(r['error'], indent=4, ensure_ascii=False)}")

# ================== MAIN ==================
if __name__ == "__main__":
    API_URL = ""
    
    print("="*60)
    print("🎨 TITAN IMAGE GENERATOR G1 V2 - API TESTER")
    print("="*60)
    print(f"API Endpoint: {API_URL}")
    
    tester = TitanImageGenTester(API_URL)
    
    # Thay đổi đường dẫn ảnh test của bạn ở đây
    INIT_IMAGE_PATH = r"C:\Users\leamo\Downloads\aaaa.jpg"
    
    if os.path.exists(INIT_IMAGE_PATH):
        print(f"✅ Init image found: {INIT_IMAGE_PATH}")
    else:
        print(f"⚠️ Init image not found: {INIT_IMAGE_PATH}")
        print("   IMG2IMG tests will be skipped")
    
    tester.run_all_tests(init_image_path=INIT_IMAGE_PATH)
    tester.print_summary()
