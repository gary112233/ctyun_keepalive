import time
try:
    import pytesseract
    USE_PYTESSERACT = True
except ImportError:
    USE_PYTESSERACT = False

try:
    from PIL import Image
    USE_PIL = True
except ImportError:
    USE_PIL = False

# 导入验证码识别库
try:
    import ddddocr
    USE_DDDDOCR = True
except ImportError:
    USE_DDDDOCR = False

try:
    import muggle_ocr
    USE_MUGGLE_OCR = True
except ImportError:
    USE_MUGGLE_OCR = False
    class Muggle_OCR():
        from enum import Enum
        class ModelType(Enum):
            Captcha=1
            OCR=2
            
        def SDK(self,model_type):
            return self
        def predict(self,image_bytes):
            return "nofoundOCR"
    muggle_ocr=Muggle_OCR()

def captcha_pic(fname,model_type=None,loops=1):
    if USE_MUGGLE_OCR:
        # 使用muggle_ocr
        sdk = muggle_ocr.SDK(model_type=model_type)
        try:
            with open(fname, "rb") as f:
                b = f.read()
                for i in range(loops):
                    st = time.time()
                    capt_text = sdk.predict(image_bytes=b)
                    print(capt_text, time.time() - st)
        except FileNotFoundError as e:
            capt_text=None
    elif USE_PYTESSERACT and USE_PIL:
        # 使用pytesseract
        try:
            image = Image.open(fname)
            # 预处理图像以提高识别率
            image = image.convert('L')  # 转换为灰度
            capt_text = pytesseract.image_to_string(image, config='--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
            capt_text = capt_text.strip()
            print(f"OCR识别结果: {capt_text}")
        except Exception as e:
            print(f"OCR识别失败: {e}")
            capt_text = None
    else:
        # 没有可用的OCR库
        print("没有可用的OCR识别库，请手动输入验证码")
        capt_text = None
    return capt_text


if __name__ == '__main__':   

    for n in range(1,10):
        fname=f"captcha{n}.jpg"
        code=captcha_pic(fname,muggle_ocr.ModelType.Captcha)
        if(code==None):break