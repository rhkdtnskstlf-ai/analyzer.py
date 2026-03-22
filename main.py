import streamlit as st
import base64
import requests
from PIL import Image
import io

# [보안] Streamlit Secrets에서 키를 불러옵니다.
if "OPENAI_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    st.error("❌ API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets 설정을 확인해주세요.")
    st.stop()

st.set_page_config(page_title="심꾸니 Premium AI Analyzer", layout="wide")

# 스타일 적용
st.markdown("""
    <style>
    .stApp { background-color: #FAFAFA; }
    .main-header { font-size: 2.2rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header">📄 심꾸니 Premium AI Document Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">이미지를 업로드하면 정밀 분석 후 대화형 가이드를 제공합니다.</div>', unsafe_allow_html=True)

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# [성능 개선] 이미지 최적화 및 인코딩 함수
def process_and_encode_image(uploaded_file):
    image = Image.open(uploaded_file)
    # 이미지가 너무 크면 분석 속도가 느려지므로 리사이징 (최대 1280px)
    image.thumbnail((1280, 1280))
    
    buffered = io.BytesIO()
    # JPEG로 압축하여 전송 속도 향상
    image.convert("RGB").save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# GPT-4o 분석 함수
def analyze_image(base64_image):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": "너는 전문 번역가이자 문서 분석가야. 이미지의 내용을 정확하게 추출하고 사용자가 이해하기 쉽게 분석해줘."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "1. [Full Text]: 모든 영문 텍스트 추출\n2. [Translation]: 자연스러운 한국어 번역\n3. [Key Points]: 핵심 내용 3줄 요약"
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 2000
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

# 추가 질문 처리 함수 (속도를 위해 gpt-4o-mini 권장)
def ask_follow_up(question, context):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"다음 분석 결과를 참고해서 답변해줘: {context}"},
            {"role": "user", "content": question}
        ]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

# 사이드바
with st.sidebar:
    st.header("📋 User Guide")
    st.info("1. 이미지 업로드\n2. 'Run Analysis' 클릭\n3. 궁금한 점 채팅 질문")
    if st.button("Clear History"):
        st.session_state.chat_history = []
        st.session_state.analysis_result = None
        st.rerun()

# 메인 화면
uploaded_file = st.file_uploader("이미지 파일을 선택하세요 (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("🖼️ Source Image")
        st.image(uploaded_file, use_container_width=True)
        
    with col2:
        st.subheader("🔍 Analysis Result")
        if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
            with st.spinner("이미지 최적화 및 분석 중..."):
                img_base64 = process_and_encode_image(uploaded_file)
                st.session_state.analysis_result = analyze_image(img_base64)
        
        if st.session_state.analysis_result:
            st.markdown(st.session_state.analysis_result)
            st.divider()
            
            st.subheader("💬 Ask more about this document")
            for chat in st.session_state.chat_history:
                with st.chat_message(chat["role"]):
                    st.write(chat["content"])
            
            if prompt := st.chat_input("문서에 대해 더 궁금한 점이 있나요?"):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("답변 생성 중..."):
                        answer = ask_follow_up(prompt, st.session_state.analysis_result)
                        st.write(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})

st.divider()
st.caption("Powered by GPT-4o & 4o-mini | Optimized for Speed")
