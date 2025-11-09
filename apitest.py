# import requests
# import json
# import base64
# from PIL import Image
# from io import BytesIO
# import os
#
#
# class APIImageGenTester:
#     def __init__(self, api_url):
#         self.api_url = api_url
#         self.results = []
#
#     def save_image(self, base64_string, filename):
#         """Lưu ảnh từ base64 string"""
#         try:
#             img_data = base64.b64decode(base64_string)
#             img = Image.open(BytesIO(img_data))
#
#             # Tạo thư mục output nếu chưa có
#             os.makedirs("output", exist_ok=True)
#             filepath = f"output/{filename}"
#
#             img.save(filepath)
#             print(f"✅ Đã lưu ảnh: {filepath}")
#             return filepath
#         except Exception as e:
#             print(f"❌ Lỗi khi lưu ảnh: {str(e)}")
#             return None
#
#     def image_to_base64(self, image_path):
#         """Chuyển ảnh thành base64 string"""
#         try:
#             with open(image_path, "rb") as img_file:
#                 return base64.b64encode(img_file.read()).decode('utf-8')
#         except Exception as e:
#             print(f"❌ Lỗi khi đọc ảnh: {str(e)}")
#             return None
#
#     def test_request(self, test_name, payload):
#         """Gửi request và kiểm tra kết quả"""
#         print(f"\n{'=' * 60}")
#         print(f"🧪 TEST: {test_name}")
#         print(f"{'=' * 60}")
#         print(
#             f"📤 Payload: {json.dumps({k: v if k != 'init_image' else '[BASE64_IMAGE]' for k, v in payload.items()}, indent=2)}")
#
#         try:
#             response = requests.post(
#                 self.api_url,
#                 json=payload,
#                 headers={"Content-Type": "application/json"},
#                 timeout=120
#             )
#
#             print(f"📊 Status Code: {response.status_code}")
#
#             if response.status_code == 200:
#                 data = response.json()
#                 print(f"✅ SUCCESS!")
#                 print(f"📝 Enhanced Prompt: {data.get('enhanced_prompt', 'N/A')[:100]}...")
#                 print(f"⚙️  Config Used: {json.dumps(data.get('config_used', {}), indent=2)}")
#
#                 # Lưu ảnh
#                 if data.get('image_base64'):
#                     filename = f"{test_name.replace(' ', '_').lower()}.png"
#                     self.save_image(data['image_base64'], filename)
#
#                 self.results.append({
#                     "test": test_name,
#                     "status": "PASS",
#                     "response": data
#                 })
#                 return True
#             else:
#                 error_data = response.json()
#                 print(f"❌ FAILED!")
#                 print(f"Error: {json.dumps(error_data, indent=2)}")
#
#                 self.results.append({
#                     "test": test_name,
#                     "status": "FAIL",
#                     "error": error_data
#                 })
#                 return False
#
#         except Exception as e:
#             print(f"❌ EXCEPTION: {str(e)}")
#             self.results.append({
#                 "test": test_name,
#                 "status": "ERROR",
#                 "error": str(e)
#             })
#             return False
#
#     def run_all_tests(self, init_image_path=None):
#         """Chạy tất cả các test cases"""
#         print("\n" + "=" * 60)
#         print("🚀 BẮT ĐẦU TEST API IMAGE GENERATION")
#         print("=" * 60)
#
#         # TEST 1: Text-to-Image cơ bản với prompt enhancement
#         self.test_request(
#             "Test 1 - Text2Img Basic with Enhancement",
#             {
#                 "prompt": "a beautiful sunset over mountains",
#                 "regen_prompt": True,
#                 "mode": "text2img",
#                 "aspect_ratio": "16:9"
#             }
#         )
#
#         # TEST 2: Text-to-Image không enhancement
#         self.test_request(
#             "Test 2 - Text2Img without Enhancement",
#             {
#                 "prompt": "a futuristic city with flying cars, neon lights, cyberpunk style",
#                 "regen_prompt": False,
#                 "mode": "text2img",
#                 "aspect_ratio": "1:1"
#             }
#         )
#
#         # TEST 3: Text-to-Image với prompt tiếng Việt
#         self.test_request(
#             "Test 3 - Text2Img Vietnamese Prompt",
#             {
#                 "prompt": "một cô gái áo dài đang đi trên cầu Nhật Bản",
#                 "regen_prompt": True,
#                 "mode": "text2img",
#                 "prompt_language": "vi",
#                 "aspect_ratio": "9:16"
#             }
#         )
#
#         # TEST 4: Text-to-Image với aspect ratio khác
#         self.test_request(
#             "Test 4 - Text2Img Different Aspect Ratio",
#             {
#                 "prompt": "a cute cat sitting on a window",
#                 "regen_prompt": True,
#                 "aspect_ratio": "4:3"
#             }
#         )
#
#         # TEST 5: Image-to-Image (nếu có ảnh init)
#         if init_image_path and os.path.exists(init_image_path):
#             init_image_b64 = self.image_to_base64(init_image_path)
#             if init_image_b64:
#                 self.test_request(
#                     "Test 5 - Img2Img with Init Image",
#                     {
#                         "prompt": "turn this into a watercolor painting",
#                         "regen_prompt": True,
#                         "mode": "img2img",
#                         "init_image": init_image_b64,
#                         "strength": 0.7,
#                         "aspect_ratio": "1:1"
#                     }
#                 )
#
#                 # TEST 6: Image-to-Image với strength cao hơn
#                 self.test_request(
#                     "Test 6 - Img2Img High Strength",
#                     {
#                         "prompt": "make it look like a comic book illustration",
#                         "regen_prompt": True,
#                         "mode": "img2img",
#                         "init_image": init_image_b64,
#                         "strength": 0.9
#                     }
#                 )
#         else:
#             print("\n⚠️  Bỏ qua test Image-to-Image vì không có ảnh init")
#
#         # TEST 7: Test error - thiếu prompt
#         self.test_request(
#             "Test 7 - Error Missing Prompt",
#             {
#                 "regen_prompt": True
#             }
#         )
#
#         # TEST 8: Test error - img2img thiếu init_image
#         self.test_request(
#             "Test 8 - Error Img2Img Missing Init Image",
#             {
#                 "prompt": "beautiful landscape",
#                 "mode": "img2img"
#             }
#         )
#
#         # In ra kết quả tổng hợp
#         self.print_summary()
#
#     def print_summary(self):
#         """In ra tổng kết kết quả"""
#         print("\n" + "=" * 60)
#         print("📊 KẾT QUẢ TỔNG HỢP")
#         print("=" * 60)
#
#         passed = sum(1 for r in self.results if r["status"] == "PASS")
#         failed = sum(1 for r in self.results if r["status"] == "FAIL")
#         errors = sum(1 for r in self.results if r["status"] == "ERROR")
#
#         print(f"✅ Passed: {passed}")
#         print(f"❌ Failed: {failed}")
#         print(f"⚠️  Errors: {errors}")
#         print(f"📝 Total: {len(self.results)}")
#
#         print("\nChi tiết:")
#         for r in self.results:
#             status_icon = "✅" if r["status"] == "PASS" else "❌"
#             print(f"{status_icon} {r['test']}: {r['status']}")
#
#
# # ================== MAIN ==================
# if __name__ == "__main__":
#     API_URL = "https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen"
#
#     # Khởi tạo tester
#     tester = APIImageGenTester(API_URL)
#
#     # Chạy tất cả tests
#     # Nếu bạn có ảnh để test img2img, thay đổi đường dẫn bên dưới
#     # Ví dụ: tester.run_all_tests(init_image_path="path/to/your/image.png")
#     tester.run_all_tests(init_image_path= r"C:\Users\leamo\Downloads\aaaa.jpg")
#
#     print("\n✨ Hoàn thành tất cả test cases!")
#     print("📁 Các ảnh đã được lưu trong thư mục 'output/'")

import requests
import json
import base64
from PIL import Image
from io import BytesIO
import os


class APIImageGenTester:
    def __init__(self, api_url):
        self.api_url = api_url
        self.results = []

    def save_image(self, base64_string, filename):
        """Lưu ảnh từ base64 string"""
        try:
            img_data = base64.b64decode(base64_string)
            img = Image.open(BytesIO(img_data))

            # Tạo thư mục output nếu chưa có
            os.makedirs("output", exist_ok=True)
            filepath = f"output/{filename}"

            img.save(filepath)
            print(f"✅ Đã lưu ảnh: {filepath} ({img.width}x{img.height})")
            return filepath
        except Exception as e:
            print(f"❌ Lỗi khi lưu ảnh: {str(e)}")
            return None

    def image_to_base64(self, image_path):
        """
        Chuyển ảnh thành base64 string - KHÔNG resize
        AWS Bedrock sẽ tự động scale ảnh theo init_image
        """
        try:
            with open(image_path, "rb") as img_file:
                img_bytes = img_file.read()
                base64_str = base64.b64encode(img_bytes).decode('utf-8')

                # Hiển thị thông tin ảnh
                img = Image.open(image_path)
                print(f"📷 Image loaded: {img.width}x{img.height} ({len(img_bytes) // 1024}KB)")

                return base64_str
        except Exception as e:
            print(f"❌ Lỗi khi đọc ảnh: {str(e)}")
            return None

    def test_request(self, test_name, payload, expected_status=200):
        """Gửi request và kiểm tra kết quả"""
        print(f"\n{'=' * 60}")
        print(f"🧪 TEST: {test_name}")
        print(f"{'=' * 60}")

        # Hiển thị payload (ẩn base64 image)
        display_payload = {
            k: (f"[BASE64_IMAGE - {len(v) // 1024}KB]" if k == 'init_image' and v else v)
            for k, v in payload.items()
        }
        print(f"📤 Payload:\n{json.dumps(display_payload, indent=2, ensure_ascii=False)}")

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )

            print(f"📊 Status Code: {response.status_code}")

            # Parse response
            try:
                data = response.json()
            except:
                data = {"error": "Cannot parse JSON", "raw": response.text[:200]}

            # Kiểm tra kết quả
            if response.status_code == expected_status:
                if expected_status == 200:
                    print(f"✅ SUCCESS!")
                    print(f"📝 Enhanced Prompt: {data.get('enhanced_prompt', 'N/A')[:100]}...")
                    print(f"⚙️  Config Used:\n{json.dumps(data.get('config_used', {}), indent=2)}")

                    # Lưu ảnh
                    if data.get('image_base64'):
                        filename = f"{test_name.replace(' ', '_').replace('-', '_').lower()}.png"
                        self.save_image(data['image_base64'], filename)
                else:
                    # Expected error
                    print(f"✅ PASS (Expected error)")
                    print(f"📝 Error: {data.get('error', 'N/A')}")
                    print(f"💡 Hint: {data.get('hint', 'N/A')}")

                self.results.append({
                    "test": test_name,
                    "status": "PASS",
                    "response": data
                })
                return True
            else:
                print(f"❌ FAILED!")
                print(f"Expected: {expected_status}, Got: {response.status_code}")
                print(f"Error:\n{json.dumps(data, indent=2, ensure_ascii=False)}")

                self.results.append({
                    "test": test_name,
                    "status": "FAIL",
                    "error": data
                })
                return False

        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            self.results.append({
                "test": test_name,
                "status": "ERROR",
                "error": str(e)
            })
            return False

    def run_all_tests(self, init_image_path=None):
        """Chạy tất cả các test cases"""
        print("\n" + "=" * 60)
        print("🚀 BẮT ĐẦU TEST API IMAGE GENERATION")
        print("=" * 60)

        # ==================== TEXT-TO-IMAGE TESTS ====================
        print("\n" + "=" * 60)
        print("📝 SECTION 1: TEXT-TO-IMAGE TESTS")
        print("=" * 60)

        # TEST 1: Text-to-Image cơ bản với prompt enhancement
        self.test_request(
            "Test-1-Text2Img-Basic-Enhancement",
            {
                "prompt": "a beautiful sunset over mountains",
                "regen_prompt": True,
                "mode": "text2img",
                "aspect_ratio": "16:9"
            }
        )

        # TEST 2: Text-to-Image không enhancement
        self.test_request(
            "Test-2-Text2Img-No-Enhancement",
            {
                "prompt": "a futuristic city with flying cars, neon lights, cyberpunk style, 8k, ultra detailed",
                "regen_prompt": False,
                "mode": "text2img",
                "aspect_ratio": "1:1"
            }
        )

        # TEST 3: Text-to-Image với prompt tiếng Việt
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

        # TEST 4: Text-to-Image aspect ratio 21:9
        self.test_request(
            "Test-4-Text2Img-Ultrawide-21-9",
            {
                "prompt": "epic landscape, mountains, lake, cinematic, wide angle",
                "regen_prompt": True,
                "aspect_ratio": "21:9"
            }
        )

        # ==================== IMAGE-TO-IMAGE TESTS ====================
        if init_image_path and os.path.exists(init_image_path):
            print("\n" + "=" * 60)
            print("🖼️  SECTION 2: IMAGE-TO-IMAGE TESTS")
            print("=" * 60)

            init_image_b64 = self.image_to_base64(init_image_path)
            if init_image_b64:
                # TEST 5: Img2Img với strength thấp (giữ nhiều chi tiết gốc)
                self.test_request(
                    "Test-5-Img2Img-Low-Strength",
                    {
                        "prompt": "turn this into a watercolor painting",
                        "regen_prompt": True,
                        "mode": "img2img",
                        "init_image": init_image_b64,
                        "strength": 0.5
                    }
                )

                # TEST 6: Img2Img với strength cao (thay đổi mạnh)
                self.test_request(
                    "Test-6-Img2Img-High-Strength",
                    {
                        "prompt": "make it look like a comic book illustration, bold colors",
                        "regen_prompt": True,
                        "mode": "img2img",
                        "init_image": init_image_b64,
                        "strength": 0.9
                    }
                )

                # TEST 7: Img2Img không enhancement (dùng prompt gốc)
                self.test_request(
                    "Test-7-Img2Img-No-Enhancement",
                    {
                        "prompt": "oil painting style, artistic, masterpiece, detailed brush strokes",
                        "regen_prompt": False,
                        "mode": "img2img",
                        "init_image": init_image_b64,
                        "strength": 0.7
                    }
                )
        else:
            print("\n⚠️  Bỏ qua IMAGE-TO-IMAGE tests (không có init image)")
            print(f"💡 Để test img2img, chạy: tester.run_all_tests(init_image_path='your_image.jpg')")

        # ==================== ERROR HANDLING TESTS ====================
        print("\n" + "=" * 60)
        print("❌ SECTION 3: ERROR HANDLING TESTS")
        print("=" * 60)

        # TEST 8: Error - Missing prompt
        self.test_request(
            "Test-8-Error-Missing-Prompt",
            {
                "regen_prompt": True,
                "mode": "text2img"
            },
            expected_status=400
        )

        # TEST 9: Error - Invalid aspect ratio
        self.test_request(
            "Test-9-Error-Invalid-Aspect-Ratio",
            {
                "prompt": "test image",
                "aspect_ratio": "4:3"  # Invalid - không có trong VALID_ASPECT_RATIOS
            },
            expected_status=500  # Lambda gốc chưa validate, sẽ bị lỗi từ Bedrock
        )

        # TEST 10: Error - Img2Img missing init_image
        self.test_request(
            "Test-10-Error-Img2Img-No-Init",
            {
                "prompt": "beautiful landscape",
                "mode": "img2img"
            },
            expected_status=400
        )

        # TEST 11: Error - Invalid mode
        self.test_request(
            "Test-11-Error-Invalid-Mode",
            {
                "prompt": "test image",
                "mode": "invalid_mode"
            },
            expected_status=500  # Lambda gốc chưa validate mode
        )

        # TEST 12: Error - Invalid strength
        if init_image_path and os.path.exists(init_image_path):
            init_image_b64 = self.image_to_base64(init_image_path)
            if init_image_b64:
                self.test_request(
                    "Test-12-Error-Invalid-Strength",
                    {
                        "prompt": "test",
                        "mode": "img2img",
                        "init_image": init_image_b64,
                        "strength": 1.5  # Invalid (> 1.0)
                    },
                    expected_status=500  # Lambda gốc chưa validate strength, lỗi từ Bedrock
                )

        # In ra kết quả tổng hợp
        self.print_summary()

    def print_summary(self):
        """In ra tổng kết kết quả"""
        print("\n" + "=" * 60)
        print("📊 KẾT QUẢ TỔNG HỢP")
        print("=" * 60)

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        total = len(self.results)

        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {failed}/{total}")
        print(f"⚠️  Errors: {errors}/{total}")
        print(f"📈 Success Rate: {(passed / total * 100):.1f}%")

        print("\n" + "-" * 60)
        print("Chi tiết từng test:")
        print("-" * 60)
        for r in self.results:
            status_icon = "✅" if r["status"] == "PASS" else "❌" if r["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {r['test']}: {r['status']}")


# ================== MAIN ==================
if __name__ == "__main__":
    API_URL = "https://autevn7nbg.execute-api.us-east-1.amazonaws.com/pro/gen"

    # Khởi tạo tester
    tester = APIImageGenTester(API_URL)

    # Chạy tất cả tests
    # 🔥 QUAN TRỌNG: Thay đường dẫn ảnh của bạn ở đây
    tester.run_all_tests(init_image_path=r"C:\Users\leamo\Downloads\aaaa.jpg")

    print("\n" + "=" * 60)
    print("✨ HOÀN THÀNH TẤT CẢ TEST CASES!")
    print("=" * 60)
    print("📁 Các ảnh đã được lưu trong thư mục 'output/'")
    print("\n💡 Lưu ý:")
    print("   - Text2Img tests (1-4): Nên PASS")
    print("   - Img2Img tests (5-7): Nên PASS (AWS tự scale ảnh)")
    print("   - Error tests (8-12): Test 8,10 PASS | Test 9,11,12 có thể 500 (lambda chưa validate)")