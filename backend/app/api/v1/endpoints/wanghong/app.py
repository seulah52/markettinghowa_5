import json
import os
import re
import time
import base64
import random
import traceback
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# API Clients
deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_w_to_man(text):
    """숫자 뒤의 'w'를 '만'으로 변경하는 함수"""
    if not text: return "0"
    return text.replace('w', '만').replace('W', '만')

def encode_image(image_path):
    if not os.path.exists(image_path): return ""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_with_vision(main_img_path, price_img_path):
    try:
        main_base64 = encode_image(main_img_path)
        price_base64 = encode_image(price_img_path)
        if not main_base64: return None
        
        prompt = """
        Analyze these screenshots. 
        Extract data into a JSON object. 
        CRITICAL: All explanations or labels must be in Korean. 
        Keys: new_followers, new_notes, hot_rate, avg_like, avg_save, avg_share, video_price, image_price, cpe, cpm.
        Replace 'w' with '만' in any numeric values.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{main_base64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{price_base64}"}} if price_base64 else {"type": "text", "text": "Price image not available"}
            ]}],
            max_tokens=800
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        return json.loads(json_match.group()) if json_match else None
    except: return None

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "전달된 상품 정보가 없습니다."}), 400
            
        desc = data.get('product_desc', '')
        count = int(data.get('recommend_count', 10))
        
        # 파일 로드
        json_path = "influencers.json"
        if not os.path.exists(json_path):
            return jsonify({"error": "서버에 왕홍 데이터(influencers.json)가 없습니다. 크롤링을 먼저 실행해주세요."}), 404
            
        with open(json_path, "r", encoding="utf-8") as f:
            influencers = json.load(f)
        
        print(f"🚀 AI 분석 요청 중... (추천 인원: {count})")
        
        # AI 프롬프트 (한국어 지시 강화)
        prompt = f"""
        당신은 가구/인테리어 마케팅 전문가입니다. 
        [상품]: {desc}
        [왕홍 리스트]: {json.dumps(influencers[:100], ensure_ascii=False)}
        
        미션: 위 리스트 중 상품과 가장 잘 어울리는 왕홍 {count}명을 선별하세요.
        조건:
        1. 추천 사유(reason)는 반드시 **한국어**로 정성스럽게 작성할 것.
        2. 결과는 JSON 리스트 형식만 출력할 것: [{{ "id": "...", "name": "...", "reason": "..." }}]
        """
        
        try:
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": "Marketing expert. Answer in JSON array format."}, {"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content.strip()
        except Exception as api_err:
            print(f"❌ DeepSeek API 오류: {api_err}")
            return jsonify({"error": f"AI API 호출 실패: {str(api_err)}"}), 500
        
        # JSON 추출
        try:
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            recs = json.loads(json_match.group()) if json_match else json.loads(content)
        except Exception as parse_err:
            print(f"❌ AI 응답 파싱 오류: {content[:100]}")
            return jsonify({"error": "AI가 보내온 데이터를 읽을 수 없습니다. 다시 시도해주세요."}), 500
            
        inf_map = {str(i.get('id')): i for i in influencers}
        results = []
        for r in recs:
            item = inf_map.get(str(r.get('id')))
            if item:
                c = item.copy()
                c['reason'] = r.get('reason', '추천 사유 없음')
                # 'w' 단위를 '만'으로 변경
                c['followers'] = format_w_to_man(str(c.get('followers', '0')))
                results.append(c)
        
        return jsonify({"recommendation": results[:count]})
        
    except Exception as e:
        print(f"❌ 전체 오류: {e}")
        return jsonify({"error": f"서버 내부 오류: {str(e)}"}), 500

@app.route('/get_detail')
def get_detail():
    anchor_id = request.args.get('id')
    anchor_name = request.args.get('name')

    def generate():
        browser = None
        try:
            yield ": keep-alive\n\n"
            yield f"data: 🚀 '{anchor_name}' 분석을 개시합니다.\n\n"
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(viewport={'width': 1440, 'height': 900}, storage_state="huitun_xhs_cookie.json")
                page = context.new_page()
                yield "data: 🕵️ 리스트 페이지 접속 중...\n\n"
                # 타임아웃을 60초로 늘리고 대기 전략을 완화함
                try:
                    page.goto("https://xhs.huitun.com/#/anchor/anchor_list?page=add", wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(3000) # 뼈대 뜬 후 추가 3초 대기
                except Exception as e:
                    yield f"data: ⚠️ 페이지 로딩 지연 중... 계속 시도합니다.\n\n"

                try: page.get_by_text("家居家装").first.click(); page.wait_for_timeout(2000)
                except: pass

                found = False
                yield "data: 🕵️ 리스트에서 왕홍 탐색 중...\n\n"
                for i in range(25):
                    yield ": keep-alive\n\n"
                    target = page.locator(f"//span[contains(text(), '{anchor_name}')] | //div[contains(text(), '{anchor_name}')]").first
                    if target.is_visible(timeout=2000):
                        # 보안 차단 회피: 클릭 직전 랜덤 지연 (1~2초)
                        page.wait_for_timeout(random.uniform(1000, 2000))
                        yield f"data: 🎯 왕홍 발견! 클릭 중...\n\n"
                        target.click(force=True); found = True; break
                    page.mouse.wheel(0, 1500)
                    page.wait_for_timeout(1000)

                # 동적 창 전환 대기 및 포커스 이동
                if found:
                    try:
                        # 새 창이 생성될 때까지 대기 (최대 5초)
                        start_time = time.time()
                        while len(context.pages) < 2 and time.time() - start_time < 5:
                            page.wait_for_timeout(500)
                        
                        if len(context.pages) > 1:
                            page = context.pages[-1]
                            page.bring_to_front()
                            yield "data: 🔄 새 창으로 전환 완료.\n\n"
                    except Exception as e:
                        print(f"⚠️ 창 전환 대기 중 오류: {e}")

                if not found or "anchor_detail" not in page.url:
                    if "anchor_detail" not in page.url:
                        yield "data: ⚠️ 직접 URL 이동으로 전환합니다.\n\n"
                        page.goto(f"https://xhs.huitun.com/#/anchor/anchor_detail?id={anchor_id}", wait_until="domcontentloaded", timeout=60000)

                yield "data: ⏳ 데이터 가시성 및 실제 값 검증 중 (최대 20초)...\n\n"
                
                # '데이터 없음(暂无数据)' 자동 새로고침 및 데이터 값 검증 대기
                try:
                    refresh_count = 0
                    data_verified = False
                    
                    while refresh_count <= 2: # 최대 2회 새로고침 시도
                        start_wait = time.time()
                        while time.time() - start_wait < 15:
                            content = page.evaluate("() => document.body.innerText")
                            
                            # '暂无数据' 감지 시 즉시 새로고침
                            if "暂无数据" in content:
                                if refresh_count < 2:
                                    refresh_count += 1
                                    yield f"data: 🔄 '데이터 없음(暂无数据)' 감지 (시도 {refresh_count}/2), 새로고침합니다...\n\n"
                                    page.reload(wait_until="domcontentloaded")
                                    page.wait_for_timeout(3000)
                                    start_wait = time.time() # 새로고침 후 대기 시간 초기화
                                    continue
                                else:
                                    yield "data: ⚠️ 2회 새로고침 후에도 데이터가 없습니다.\n\n"
                                    break

                            # 데이터 값 검증 대기: 실제 숫자(0이 아닌 값)가 들어올 때까지 확인
                            # 粉丝, 笔记, 赞藏 등 주요 지표 옆에 1-9로 시작하는 숫자가 있는지 확인
                            if re.search(r'(粉丝|笔记|赞藏|关注|点赞)\D*[1-9]\d*[\.w만W]*', content):
                                # 애니메이션 정지 대기: 숫자가 변하지 않도록 추가 3초 대기
                                yield "data: ✅ 실제 데이터(Non-zero) 감지! 안정화를 위해 대기합니다...\n\n"
                                page.wait_for_timeout(3000)
                                data_verified = True
                                break
                            
                            page.wait_for_timeout(1500)
                        
                        if data_verified: break
                        if refresh_count >= 2: break
                        
                    if not data_verified:
                        yield "data: ⚠️ 데이터 로딩 지연 또는 0인 상태입니다. 현재 상태로 분석을 진행합니다.\n\n"
                except Exception as e:
                    yield f"data: ⚠️ 데이터 검증 로직 중 오류 발생: {str(e)}\n\n"

                # 추출 직전 디버그 로그
                final_content = page.evaluate("() => document.body.innerText")
                debug_content = final_content[:200].replace('\n', ' ')
                print(f"🔍 [추출 직전 화면 확인]: {debug_content}...")
                
                main_shot = f"debug_main_{anchor_id}.png"
                page.screenshot(path=main_shot)
                
                clicked = page.evaluate("""() => {
                    const targets = Array.from(document.querySelectorAll('.ant-tabs-tab, .el-tabs__item, span, div'));
                    const found = targets.find(t => t.innerText && t.innerText.trim() === '报价');
                    if (found) { found.click(); return true; }
                    return false;
                }""")

                price_shot = f"debug_price_{anchor_id}.png"
                if not clicked:
                    yield "data: 📢 [알림] 직접 '报价' 탭을 눌러주세요! (15초 대기)\n\n"
                    for r in range(15, 0, -1):
                        yield f"data: ⏳ 대기 중... {r}초\n\n"
                        page.wait_for_timeout(1000)
                else:
                    # '报价' 클릭 후에도 애니메이션/로딩 대기
                    page.wait_for_timeout(3000)
                
                page.screenshot(path=price_shot)
                browser.close(); browser = None
                
                yield "data: 🧠 GPT-4o Vision 분석 중 (한국어로 변환)...\n\n"
                ai_data = extract_with_vision(main_shot, price_shot)
                
                if ai_data:
                    for key in ai_data:
                        if isinstance(ai_data[key], str):
                            ai_data[key] = format_w_to_man(ai_data[key])
                    yield f"data: FINISHED:{json.dumps(ai_data)}\n\n"
                else:
                    yield "data: ERROR: 분석 실패\n\n"

        except Exception as e:
            # 전체 프로세스 예외 처리 및 실패 화면 저장
            print(f"❌ 분석 오류 발생 ({anchor_id}): {traceback.format_exc()}")
            try:
                if 'page' in locals() and page:
                    fail_path = f"fail_{anchor_id}.png"
                    page.screenshot(path=fail_path)
                    yield f"data: 📸 오류 발생! 실패 화면이 저장되었습니다: {fail_path}\n\n"
            except: pass
            yield f"data: ERROR: {str(e)}\n\n"
        finally:
            if browser: 
                try: browser.close()
                except: pass

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(port=5000, debug=True, threaded=True)
