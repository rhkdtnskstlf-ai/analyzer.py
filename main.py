import streamlit as st
import base64
import requests
from PIL import Image
import io

# ==========================================
# 1. 설정 (보안 강화: Secrets 방식 적용)
# ==========================================
# 배포 시 환경변수에서 키를 가져옵니다. 로컬 실행 시에도 secrets.toml을 참조합니다.
try:
    API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    API_KEY = "키가 설정되지 않았습니다. Secrets를 확인하세요."

st.set_page_config(page_title="심꾸니 학업 비서 v6.6", page_icon="📚", layout="wide")

# [디자인 스타일 - 주임님 요청 원복본]
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&display=swap');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    
    .main-header { 
        background: white; padding: 25px; border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; margin-bottom: 25px;
        border-top: 5px solid #3B82F6;
    }
    
    .manual-box {
        background: #EFF6FF; border: 1px solid #BFDBFE; 
        padding: 20px; border-radius: 12px; margin-bottom: 25px;
        color: #1E40AF; font-size: 0.95rem; line-height: 1.6;
    }
    
    .analysis-card {
        background: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left: 5px solid #3B82F6;
        line-height: 1.8;
    }
    
    .footer {
        text-align: center; margin-top: 50px; padding: 20px;
        font-weight: 700; color: #64748B; border-top: 1px solid #E2E8F0;
    }
    .heart { color: #EF4444; }
    </style>
    """, unsafe_allow_html=True)

# [세션 상태 관리]
if "pages" not in st.session_state: st.session_state.pages = []
if "current_idx" not in st.session_state: st.session_state.current_idx = 0
if "chat_history" not in st.session_state: st.session_state.chat_history = {}
if "merged_data" not in st.session_state: st.session_state.merged_data = {"raw": "", "analysis": "", "chat": []}

# --- [AI 엔진] ---
def call_gpt(model, messages, temp=0.5):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": model, "messages": messages, "temperature": temp}
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        return response.json()['choices'][0]['message']['content']
    except: return "❌ AI 응답 오류 발생 (API 키 설정을 확인하세요)"

def get_b64(image):
    image.thumbnail((1100, 1100))
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- [사이드바] ---
with st.sidebar:
    st.header("⚙️ 학습 메뉴")
    mode = st.radio("작업 모드", ["🔍 이미지별 정밀 분석", "📚 묶음 통합 분석"])
    st.divider()
    files = st.file_uploader("이미지 업로드", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if files and st.button("🆕 데이터 업데이트"):
        st.session_state.pages = [{"name": f.name, "image": Image.open(f), "raw": "", "analysis": ""} for f in files]
        st.rerun()

# --- [메인 화면 헤더] ---
st.markdown("<div class='main-header'><h1>🩺 심꾸니 학업 비서 v5.5 pro </h1></div>", unsafe_allow_html=True)

# --- [설명서 섹션] ---
st.markdown("""
    <div class='manual-box'>
        <strong>💡 심꾸니를 위한 학업 비서 활용 가이드</strong><br>
        1. <strong>이미지별 분석:</strong> 각 페이지를 '번역-요약-키워드' 순으로 아주 상세하게 공부할 때 사용하세요.<br>
        2. <strong>묶음 통합 분석:</strong> 여러 장을 한 번에 합쳐서 전체적인 맥락을 파악할 때 유용합니다.<br>
        * <em>통합 분석에서 추출된 원문은 개별 이미지 탭에서도 자동으로 연동되어 확인 가능합니다.</em><br>
        * <em>전체적인 페이지의 요약에 대해서 확인, 전체 페이지 원문 한번에 추출을 위한 기능으로 활용 권장합니다.</em><br>
        * <em>통합 정밀 분석은 분량이 많아 전체 내용을 핵심 위주로 요약하여 다룹니다. 세부 내용은 이미지별에서 확인하거나 ai에게 질의하세요.</em>
    </div>
    """, unsafe_allow_html=True)

if not st.session_state.pages:
    st.info("사이드바에서 학습 자료를 업로드하면 학업 지원이 시작됩니다.")
else:
    # --- [모드 1: 이미지별 분석] ---
    if mode == "🔍 이미지별 정밀 분석":
        st.sidebar.subheader("📄 페이지 리스트")
        for i, p in enumerate(st.session_state.pages):
            if st.sidebar.button(f"P.{i+1} - {p['name'][:10]}", key=f"side_{i}", use_container_width=True,
                                 type="primary" if i == st.session_state.current_idx else "secondary"):
                st.session_state.current_idx = i
                st.rerun()

        curr = st.session_state.pages[st.session_state.current_idx]
        col_img, col_work = st.columns([1, 1.2])
        
        with col_img:
            st.image(curr["image"], use_container_width=True)
            if st.button("✨ 이 페이지 원문 추출", use_container_width=True):
                b64 = get_b64(curr["image"])
                msg = [{"role": "system", "content": "OCR 전문가. 글자만 추출."}, 
                       {"role": "user", "content": [{"type": "text", "text": "추출."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}]
                curr["raw"] = call_gpt("gpt-4o-mini", msg, temp=0.0)
                st.rerun()

        with col_work:
            if curr["raw"]:
                with st.expander("📄 스캔 원문(영문) 확인", expanded=False):
                    curr["raw"] = st.text_area("내용 수정", curr["raw"], height=200, key=f"edit_{st.session_state.current_idx}")
                
                if st.button("🚀 정밀 분석 (5.0 Style)", use_container_width=True):
                    prompt = f"다음 영문 내용을 번역하고, 핵심 요약과 주요 키워드를 정리해줘:\n{curr['raw']}"
                    curr["analysis"] = call_gpt("gpt-4o", [{"role": "user", "content": prompt}])
                    st.rerun()
                
                if curr["analysis"]:
                    st.markdown(f"<div class='analysis-card'>{curr['analysis']}</div>", unsafe_allow_html=True)

        # 이미지별 대화
        if curr["analysis"]:
            st.divider()
            st.subheader("💬 페이지 질의응답")
            chat_key = f"chat_{st.session_state.current_idx}"
            if chat_key not in st.session_state.chat_history: st.session_state.chat_history[chat_key] = []
            for m in st.session_state.chat_history[chat_key]:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            if prompt := st.chat_input("이 페이지에 대해 궁금한 점?"):
                st.session_state.chat_history[chat_key].append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                with st.chat_message("assistant"):
                    ctx = [{"role": "system", "content": f"원문: {curr['raw']}"}, {"role": "user", "content": prompt}]
                    res = call_gpt("gpt-4o", ctx)
                    st.markdown(res)
                    st.session_state.chat_history[chat_key].append({"role": "assistant", "content": res})

    # --- [모드 2: 묶음 통합 분석] ---
    else:
        st.markdown("### 📚 통합 분석 순서 지정")
        cols = st.columns(4)
        order_map = {}
        for i, p in enumerate(st.session_state.pages):
            with cols[i % 4]:
                st.image(p["image"], use_container_width=True)
                order_val = st.number_input(f"순서 ({i+1}번)", min_value=0, max_value=len(st.session_state.pages), value=0, key=f"order_{i}")
                if order_val > 0: order_map[order_val] = i

        st.divider()
        sorted_indices = [order_map[k] for k in sorted(order_map.keys())]
        
        if sorted_indices:
            st.write(f"✅ **병합 순서:** {' ➔ '.join([str(idx+1) for idx in sorted_indices])}")
            c_b1, c_b2 = st.columns(2)
            
            if c_b1.button("🔍 통합 원문 추출", use_container_width=True):
                combined = ""
                bar = st.progress(0)
                for i, idx in enumerate(sorted_indices):
                    p = st.session_state.pages[idx]
                    if not p["raw"]:
                        b64 = get_b64(p["image"])
                        p["raw"] = call_gpt("gpt-4o-mini", [{"role": "user", "content": [{"type": "text", "text": "OCR."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}], temp=0.0)
                    combined += p["raw"] + " "
                    bar.progress((i + 1) / len(sorted_indices))
                st.session_state.merged_data["raw"] = combined
                st.rerun()

            if c_b2.button("🚀 전체 통합 요약 분석", use_container_width=True):
                if st.session_state.merged_data["raw"]:
                    prompt = f"다음은 여러 페이지가 통합된 내용입니다. 전체 번역 후 핵심 내용을 요약하고 전문 용어를 정리해주세요:\n{st.session_state.merged_data['raw']}"
                    st.session_state.merged_data["analysis"] = call_gpt("gpt-4o", [{"role": "user", "content": prompt}])
                    st.rerun()

        if st.session_state.merged_data["raw"]:
            with st.expander("📄 통합 영문 데이터", expanded=False):
                st.text_area("Raw", st.session_state.merged_data["raw"], height=200)
            
            if st.session_state.merged_data["analysis"]:
                st.markdown("### 🌍 통합 분석 리포트")
                st.markdown(f"<div class='analysis-card'>{st.session_state.merged_data['analysis']}</div>", unsafe_allow_html=True)
                
                st.divider()
                st.subheader("💬 통합 AI 토론")
                for m in st.session_state.merged_data["chat"]:
                    with st.chat_message(m["role"]): st.markdown(m["content"])
                if m_prompt := st.chat_input("전체 내용 질문?"):
                    st.session_state.merged_data["chat"].append({"role": "user", "content": m_prompt})
                    with st.chat_message("user"): st.markdown(m_prompt)
                    with st.chat_message("assistant"):
                        ctx = [{"role": "system", "content": f"원문: {st.session_state.merged_data['raw']}"}, {"role": "user", "content": m_prompt}]
                        res = call_gpt("gpt-4o", ctx)
                        st.markdown(res)
                        st.session_state.merged_data["chat"].append({"role": "assistant", "content": res})

st.markdown("""
    <div class='footer'>
        Design by 팡수 For 심꾸니 <span class='heart'>❤</span>
    </div>
    """, unsafe_allow_html=True)
