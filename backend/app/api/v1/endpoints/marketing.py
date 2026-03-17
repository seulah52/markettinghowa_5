import os
import json
import base64
import asyncio
import requests
import traceback
from io import BytesIO
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont, ImageColor
import re

print("[BOOT] marketing.py loaded, re ok:", re)

# =========================
# 상수 / 금지 표현
# =========================
CATEGORY_BANNED: Dict[str, List[str]] = {
    "건강식품": ["치료", "완치", "의학적 효능", "임상 입증", "FDA 승인"],
    "화장품":   ["주름 제거", "미백 보장", "성형 효과", "피부과 인증"],
    "식품":     ["다이어트 보장", "칼로리 제로 보장", "의사 추천"],
}
BASE_BANNED = ["100%", "最", "立即见效", "治愈", "无副作用", "最好", "第一"]

BANNED_EXPLANATION = {
    "最":       "最 (최고·가장 등 최상급 표현 — 중국 광고법 금지)",
    "100%":     "100% (절대적 수치 보장 — 허위 광고 위험)",
    "立即见效": "立即见效 (즉각 효과 보장 — 과장 광고)",
    "治愈":     "治愈 (치료·완치 의료 주장 — 식품·가구 사용 불가)",
    "无副作用": "无副作用 (부작용 없음 보장 — 의료 효능 주장)",
    "最好":     "最好 (가장 좋음 — 근거 없는 최상급 금지)",
    "第一":     "第一 (1위 표현 — 증빙 없는 순위 금지)",
}

BRIEF_PARTIAL_SCHEMA = {
    "title": "brief_partial",
    "type": "object",
    "properties": {
        "target":         {"type": "string"},
        "key_benefits":   {"type": "array", "items": {"type": "string"}},
        "tone":           {"type": "string"},
        "banned_claims":  {"type": "array", "items": {"type": "string"}},
        "landing_action": {"type": "string"},
    },
    "required": ["target", "key_benefits", "tone", "banned_claims", "landing_action"],
    "additionalProperties": False,
}

# =========================
# 플랫폼 설정
# =========================
PLATFORMS: Dict[str, Dict[str, Any]] = {
    "xiaohongshu": {
        "name_kr": "샤오홍수",
        "name_cn": "小红书",
        "style": "감성 종초(种草) 스타일, 진정성 있는 후기, 이모지 활용, 생활 밀착형 서술",
        "hashtag_count": 8,
        "caption_max": 1000,
        "scene_count": 6,
        "video_duration": "15~30초",
    },
    "taobao": {
        "name_kr": "타오바오",
        "name_cn": "淘宝",
        "style": "가성비 강조, 상품 상세 설명, 프로모션·할인 부각, 신뢰도 기반",
        "hashtag_count": 5,
        "caption_max": 800,
        "scene_count": 5,
        "video_duration": "15~60초",
    },
    "douyin": {
        "name_kr": "더우인",
        "name_cn": "抖音",
        "style": "트렌디·바이럴 숏폼, 강렬한 후킹, 챌린지 유도, 빠른 템포",
        "hashtag_count": 5,
        "caption_max": 300,
        "scene_count": 5,
        "video_duration": "15~60초",
    },
    "jingdong": {
        "name_kr": "징동",
        "name_cn": "京东",
        "style": "브랜드 신뢰도, 스펙 중심 상세 설명, 품질·정품 보증 강조",
        "hashtag_count": 4,
        "caption_max": 600,
        "scene_count": 5,
        "video_duration": "30~60초",
    },
}

try:
    from rembg import remove as rembg_remove  # type: ignore
    REMBG_AVAILABLE = True
except Exception:
    rembg_remove = None
    REMBG_AVAILABLE = False

from openai import AsyncOpenAI
from app.core.config import settings

router = APIRouter()

# =========================
# 클라이언트 설정
# =========================
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# DeepSeek / Remove.bg / 모델명 — config(배포 env) 기준
DEEPSEEK_API_KEY = settings.DEEPSEEK_API_KEY
deepseek_client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
) if settings.DEEPSEEK_API_KEY else None
DEEPSEEK_MODEL = "deepseek-chat"

REMOVE_BG_API_KEY = settings.REMOVE_BG_API_KEY
IMAGE_MODEL = settings.IMAGE_MODEL
TEXT_MODEL = settings.TEXT_MODEL

ROOT_DIR         = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DATA_STORAGE_DIR = os.path.join(ROOT_DIR, "storage", "data")
MARKETING_DIR    = os.path.dirname(__file__)
FONT_DIR         = os.path.join(MARKETING_DIR, "marketing", "font")
EVENTS_PATH      = os.path.join(MARKETING_DIR, "marketing", "events.jsonl")

FONTS = {
    "JianZhengLiHei":        "JianZhengLiHei.ttf",
    "XingQiuHei":            "XingQiuHei.ttf",
    "XinRui":                "XinRui.ttf",
    "ZhengQingKeShuaiHeiTi": "ZhengQingKeShuaiHeiTi.ttf",
}

NO_TEXT = (
    "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO FONTS, NO TYPOGRAPHY, "
    "NO LOGOS, NO WATERMARKS, NO LABELS anywhere in the image. "
    "Pure product photography only."
)

IMAGE_THEMES = [
    {
        "name_kr": "☀️ 자연채광 웜톤 거실 컷",
        "style": (
            "Interior lifestyle photography, warm afternoon sunlight streaming through sheer curtains, "
            "natural wood tones and warm beige palette, cozy and inviting living room setting, "
            "soft linen textures, potted plant in the background, "
            "Xiaohongshu interior influencer aesthetic, golden hour warmth. "
        ),
    },
    {
        "name_kr": "🛋️ 모던 미니멀리즘 컷",
        "style": (
            "Modern minimalist interior photography, clean white and light grey tones, "
            "sleek contemporary furniture, uncluttered composition with intentional negative space, "
            "soft diffused studio lighting, architectural lines, "
            "Scandinavian-Korean fusion design aesthetic, premium lifestyle feel. "
        ),
    },
    {
        "name_kr": "🌃 무드 시네마틱 라운지 컷",
        "style": (
            "Cinematic luxury lounge interior photography, warm indirect ambient lighting, "
            "deep moody tones with rich shadows, high-end hotel or boutique lounge atmosphere, "
            "plush textures, velvet and marble accents, "
            "sophisticated and aspirational mood, editorial interior style. "
        ),
    },
    {
        "name_kr": "🌿 식물테리어(플랜테리어) 컷",
        "style": (
            "Planteria interior photography, lush green houseplants of various sizes surrounding the furniture, "
            "fresh and natural biophilic design, soft daylight with green leafy shadows, "
            "terracotta pots and natural woven baskets as props, "
            "earthy and refreshing mood, urban jungle Xiaohongshu lifestyle aesthetic. "
        ),
    },
]

# =========================
# 요청 스키마
# =========================
class Step2Request(BaseModel):
    image_b64:       Optional[str]       = ""
    brand:           Optional[str]       = ""
    product:         Optional[str]       = ""
    features:        Optional[str]       = ""
    category:        Optional[str]       = ""
    price:           Optional[str]       = ""
    promo:           Optional[str]       = ""
    image_size:      Optional[str]       = "1024x1792"
    selected_themes: Optional[List[str]] = Field(default_factory=list)
    use_previous:    Optional[bool]      = False  # True 시 이전 데이터의 keyword로 product·category 자동 채움

class OverlayRequest(BaseModel):
    image_b64:     str
    text:          str
    font_name:     str
    color:         str
    size_ratio:    float
    pos_x:         float
    pos_y:         float
    rotation:      int
    shadow:        bool
    outline:       bool
    outline_color: str
    bg_enabled:    bool
    bg_color:      str
    bg_opacity:    float
    # 브랜드명 오버레이 - 개별 설정
    brand_text:    Optional[str] = ""
    brand_font:    Optional[str] = "JianZhengLiHei"
    brand_color:   Optional[str] = "#FFFFFF"
    brand_size:    Optional[float] = 0.08
    brand_x:       Optional[float] = 0.5
    brand_y:       Optional[float] = 0.7
    brand_shadow:  Optional[bool] = False
    brand_outline: Optional[bool] = False
    brand_out_color: Optional[str] = "#000000"
    brand_bg:      Optional[bool] = False
    brand_bg_color: Optional[str] = "#000000"
    brand_bg_opacity: Optional[float] = 0.5
    # 가격 오버레이 - 개별 설정
    price_text:    Optional[str] = ""
    price_font:    Optional[str] = "JianZhengLiHei"
    price_color:   Optional[str] = "#FFFFFF"
    price_size:    Optional[float] = 0.08
    price_x:       Optional[float] = 0.5
    price_y:       Optional[float] = 0.6
    price_shadow:  Optional[bool] = False
    price_outline: Optional[bool] = False
    price_out_color: Optional[str] = "#000000"
    price_bg:      Optional[bool] = False
    price_bg_color: Optional[str] = "#000000"
    price_bg_opacity: Optional[float] = 0.5

class Step3Request(BaseModel):
    brand:        Optional[str] = ""
    product:      Optional[str] = ""   # 한국어 원본
    product_en:   Optional[str] = ""   # 영어 번역
    product_cn:   Optional[str] = ""   # 중국어 번역
    features:     Optional[str] = ""
    platform:     Optional[str] = "xiaohongshu"
    target:       Optional[str] = ""
    category:     Optional[str] = ""
    use_previous: Optional[bool] = False  # True 시 이전 데이터의 keyword로 product·category 자동 채움

class Step4Request(BaseModel):
    brand:        Optional[str] = ""
    product:      Optional[str] = ""
    features:     Optional[str] = ""
    platform:     Optional[str] = "xiaohongshu"
    category:     Optional[str] = ""
    price:        Optional[str] = ""
    promo:        Optional[str] = ""
    target:       Optional[str] = ""
    tone:         Optional[str] = ""
    use_previous: Optional[bool] = False  # True 시 이전 데이터의 keyword로 product·category 자동 채움

class Step5Request(BaseModel):
    brand:        Optional[str] = ""
    product:      Optional[str] = ""
    title:        Optional[str] = ""
    body:         Optional[str] = ""
    platform:     Optional[str] = "xiaohongshu"
    use_previous: Optional[bool] = False  # True 시 이전 데이터의 keyword로 product 자동 채움

class TranslateProductRequest(BaseModel):
    product_kr: str = ""  # 한국어 제품명(키워드)

# =========================
# 응답 스키마
# =========================
CREATIVE_COPY_SCHEMA = {
    "type": "object",
    "properties": {
        "title_cn": {"type": "string"},
        "title_kr": {"type": "string"},
        "body_cn":  {"type": "string"},
        "body_kr":  {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title_cn", "title_kr", "body_cn", "body_kr", "hashtags"],
    "additionalProperties": False,
}

STORYBOARD_FULL_SCHEMA = {
    "type": "object",
    "properties": {
        "subtitles_cn": {"type": "array", "items": {"type": "string"}},
        "subtitles_kr": {"type": "array", "items": {"type": "string"}},
        "storyboard": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene":      {"type": "string"},
                    "duration":   {"type": "string"},
                    "visual":     {"type": "string"},
                    "caption_cn": {"type": "string"},
                    "caption_kr": {"type": "string"},
                },
                "required": ["scene", "duration", "visual", "caption_cn", "caption_kr"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["subtitles_cn", "subtitles_kr", "storyboard"],
    "additionalProperties": False,
}

# =========================
# 유틸리티
# =========================
def ensure_list(v) -> List[str]:
    if v is None: return []
    if isinstance(v, list): return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        return [x.strip() for x in v.replace(";", ",").replace("\n", ",").split(",") if x.strip()]
    return [str(v).strip()]

def extract_xhs_hashtags(xhs_data: List[Dict]) -> List[str]:
    tags = []
    for item in xhs_data:
        desc = item.get("description", "")
        found = re.findall(r"#([^\s#\ufeff\u200b]+)", desc)
        for f in found:
            cleaned = re.sub(r'[^\w\u4e00-\u9fff]', '', f).strip()
            if cleaned:
                tags.append("#" + cleaned)
    return sorted(list(set(tags)))

def load_json(filename: str):
    path = os.path.join(DATA_STORAGE_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def remove_background(img_bytes: bytes) -> bytes:
    if REMOVE_BG_API_KEY:
        try:
            resp = requests.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": img_bytes},
                data={"size": "auto"},
                headers={"X-Api-Key": REMOVE_BG_API_KEY},
                timeout=30,
            )
            if resp.status_code == 200: return resp.content
        except Exception: pass
    if REMBG_AVAILABLE and rembg_remove is not None:
        try:
            out = rembg_remove(img_bytes)
            if out: return out
        except Exception: pass
    return img_bytes

def _load_overlay_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        if font_name in FONTS:
            path = os.path.join(FONT_DIR, FONTS[font_name])
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
    except Exception: pass
    return ImageFont.load_default()

def _extract_texts(data, max_items: int = 10, key: str = "description") -> str:
    if isinstance(data, list):
        return "\n".join([str(item.get(key, ""))[:300] for item in data[:max_items]])
    if isinstance(data, dict):
        return json.dumps(data, ensure_ascii=False)[:2000]
    return ""

# ===== 이미지 비율 보정 함수 (신규) =====
def adjust_image_aspect_ratio(img: Image.Image, target_size: str) -> Image.Image:
    """
    이미지를 목표 비율에 맞춰 crop 처리합니다.
    1024x1024: 1:1 정사각형
    1024x1792: 9:16 세로형
    """
    W, H = img.size
    
    if target_size == "1024x1024":
        # 정사각형: 짧은 쪽에 맞춰서 crop
        size = min(W, H)
        left = (W - size) // 2
        top = (H - size) // 2
        return img.crop((left, top, left + size, top + size))
    elif target_size == "1024x1792":
        # 9:16 세로형
        target_ratio = 9 / 16
        current_ratio = W / H
        
        if current_ratio > target_ratio:
            # 가로가 너무 길면: 가로를 crop
            new_w = int(H * target_ratio)
            left = (W - new_w) // 2
            return img.crop((left, 0, left + new_w, H))
        elif current_ratio < target_ratio:
            # 세로가 너무 길면: 세로를 crop
            new_h = int(W / target_ratio)
            top = (H - new_h) // 2
            return img.crop((0, top, W, top + new_h))
        else:
            return img
    else:
        return img

# =========================
# AI 헬퍼
# =========================
async def _call_structured(system: str, user: str, schema: dict, max_retries: int = 2) -> Dict[str, Any]:
    """OpenAI gpt-4o JSON 호출 (이미지 분석 등 OpenAI 전용 용도)"""
    for attempt in range(max_retries + 1):
        try:
            resp = await openai_client.chat.completions.create(
                model=TEXT_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system + "\n\nReturn ONLY valid JSON."},
                    {"role": "user",   "content": "json\n" + user},
                ],
                temperature=0.85,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            if attempt == max_retries: raise e
            await asyncio.sleep(1)
    return {}

async def _call_deepseek_json(system: str, user: str, max_retries: int = 2) -> Dict[str, Any]:
    """DeepSeek JSON 모드 호출. 키 없으면 OpenAI 폴백."""
    client = deepseek_client
    if not client:
        return await _call_structured(system, user, {})
    for attempt in range(max_retries + 1):
        try:
            resp = await client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system + "\n\nReturn ONLY valid JSON."},
                    {"role": "user",   "content": "json\n" + user},
                ],
                temperature=0.85,
            )
            raw = resp.choices[0].message.content or "{}"
            raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
            return json.loads(raw)
        except Exception as e:
            if attempt == max_retries: raise e
            await asyncio.sleep(1)
    return {}

async def _call_deepseek_text(system: str, user: str, max_retries: int = 2) -> str:
    """DeepSeek 자유형식 텍스트 호출. 키 없으면 OpenAI 폴백."""
    client = deepseek_client
    if not client:
        resp = await openai_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.85,
        )
        return resp.choices[0].message.content or ""
    for attempt in range(max_retries + 1):
        try:
            resp = await client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                temperature=0.85,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            if attempt == max_retries: raise e
            await asyncio.sleep(1)
    return ""

async def analyze_product_image(img_bytes: bytes) -> Dict[str, str]:
    try:
        b64 = base64.b64encode(img_bytes).decode()
        user_content = [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": (
                "이 제품 사진을 분석해서 아래 항목을 한국어 한두 문장으로만 요약해줘.\n"
                "- shape: 소파 전체 실루엣/구조 (예: L자형, 일자형, 낮은 등받이 등)\n"
                "- material: 주요 소재/텍스처 (예: 패브릭, 가죽, 린넨 등)\n"
                "- base_color: 전체적인 색상 계열 (예: 웜 베이지, 쿨 그레이 등)\n"
                "- details: 다리에 대한 특징, 팔걸이 형태 등 추가 시각적 디테일 한두 문장\n"
                "- short_desc: 이 제품이 어떻게 보이는지 한 문장 요약"
            )},
        ]
        resp = await openai_client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "너는 제품 사진을 보는 시각 디자이너다. 제품의 외형/재질/색감을 간결하게 요약해 JSON으로만 출력한다."},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.1,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"[vision] 분석 실패: {e}")
        return {}

# =========================
# 이미지 생성
# =========================
async def generate_theme_image(
    theme,
    nobg_img_bytes: bytes,
    brand: str,
    product: str,
    brief_data: Dict[str, Any],
    vision_info: Dict[str, Any],
    size: str = "1024x1792",
):
    try:
        requested_size = size or "1024x1792"
        actual_size = "1024x1024"
        if "1792" in requested_size or "1536" in requested_size:
            actual_size = "1024x1792"

        shape      = vision_info.get("shape", "")
        material   = vision_info.get("material", "")
        base_color = vision_info.get("base_color", "")
        details    = vision_info.get("details", "")
        short_desc = vision_info.get("short_desc", "")
        kb = ", ".join(brief_data.get("key_benefits", [])[:2])

        prompt_parts = [
            theme.get("style", ""),
            "High-end commercial product photography.",
            "The hero product must look like the SAME physical object as the original reference photo.",
            "Exactly ONE hero product in the scene. Do NOT duplicate the product.",
            "Keep the full product in frame. Do not crop it out of the image.",
            "절대 제품의 형태, 비율, 소재, 기본 색감을 바꾸지 말 것. 배경과 조명만 재해석한다.",
            f"원본 제품 요약: {short_desc}",
            f"형태: {shape} / 소재: {material} / 기본 색감: {base_color}.",
        ]
        if details: prompt_parts.append(f"디테일: {details}.")
        prompt_parts.append(f"Product: '{product}' by brand '{brand}'.")
        prompt_parts.append(f"Target: {brief_data.get('target', '')}. Key benefits: {kb}.")
        prompt_parts.append(f"No medical claims. {NO_TEXT}")

        prompt = " ".join(str(p) for p in prompt_parts if p)
        if len(prompt) > 950: prompt = prompt[:950]

        kwargs: Dict[str, Any] = {"model": IMAGE_MODEL, "prompt": prompt, "n": 1}
        if IMAGE_MODEL.startswith("gpt-image-"):
            kwargs["size"]    = "1024x1536" if ("1792" in requested_size or "1536" in requested_size) else "1024x1024"
            kwargs["quality"] = "medium"
            # response_format 미지원 — 추가하지 않음
        else:
            kwargs["size"]            = actual_size
            kwargs["quality"]         = "standard"
            kwargs["response_format"] = "b64_json"

        result   = await openai_client.images.generate(**kwargs)
        item     = result.data[0]
        b64_data: Optional[str] = getattr(item, "b64_json", None)
        if not b64_data:
            url = getattr(item, "url", None)
            if url:
                img_resp = requests.get(url, timeout=30)
                if img_resp.status_code == 200:
                    b64_data = base64.b64encode(img_resp.content).decode()
        if not b64_data: return None

        # 후처리: center-crop → 요청 해상도로 resize
        try:
            img = Image.open(BytesIO(base64.b64decode(b64_data)))
            rw, rh = map(int, requested_size.split('x'))
            if img.size != (rw, rh):
                w, h = img.size
                tr = rh / rw
                cr = h / w
                if cr > tr:
                    nh = int(w * tr); top = (h - nh) // 2
                    img = img.crop((0, top, w, top + nh))
                elif cr < tr:
                    nw = int(h / tr); left = (w - nw) // 2
                    img = img.crop((left, 0, left + nw, h))
                img = img.resize((rw, rh), Image.LANCZOS)
                buf = BytesIO(); img.save(buf, format="PNG")
                b64_data = base64.b64encode(buf.getvalue()).decode()
        except Exception as resize_err:
            print(f"[resize] 후처리 실패: {resize_err}")

        return {"name": theme["name_kr"], "image_b64": f"data:image/png;base64,{b64_data}"}
    except Exception as e:
        print(f"!!! Theme fail [{theme['name_kr']}]: {str(e)}")
        return None

# =========================
# 텍스트 레이어 그리기 함수 (개선)
# =========================
def _draw_text_layer(
    img: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill_rgb: tuple,
    pos_x: float, pos_y: float,
    rotation: int, shadow: bool, outline: bool, outline_rgb: tuple,
    bg_rgba = None,
) -> Image.Image:
    """
    단일 텍스트 레이어를 img(RGBA)에 합성하여 반환
    개선: 글씨만 출력, 배경은 선택 시에만 추가 (bg_rgba가 None이 아닐 때만)
    """
    W, H = img.size
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw      = ImageDraw.Draw(txt_layer)
    bbox   = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]; text_h = bbox[3] - bbox[1]
    font_size = font.size if hasattr(font, 'size') else 20
    x = int(max(0.0, min(pos_x, 1.0)) * W - text_w / 2)
    y = int(max(0.0, min(pos_y, 1.0)) * H - text_h / 2)
    
    # 배경: bg_rgba가 있을 때만 그리기
    if bg_rgba is not None:
        pad_x, pad_y = int(text_w * 0.25), int(text_h * 0.35)
        rect = [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y]
        ImageDraw.Draw(img).rounded_rectangle(rect, radius=max(4, int(font_size * 0.4)), fill=bg_rgba)
    
    if shadow:
        so = max(2, font_size // 10)
        draw.text((x + so, y + so), text, font=font, fill=(0, 0, 0, 180))
    if outline:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1,-1),(1,-1),(-1,1),(1,1)]:
            draw.text((x + dx, y + dy), text, font=font, fill=outline_rgb)
    draw.text((x, y), text, font=font, fill=(*fill_rgb, 255))
    if rotation:
        txt_layer = txt_layer.rotate(rotation, resample=Image.BICUBIC, center=(W // 2, H // 2))
    return Image.alpha_composite(img, txt_layer)

# =========================
# 엔드포인트
# =========================

@router.post("/step2-init")
async def step2_init(req: Step2Request):
    try:
        # 이전 데이터 불러오기 모드: product·category를 이전 keyword로 자동 채움
        if req.use_previous:
            prev = _load_previous_data_fields()
            if not prev["keyword"]:
                raise HTTPException(status_code=404, detail="이전 데이터가 없습니다. 먼저 리서치를 실행해주세요.")
            if not req.product:
                req.product = prev["keyword"]
            if not req.category:
                req.category = prev["category"]

        xhs_data = load_json("xhs_result.json") or []
        xhs_tone_sample = "\n".join([str(item.get("description", "")) for item in xhs_data[:20]])

        cat_banned = CATEGORY_BANNED.get(req.category.split("/")[0] if req.category else "", [])
        all_banned = list(set(BASE_BANNED + cat_banned))

        brief_sys = (
            "너는 중국 B2C 왕홍 마케팅 전문 기획자다.\n"
            "아래 확정 정보를 바탕으로 마케팅 브리프 JSON을 생성한다.\n"
            "- 브랜드명·제품명·카테고리·가격·프로모션은 절대 변경하지 말 것.\n"
            "- 오직 target, key_benefits, tone, banned_claims, landing_action 5개 키만 생성.\n"
            f"- key_benefits: 3~5개 배열\n"
            f"- banned_claims에 반드시 포함: {all_banned}\n"
            "- tone 스타일 지시: 真实测评\n"
        )
        brief_user = (
            f"브랜드: {req.brand}\n제품: {req.product}\n카테고리: {req.category}\n"
            f"가격: {req.price}\n프로모션: {req.promo}\n추가 메모: {req.features}"
        )
        brief_partial = await _call_structured(brief_sys, brief_user, BRIEF_PARTIAL_SCHEMA)

        def _el(v):
            if v is None: return []
            return v if isinstance(v, list) else [str(v)]

        brief_partial["key_benefits"]  = _el(brief_partial.get("key_benefits"))
        brief_partial["banned_claims"] = list(set(_el(brief_partial.get("banned_claims")) + all_banned))

        brief_data = {
            "brand_name":   req.brand or "미입력",
            "product_name": req.product,
            "category":     req.category or "미입력",
            "price":        req.price or None,
            "promo":        req.promo or None,
            "target":       brief_partial.get("target", ""),
            "key_benefits": brief_partial.get("key_benefits", []),
            "tone":         brief_partial.get("tone", ""),
            "banned_claims":  brief_partial.get("banned_claims", []),
            "landing_action": brief_partial.get("landing_action", ""),
        }

        img_data    = base64.b64decode(req.image_b64.split(",")[-1])
        nobg_bytes  = await asyncio.to_thread(remove_background, img_data)
        vision_info = await analyze_product_image(nobg_bytes)

        # DeepSeek: 오버레이 문구 5개 추천
        overlay_sys  = "你是小红书爆款文案专家。只输出JSON。"
        overlay_user = (
            f"请学习以下小红书笔记的写作语气（只看语气，不要照抄内容）。\n"
            f"[语气样本]\n{xhs_tone_sample}\n"
            f"现在请为品牌 {req.brand} 的产品 {req.product} 生成5条可叠加在图片上的短文案"
            f"（不超过7个汉字，中文，无标点）。"
            f'格式：{{"recommendations":["...","..."]}}'
        )
        copy_res = await _call_deepseek_json(overlay_sys, overlay_user)
        overlays = copy_res.get("recommendations", [])[:5]

        themes_out = []
        active_themes = (
            [t for t in IMAGE_THEMES if t["name_kr"] in (req.selected_themes or [])]
            if req.selected_themes else IMAGE_THEMES
        )
        for i, theme in enumerate(active_themes):
            r = await generate_theme_image(
                theme, nobg_bytes, req.brand, req.product,
                brief_data, vision_info, req.image_size or "1024x1536"
            )
            if r: themes_out.append(r)
            if i < len(active_themes) - 1: await asyncio.sleep(1.5)

        if not themes_out: raise RuntimeError("이미지 생성 실패")
        return {"status": "ok", "themes": themes_out, "overlays": overlays}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/overlay")
async def overlay(req: OverlayRequest):
    """
    메인 오버레이 + 브랜드명 + 가격 오버레이 (모두 개별 설정 지원)
    - 메인 텍스트: 기본 설정
    - 브랜드명: 개별 폰트, 색상, 위치, 배경 설정
    - 가격: 개별 폰트, 색상, 위치, 배경 설정
    """
    try:
        raw_b64   = req.image_b64.split(",")[-1]
        img_bytes = base64.b64decode(raw_b64)
        base_img  = Image.open(BytesIO(img_bytes)).convert("RGBA")
        W, H      = base_img.size

        img = base_img.copy()

        # ──────────── 메인 텍스트 오버레이 ────────────
        font_size   = max(12, int(min(W, H) * max(0.02, min(req.size_ratio, 0.3))))
        font        = _load_overlay_font(req.font_name, font_size)
        fill_rgb    = ImageColor.getrgb(req.color) if req.color else (255, 255, 255)
        outline_rgb = ImageColor.getrgb(req.outline_color) if req.outline and req.outline_color else (0, 0, 0)
        bg_rgba = None
        if req.bg_enabled:
            bg_rgb  = ImageColor.getrgb(req.bg_color) if req.bg_color else (0, 0, 0)
            alpha   = int(255 * max(0.0, min(req.bg_opacity, 1.0)))
            bg_rgba = (*bg_rgb, alpha)

        text = (req.text or "").strip()
        if text:
            img = _draw_text_layer(
                img, text, font, fill_rgb,
                req.pos_x, req.pos_y,
                req.rotation, req.shadow, req.outline, outline_rgb, bg_rgba,
            )

        # ──────────── 브랜드명 오버레이 (개별 설정) ────────────
        brand_text = (req.brand_text or "").strip()
        if brand_text:
            brand_font_size = max(12, int(min(W, H) * max(0.02, min(req.brand_size, 0.3))))
            brand_font = _load_overlay_font(req.brand_font, brand_font_size)
            brand_fill_rgb = ImageColor.getrgb(req.brand_color) if req.brand_color else (255, 255, 255)
            brand_outline_rgb = ImageColor.getrgb(req.brand_out_color) if req.brand_out_color else (0, 0, 0)
            
            brand_bg_rgba = None
            if req.brand_bg:
                brand_bg_rgb = ImageColor.getrgb(req.brand_bg_color) if req.brand_bg_color else (0, 0, 0)
                brand_alpha = int(255 * max(0.0, min(req.brand_bg_opacity, 1.0)))
                brand_bg_rgba = (*brand_bg_rgb, brand_alpha)
            
            img = _draw_text_layer(
                img, brand_text, brand_font, brand_fill_rgb,
                req.brand_x, req.brand_y,
                0, req.brand_shadow, req.brand_outline, brand_outline_rgb, brand_bg_rgba,
            )

        # ──────────── 가격 오버레이 (개별 설정) ────────────
        price_text = (req.price_text or "").strip()
        if price_text:
            price_font_size = max(12, int(min(W, H) * max(0.02, min(req.price_size, 0.3))))
            price_font = _load_overlay_font(req.price_font, price_font_size)
            price_fill_rgb = ImageColor.getrgb(req.price_color) if req.price_color else (255, 255, 255)
            price_outline_rgb = ImageColor.getrgb(req.price_out_color) if req.price_out_color else (0, 0, 0)
            
            price_bg_rgba = None
            if req.price_bg:
                price_bg_rgb = ImageColor.getrgb(req.price_bg_color) if req.price_bg_color else (0, 0, 0)
                price_alpha = int(255 * max(0.0, min(req.price_bg_opacity, 1.0)))
                price_bg_rgba = (*price_bg_rgb, price_alpha)
            
            img = _draw_text_layer(
                img, price_text, price_font, price_fill_rgb,
                req.price_x, req.price_y,
                0, req.price_shadow, req.price_outline, price_outline_rgb, price_bg_rgba,
            )

        merged = img.convert("RGB")
        out    = BytesIO(); merged.save(out, format="PNG")
        return {"status": "ok", "image_b64": f"data:image/png;base64,{base64.b64encode(out.getvalue()).decode()}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step3-generate")
async def step3_generate(req: Step3Request):
    try:
        # 이전 데이터 불러오기 모드
        if req.use_previous:
            prev = _load_previous_data_fields()
            if not prev["keyword"]:
                raise HTTPException(status_code=404, detail="이전 데이터가 없습니다. 먼저 리서치를 실행해주세요.")
            if not req.product:
                req.product = prev["keyword"]
            if not req.category:
                req.category = prev["category"]

        platform_key = req.platform if req.platform in PLATFORMS else "xiaohongshu"
        p = PLATFORMS[platform_key]

        xhs_data     = load_json("xhs_result.json") or []
        xhs_tag_data = load_json("xhs_tag.json")    or {}

        # 해시태그 풀 구성
        real_hashtags_from_posts = extract_xhs_hashtags(xhs_data)
        static_tags = ["#" + t.strip() for t in xhs_tag_data.get("tags", []) if t.strip()]
        all_tags_raw = sorted(list(set(real_hashtags_from_posts + static_tags)))

        xhs_tone_sample  = "\n".join([str(item.get("description", ""))[:200] for item in xhs_data[:10]])
        cat_banned       = CATEGORY_BANNED.get(req.category.split("/")[0] if req.category else "", [])
        all_banned       = list(set(BASE_BANNED + cat_banned))
        hashtag_candidates = ", ".join(all_tags_raw[:50])

        # 제품명 다국어 처리
        product_for_prompt = (
            req.product_cn.strip() if req.product_cn and req.product_cn.strip()
            else req.product_en.strip() if req.product_en and req.product_en.strip()
            else req.product or ""
        )
        product_label_parts = [req.product or ""]
        if req.product_en and req.product_en.strip():
            product_label_parts.append(req.product_en.strip())
        if req.product_cn and req.product_cn.strip():
            product_label_parts.append(req.product_cn.strip())
        product_label = " / ".join(dict.fromkeys(filter(None, product_label_parts)))

        # DeepSeek: 제목/본문/해시태그 생성
        copy_sys = (
            f"你是中国{p['name_cn']}专业营销人员。\n"
            f"平台风格: {p['style']}\n"
            f"请学习以下{p['name_cn']}帖子的写作语气，并为品牌撰写标题和正文。\n"
            f"[写作语气样本]\n{xhs_tone_sample}\n\n"
            f"[热门话题标签候选 — 从中选出最适合产品的{p['hashtag_count']}个]\n"
            f"{hashtag_candidates}\n\n"
            f"要求:\n"
            f"- 产品名称请优先使用中文名称进行内容创作\n"
            f"- hashtags: 从上述候选中精确选择{p['hashtag_count']}个（含#）\n"
            f"- body_cn: {p['caption_max']}字以内\n"
            f"- 绝对禁止: {all_banned}\n"
            f"- title_cn/body_cn → 自然中文\n"
            f"- title_kr/body_kr: 2단계 번역 필수: 中文→英文→韩語 순으로 번역하여 최종 한국어 출력\n"
            f"只输出JSON。"
        )
        copy_user = json.dumps(
            {
                "brand":       req.brand,
                "product":     product_for_prompt,
                "product_all": product_label,
                "extra_notes": req.features,
                "target":      req.target,
            },
            ensure_ascii=False,
        )
        copy_data = await _call_deepseek_json(copy_sys, copy_user)

        # DeepSeek: 해시태그 한국어 번역
        trans_sys = (
            "你是中韩翻译专家。将以下中文话题标签翻译成简短的韩语含义（5字以内）。\n"
            '只输出JSON格式: {"items": [{"tag": "#原文", "kr": "韩语含义"}, ...]}'
        )
        trans_user = json.dumps({"tags": all_tags_raw[:80]}, ensure_ascii=False)
        trans_data = await _call_deepseek_json(trans_sys, trans_user)
        tag_kr_map: Dict[str, str] = {
            item["tag"]: item.get("kr", "")
            for item in trans_data.get("items", [])
            if "tag" in item
        }

        all_real_hashtags = [
            {"tag": t, "kr": tag_kr_map.get(t, "")}
            for t in all_tags_raw
        ]

        return {
            "status":       "ok",
            "title":        copy_data.get("title_cn", ""),
            "body":         copy_data.get("body_cn", ""),
            "title_kr":     copy_data.get("title_kr", ""),
            "body_kr":      copy_data.get("body_kr", ""),
            "hashtags":     copy_data.get("hashtags", []),
            "real_hashtags": all_real_hashtags,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step4-memo")
async def step4_memo(req: Step4Request):
    try:
        # 이전 데이터 불러오기 모드
        if req.use_previous:
            prev = _load_previous_data_fields()
            if not prev["keyword"]:
                raise HTTPException(status_code=404, detail="이전 데이터가 없습니다. 먼저 리서치를 실행해주세요.")
            if not req.product:
                req.product = prev["keyword"]
            if not req.category:
                req.category = prev["category"]

        platform_key = req.platform if req.platform in PLATFORMS else "xiaohongshu"
        p = PLATFORMS[platform_key]

        xhs_data    = load_json("xhs_result.json")   or []
        taobao_data = load_json("taobao_result.json") or []
        baidu_data  = load_json("baidu_result.json")  or []
        final_data  = load_json("final_report.json")  or {}

        xhs_text    = _extract_texts(xhs_data,    max_items=8)
        taobao_text = _extract_texts(taobao_data, max_items=8)
        baidu_text  = _extract_texts(baidu_data,  max_items=8)
        final_text  = _extract_texts(final_data)

        strategy_sys = (
            f"당신은 중국 {p['name_kr']} ({p['name_cn']}) 마케팅 전략 수석 기획자입니다.\n"
            f"플랫폼 스타일: {p['style']}\n"
            f"아래 4개 데이터 소스(XHS, 타오바오, 바이두, 최종리포트)를 종합 분석하여 "
            f"한국어로 상세한 마케팅 전략 명세서를 작성하십시오.\n"
            f"각 항목은 **볼드 제목** + 3~5문장 이상의 구체적 내용으로 작성하십시오.\n\n"
            f"**1. 핵심 소구점 (USP)**\n"
            f"**2. 타겟 고객 페르소나 분석**\n"
            f"**3. 페인포인트 & 솔루션**\n"
            f"**4. 시각적 무드 & 콘텐츠 방향**\n"
            f"**5. 추천 콘텐츠 톤앤매너**\n"
            f"**6. 가격·프로모션 전략**\n"
            f"**7. 예상 KPI & 바이럴 전략**\n\n"
            f"반드시 한국어로만 작성하십시오."
        )
        strategy_user = (
            f"브랜드: {req.brand}\n제품: {req.product}\n카테고리: {req.category}\n"
            f"가격: {req.price}\n프로모션: {req.promo}\n타겟: {req.target or '자동추론'}\n"
            f"추가메모: {req.features}\n\n"
            f"--- XHS 데이터 ---\n{xhs_text}\n\n"
            f"--- 타오바오 데이터 ---\n{taobao_text}\n\n"
            f"--- 바이두 데이터 ---\n{baidu_text}\n\n"
            f"--- 최종 리포트 ---\n{final_text}"
        )

        memo = await _call_deepseek_text(strategy_sys, strategy_user)
        return {
            "status": "ok",
            "memo": memo.strip(),
            "banned_explanation": BANNED_EXPLANATION,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


STORYBOARD_STRICT_SCHEMA = {
    "type": "object",
    "properties": {
        "subtitles_cn": {"type": "array", "items": {"type": "string"}},
        "subtitles_kr": {"type": "array", "items": {"type": "string"}},
        "storyboard": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene":      {"type": "string"},
                    "duration":   {"type": "string"},
                    "visual":     {"type": "string"},
                    "caption_cn": {"type": "string"},
                    "caption_kr": {"type": "string"},
                },
                "required": ["scene", "duration", "visual", "caption_cn", "caption_kr"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["subtitles_cn", "subtitles_kr", "storyboard"],
    "additionalProperties": False,
}

def _ensure_storyboard(v) -> list:
    """타입 보정"""
    if v is None: return []
    if isinstance(v, list):
        result = []
        for item in v:
            if isinstance(item, dict):
                result.append({
                    "scene":      str(item.get("scene", "")),
                    "duration":   str(item.get("duration", "")),
                    "visual":     str(item.get("visual", "")),
                    "caption_cn": str(item.get("caption_cn", "")),
                    "caption_kr": str(item.get("caption_kr", "")),
                })
            else:
                result.append({
                    "scene": str(item), "duration": "", "visual": "",
                    "caption_cn": "", "caption_kr": "",
                })
        return result
    return []


@router.post("/step5-video")
async def step5_video(req: Step5Request):
    try:
        # 이전 데이터 불러오기 모드
        if req.use_previous:
            prev = _load_previous_data_fields()
            if not prev["keyword"]:
                raise HTTPException(status_code=404, detail="이전 데이터가 없습니다. 먼저 리서치를 실행해주세요.")
            if not req.product:
                req.product = prev["keyword"]

        platform_key = req.platform if req.platform in PLATFORMS else "xiaohongshu"
        p = PLATFORMS[platform_key]

        sb_sys = (
            f"你是中国{p['name_cn']}专业短视频营销策划师。\n"
            f"请为以下产品制作{p['scene_count']}个场景的分镜脚本。\n"
            f"视频建议时长: {p['video_duration']}\n\n"
            f"规则:\n"
            f"1. storyboard: 每个场景包含 scene(场景名), duration(时长), visual(画面构成详细说明), "
            f"caption_cn(中文字幕，18字以内), caption_kr(韩语翻译)\n"
            f"2. caption_kr: 2단계 번역 필수: 中文→英文→韩語 순으로 번역하여 최종 한국어 출력\n"
            f"2. visual의 영문 프롬프트: 매우 상세함, 장면·제품·색상·질감·조명·각도·동작 포함, 영문 150-300자\n3. subtitles_cn: 整体视频字幕列表（8行以内，每行最多18字）\n"
            f"4. subtitles_kr: subtitles_cn의 2단계 번역 (中文→英文→韩語)\n"
            f"5. 所有字段必须是字符串类型\n"
            f"只输出JSON。"
        )
        sb_user = json.dumps(
            {
                "brand":   req.brand,
                "product": req.product,
                "title":   req.title,
                "body":    req.body,
                "platform": p["name_cn"],
            },
            ensure_ascii=False,
        )

        data = {}
        last_err = None
        for attempt in range(3):
            try:
                data = await _call_deepseek_json(sb_sys, sb_user)
                if data.get("storyboard"):
                    break
            except Exception as e:
                last_err = e
                await asyncio.sleep(1)

        if not data.get("storyboard") and last_err:
            raise last_err

        storyboard   = _ensure_storyboard(data.get("storyboard", []))
        subtitles_cn = [str(s) for s in data.get("subtitles_cn", []) if s]
        subtitles_kr = [str(s) for s in data.get("subtitles_kr", []) if s]

        return {
            "status":       "ok",
            "storyboard":   storyboard,
            "subtitles_cn": subtitles_cn,
            "subtitles_kr": subtitles_kr,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# 이전 데이터 헬퍼
# =========================
def _load_previous_data_fields() -> dict:
    """final_report.json 에서 keyword·category를 추출해 반환."""
    final_data = load_json("final_report.json") or {}

    keyword = ""
    for key in ("keyword", "keywords", "search_keyword", "query",
                "product", "product_name", "한국어_키워드", "kr_keyword"):
        val = final_data.get(key)
        if val:
            keyword = val[0] if isinstance(val, list) else str(val)
            break

    category = ""
    for key in ("category", "industry", "industry_category", "산업군",
                "sector", "main_category", "classification"):
        val = final_data.get(key)
        if val:
            category = val[0] if isinstance(val, list) else str(val)
            break

    return {"keyword": keyword, "category": category, "raw": final_data}


@router.get("/previous-data")
async def get_previous_data():
    """이전 데이터(final_report.json)에서 keyword·category를 반환한다."""
    try:
        result = _load_previous_data_fields()
        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate-product")
async def translate_product(req: TranslateProductRequest):
    """제품명 다국어 번역"""
    try:
        if not req.product_kr.strip():
            return {"status": "ok", "kr": "", "en": "", "cn": ""}

        sys_prompt = (
            "You are a professional Korean-English-Chinese translator specializing in product and brand naming.\n"
            "Translate the given Korean product name/keyword into natural English and Simplified Chinese.\n"
            "Rules:\n"
            "- English: Use natural marketing-friendly product name (Title Case, concise)\n"
            "- Chinese: Use natural Simplified Chinese consumer-facing product name (2-6 characters preferred)\n"
            'Return ONLY JSON: {"en": "...", "cn": "..."}'
        )
        user_prompt = f"Korean product name: {req.product_kr.strip()}"

        result = await _call_deepseek_json(sys_prompt, user_prompt)

        return {
            "status": "ok",
            "kr": req.product_kr.strip(),
            "en": result.get("en", ""),
            "cn": result.get("cn", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
