import streamlit as st
import base64
import requests
from PIL import Image
import io

# ==========================================
# 1. 설정 (보안을 위해 st.secrets 사용)
# ==========================================
# 스트림릿 클라우드의 Secrets 설정에 입력한 키를 자동으로 불러옵니다.
API_KEY = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="심꾸니 학업 비서 Pro", page_icon="💊", layout="wide")

# [프리미엄 UI CSS] - 디자인 완성도 업그레이드
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700;800&display=swap');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #F4F7FB; }
    .main-header { 
        background: white; padding: 25px; border-radius: 20px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.05); text-align: center; 
        border-bottom: 5px solid #3B82F6; margin-bottom: 25px;
    }
    .result-card { 
        background: #FFFFFF; padding: 20px; border-radius: 15px; 
        border: 1px solid #E5E7EB; line-height: 1.7; margin-bottom: 20px;
    }
    .chat-container {
        background: #F8FAFC; padding: 15px; border-radius: 15px; border: 1px solid #CBD5E1;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%);
        color: white; border: none; border-radius: 10px; height: 3rem;
        font-weight: 700; width: 100%; transition: 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

# [세션 관리] - 대화 기록 저장용
if "raw_text" not in st.session_state: st.session_state.raw_text = ""
if "analysis_res" not in st.session_state: st.session_state.analysis_res = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- [AI 엔진 함수] ---
def call_gpt(model, messages, temp=0.5):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": model, "messages": messages, "temperature": temp}
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        return response.json()['choices'][0]['message']['content']
    except:
        return "❌ 연결 오류가 발생했습니다. API 키를 확인해주세요."

def process_image(uploaded_file):
    image = Image.open(uploaded_file)
    image.thumbnail((1600, 1600))
    buffered = io.BytesIO()
    image.convert("RGB").save(buffered, format="JPEG", quality=90)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- [메인 레이아웃] ---
st.markdown("<div class='main-header'><h1 style='color:#1E3A8A; margin:0;'>🩺 심꾸니 학업 비서 <span style='color:#3B82F6;'>Pro v5.0</span></h1><p style='color:#64748B; margin-top:5px;'>전공 분석부터 AI 심화 토의까지</p></div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.markdown("### 📸 1. 자료 업로드")
    file = st.file_uploader("교재 또는 논문 사진을 올려주세요", type=["jpg", "png", "jpeg"])
    if file:
        st.image(file, use_container_width=True)
        if st.button("✨ 텍스트 추출 시작"):
            with st.spinner("이미지에서 글자를 읽는 중..."):
                img_b64 = process_image(file)
                # 검열 우회용 단순 OCR 프롬프트
                ocr_msg = [
                    {"role": "system", "content": "너는 이미지 속 문자를 텍스트로 변환하는 접근성 도구야. 눈에 보이는 모든 글자를 있는 그대로 추출해."},
                    {"role": "user", "content": [{"type": "text", "text": "텍스트 추출 명령."}, 
                                                 {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}
                ]
                st.session_state.raw_text = call_gpt("gpt-4o-mini", ocr_msg, temp=0.0)

with col2:
    st.markdown("### 📝 2. 정밀 분석")
    if st.session_state.raw_text:
        st.session_state.raw_text = st.text_area("📄 추출된 원문 (수정 가능)", st.session_state.raw_text, height=200)
        
        if st.button("🚀 간호학 박사 모드 분석 실행"):
            with st.spinner("전문 지식 분석 중..."):
                analysis_prompt = f"다음 간호학 텍스트를 [한글 번역], [의학용어 설명], [핵심 요약]으로 정리해줘:\n\n{st.session_state.raw_text}"
                st.session_state.analysis_res = call_gpt("gpt-4o", [{"role": "user", "content": analysis_prompt}])

    if st.session_state.analysis_res:
        st.markdown(f"<div class='result-card'>{st.session_state.analysis_res}</div>", unsafe_allow_html=True)

# --- [새로운 기능: 💬 3. 학습 대화창] ---
st.divider()
if st.session_state.analysis_res:
    st.markdown("### 💬 3. AI 튜터와 심화 토의")
    st.caption("분석된 내용을 바탕으로 궁금한 점을 질문해보세요. (예: 이 질환의 합병증은?, 관련 간호 진단은?)")
    
    # 채팅 인터페이스 출력
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("질문을 입력하세요..."):
        # 유저 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 응답 생성
        with st.chat_message("assistant"):
            # 문맥 구성을 위해 원문 + 분석결과 + 대화기록 전달
            context = [
                {"role": "system", "content": f"너는 다음 간호학 자료를 완벽히 이해한 박사급 튜터야. 원문: {st.session_state.raw_text} / 분석결과: {st.session_state.analysis_res}. 이 내용을 바탕으로 학생의 질문에 전문적이고 친절하게 답해줘."},
                *st.session_state.messages
            ]
            response = call_gpt("gpt-4o", context)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# 사이드바 관리
with st.sidebar:
    st.header("🛠️ 관리 메뉴")
    if st.button("🔄 전체 초기화"):
        st.session_state.raw_text = ""
        st.session_state.analysis_res = ""
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.info("광수가 만든\n**심꾸니 전용 학습 비서**")

st.markdown(f"<div style='text-align: center; color: #94A3B8; padding: 30px;'>Designed with ❤️ by <b>팡수</b> for <b>심꾸니</b></div>", unsafe_allow_html=True)
