import streamlit as st
import base64
import requests
from PIL import Image
import io

# [보안] Streamlit Secrets 로드
if "OPENAI_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    st.error("❌ API 키 설정이 필요합니다. Streamlit Cloud Secrets를 확인해주세요.")
    st.stop()

st.set_page_config(page_title="간호대학원 학업 비서", layout="wide")

# 디자인 설정
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .main-header { font-size: 2.2rem; font-weight: 800; color: #2C3E50; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #7F8C8D; margin-bottom: 2rem; }
    .section-box { padding: 15px; border-radius: 10px; background-color: white; border: 1px solid #E9ECEF; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header">🩺 심꾸니 간호대학원 학업 보조 AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">이미지 속 원문 전체 추출부터 전문 용어 정리까지 한 번에 도와드려요.</div>', unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

def process_and_encode_image(uploaded_file):
    image = Image.open(uploaded_file)
    image.thumbnail((1600, 1600)) # 원문 추출을 위해 해상도를 조금 더 높임
    buffered = io.BytesIO()
    image.convert("RGB").save(buffered, format="JPEG", quality=90)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# [핵심] 요청 순서 변경: 원문 전체 -> 번역 -> 용어 -> 요약
def analyze_image(base64_image):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": (
                    "너는 간호대학원생의 논문 읽기를 돕는 전문 튜터야. "
                    "이미지에서 텍스트를 누락 없이 '전체' 추출하는 것이 가장 중요해. "
                    "의학적 진단이 아닌 학술적 분석임을 명시하고, 다음 순서대로 답변해줘."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "이 자료를 다음 순서로 아주 상세하게 분석해줘:\n\n"
                            "1. [Original Full Text]: 이미지에 있는 영문 텍스트 전체를 한 글자도 빠짐없이 그대로 추출해줘.\n"
                            "2. [Korean Translation]: 위 원문 전체를 매끄럽고 전문적인 한국어 간호학 용어를 써서 번역해줘.\n"
                            "3. [Medical Terminology]: 본문에 나온 주요 의학/간호 전문 용어들을 뽑아서 알기 쉽게 설명해줘.\n"
                            "4. [Academic Summary]: 대학원 수준에서 꼭 알아야 할 핵심 내용과 시사점을 3줄로 요약해줘."
                        )
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 4000 # 전체 텍스트 추출을 위해 토큰 한도를 높임
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

def ask_follow_up(question, context):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"간호학 대학원 튜터로서 다음 내용을 바탕으로 답해줘: {context}"},
            {"role": "user", "content": question}
        ]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

with st.sidebar:
    st.header("📖 Study Guide")
    st.write("논문이나 전공 서적 페이지를 찍어 올려주세요. 원문 전체와 번역본을 대조하며 공부할 수 있습니다.")
    if st.button("기록 지우고 새로 시작"):
        st.session_state.chat_history = []
        st.session_state.analysis_result = None
        st.rerun()

uploaded_file = st.file_uploader("공부할 페이지 이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

if uploaded_file:
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.image(uploaded_file, caption="학습 자료 원본", use_container_width=True)
    with col2:
        if st.button("🚀 전체 분석 시작", type="primary", use_container_width=True):
            with st.spinner("원문을 정밀하게 읽어오고 있습니다. 잠시만 기다려주세요..."):
                img_base64 = process_and_encode_image(uploaded_file)
                st.session_state.analysis_result = analyze_image(img_base64)
        
        if st.session_state.analysis_result:
            st.markdown(st.session_state.analysis_result)
            st.divider()
            
            st.subheader("💬 추가 질문하기")
            for chat in st.session_state.chat_history:
                with st.chat_message(chat["role"]): st.write(chat["content"])
            
            if prompt := st.chat_input("이 페이지 내용 중 더 궁금한 점이 있나요?"):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.write(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("답변 생성 중..."):
                        answer = ask_follow_up(prompt, st.session_state.analysis_result)
                        st.write(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})

st.divider()
st.caption("간호학 대학원 학습 지원 모드 | Powered by GPT-4o")
