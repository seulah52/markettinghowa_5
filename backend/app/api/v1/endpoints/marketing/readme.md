# 🇨🇳 중국 왕홍 마케팅 자동 콘텐츠 생성기 v7 (Shohong AI)

본 프로젝트는 한국 기업의 중국 시장 진출을 돕기 위해, 제품 이미지만으로 **중국 현지 플랫폼 최적화 홍보물(이미지, 문구, 영상 스토리보드, 왕홍 제안서)**을 원스톱으로 생성하는 AI 기반 마케팅 자동화 솔루션입니다.

---

## ✨ 핵심 기능 (Key Features)

### 1. 🖼️ 지능형 제품 분석 및 배경 제거 (STEP 1)
*   **GPT-4o Vision 분석:** 이미지 업로드 시 브랜드명, 제품 특징, 타겟 고객 등을 한국어로 자동 추출.
*   **하이브리드 배경 제거:** `remove.bg` API와 로컬 `rembg` 라이브러리를 결합하여 최상의 제품 누끼 이미지 생성.

### 2. 📈 플랫폼 특화 마케팅 브리프 (STEP 2)
*   **6대 플랫폼 대응:** 샤오홍슈(小红书), 도우인(抖音), 타오바오(淘宝) 등 각 플랫폼 가이드라인(글자 수, 해시태그 수, 톤앤매너) 자동 적용.
*   **자동 컴플라이언스 검수:** 중국 광고법 위반 소지가 있는 금지 표현(최고, 유일 등)을 카테고리별로 자동 필터링 및 수정 제안.

### 3. 🎨 AI 멀티 테마 콘텐츠 생성 (STEP 3)
*   **멀티 테마 합성:** '모던 라이프스타일', '사이버펑크 테크', '럭셔리 골드' 등 4가지 테마에 제품을 자연스럽게 합성.
*   **DeepSeek 기반 카피라이팅:** DeepSeek-V3를 활용하여 현지 MZ세대가 열광하는 트렌디한 중국어 문구 및 해시태그 생성.
*   **PIL 텍스트 오버레이:** 생성된 이미지 하단에 중국어 홍보 문구를 세련된 배너 형태로 자동 합성.

### 4. 🤝 왕홍 협업 및 리포트 자동화 (STEP 4)
*   **맞춤형 제안서 3종:** 왕홍의 티어와 스타일에 맞춘 협업 제안서(DM 단문/장문, 이메일)를 한/중 쌍으로 자동 생성.
*   **AI 영상 스토리보드:** 씬별 비주얼 설명 및 자막(Pinyin 포함)이 포함된 숏폼 영상 기획안 제공.
*   **엑셀/JSON 다운로드:** 모든 기획 데이터를 스타일이 적용된 엑셀 보고서 또는 시스템 연동용 JSON으로 내보내기.

---

## 🛠 기술 스택 (Tech Stack)

*   **Frontend/App Framework:** Streamlit
*   **Large Language Models:**
    *   OpenAI GPT-4o (Vision, Structured Outputs, Text)
    *   DeepSeek-V3 (Creative Copywriting)
*   **Image Generation:** OpenAI DALL-E 3 (Edit & Generate)
*   **Image Processing:** PIL (Pillow), rembg (ONNX Runtime)
*   **Data Export:** openpyxl (Styled Excel)
*   **APIs:** remove.bg API

---

## 🚀 시작하기 (Getting Started)

### 1. 환경 설정 (.env)
루트 디렉토리에 `.env` 파일을 생성하고 아래 키를 입력하세요.
```env
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
REMOVE_BG_API_KEY=your_remove_bg_api_key (선택)
```

### 2. 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 3. 앱 실행
```bash
streamlit run app.py
```

---

## 📂 프로젝트 구조
*   `app.py`: v7 최신 통합 버전 (메인 실행 파일)
*   `app12.py`: v6 기반 기능 테스트용 파일
*   `requirements.txt`: 의존성 라이브러리 목록
*   `.env.example`: 환경 변수 설정 샘플

---

## 📝 참고 사항
*   **이미지 합성:** 원본 제품의 형태를 최대한 보존하는 'Preserve' 모드와 배경에 어우러지는 'Generate' 모드를 선택할 수 있습니다.
*   **언어 지원:** 기획과 분석은 한국어로 진행되며, 최종 결과물은 중국어로 생성되고 한국어 번역이 병기됩니다.
