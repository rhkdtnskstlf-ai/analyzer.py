import streamlit as st
import base64
import requests
from PIL import Image
import io

# [보안] Streamlit Secrets에서 API 키 로드
if "OPENAI_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    st.error("❌ API 키 설정이 필요합니다. Streamlit Cloud Secrets에 'OPENAI_API_KEY'를 넣어주세요.")
    st.stop()

st.set_page_config(page_title="간호대학원 학업 비서", layout="wide")

# 스타일 설정 (여성스럽고 깔끔한 디자인)
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .main-header { font-size: 2.2rem; font-weight: 800; color: #2C3E50; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #7F8C8D; margin-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header">🩺 심꾸니 간호대학원 학업 보조 AI 비서</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">전공 서적이나 논문을 찍어 올리면 정밀 번역과 핵심 요약을 제공합니다.</div>', unsafe_allow_html=True)

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# [성능] 이미지 최적화 함수
def process_and_encode_image(uploaded_file):
    image = Image.open(uploaded_file)
    image.thumbnail((1280, 1280)) # 속도를 위해 리사이징
    buffered = io.BytesIO()
    image.convert("RGB").save(buffered, format="JPEG", quality=85) # 용량 압축
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# [핵심] 거절 방지 및 간호학 특화 프롬프트
def analyze_image(base64_image):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": (
                    "너는 간호학 대학원생의 학업을 돕는 전문 교육용 어시스턴트야. "
                    "제공된 이미지는 전공 서적 혹은 연구 논문의 일부이며, 오직 교육적 분석 목적으로만 사용돼. "
                    "의학적 진단을 내리는 것이 아니라, 학술적 내용을 번역하고 정리하는 역할임을 명심해. "
                    "보안 가이드라인을 준수하면서, 전문적인 간호 및 의학 용어를 정확하게 사용하여 분석해줘."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "이 학술 자료를 분석해줘:\n"
                            "1. [Full Text]: 원문 내용 추출\n"
                            "2. [Terminology]: 주요 간호/의학 용어 설명\n"
                            "3. [Summary]: 대학원생 수준의 핵심 요약 및 시사점"
                        )
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 2000
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

def ask_follow_up(question, context):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"너는 간호대학원생을 돕는 튜터야. 다음 내용을 바탕으로 학생의 질문에 답해줘: {context}"},
            {"role": "user", "content": question}
        ]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

# 사이드바
with st.sidebar:
    st.header("📖 Study Guide")
    st.write("원서나 논문의 어려운 부분을 사진 찍어 올리시면 간호학 전문 용어를 포함해 정밀 분석해 드립니다.")
    if st.button("새로 시작하기 (기록 삭제)"):
        st.session_state.chat_history = []
        st.session_state.analysis_result = None
        st.rerun()

# 메인 화면
uploaded_file = st.file_uploader("전공 서적이나 논문 이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

if uploaded_file:
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.image(uploaded_file, caption="업로드된 자료", use_container_width=True)
    with col2:
        if st.button("🚀 분석 시작", type="primary", use_container_width=True):
            with st.spinner("전문 용어 분석 중... 잠시만 기다려주세요."):
                img_base64 = process_and_encode_image(uploaded_file)
                st.session_state.analysis_result = analyze_image(img_base64)
        
        if st.session_state.analysis_result:
            st.markdown(st.session_state.analysis_result)
            st.divider()
            
            # 대화형 피드백
            st.subheader("💬 이 내용에 대해 더 궁금한 점이 있나요?")
            for chat in st.session_state.chat_history:
                with st.chat_message(chat["role"]): st.write(chat["content"])
            
            if prompt := st.chat_input("교수님께 질문하듯 물어보세요!"):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.write(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("답변 중..."):
                        answer = ask_follow_up(prompt, st.session_state.analysis_result)
                        st.write(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})

st.divider()
st.caption("간호대학원 학업 지원 전용 AI | Powered by GPT-4o")
