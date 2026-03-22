import streamlit as st
import base64
import requests

# [보안 업데이트] GitHub에 키가 노출되지 않도록 st.secrets를 사용합니다.
# 실제 키는 배포 후 Streamlit Cloud 설정(Secrets)에 넣으셔야 합니다.
if "OPENAI_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    st.error("❌ API 키가 설정되지 않았습니다. Streamlit Secrets에 'OPENAI_API_KEY'를 추가해주세요.")
    st.stop()

st.set_page_config(page_title="Premium AI Analyzer", layout="wide")

# 스타일 및 헤더 (기존 유지)
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

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

# GPT-4o 분석 함수 (기본 유지)
def analyze_image(base64_image):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "너는 전문 번역가이자 문서 분석가야. 이미지의 내용을 정확하게 텍스트로 추출하고 분석해줘."},
            {"role": "user", "content": [
                {"type": "text", "text": "1. [Full Text]: 영문 텍스트 추출\n2. [Translation]: 매끄러운 한국어 번역\n3. [Key Points]: 핵심 요약"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        "max_tokens": 2000
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

# 추가 질문 처리 함수 (가성비 모델 gpt-4o-mini 권장하나 원본대로 유지)
def ask_follow_up(question, context):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": f"너는 다음 분석 결과를 바탕으로 사용자의 질문에 답하는 어시스턴트야: {context}"},
            {"role": "user", "content": question}
        ]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

# 메인 UI 및 사이드바 (기존 유지)
with st.sidebar:
    st.header("📋 User Guide")
    st.info("1. 이미지 업로드\n2. Run Analysis 클릭\n3. 추가 질문 가능")
    if st.button("Clear History"):
        st.session_state.chat_history = []
        st.session_state.analysis_result = None
        st.rerun()

uploaded_file = st.file_uploader("이미지 파일 선택", type=["png", "jpg", "jpeg"])

if uploaded_file:
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.image(uploaded_file, use_container_width=True)
    with col2:
        if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
            with st.spinner("분석 중..."):
                uploaded_file.seek(0)
                img_base64 = encode_image(uploaded_file)
                st.session_state.analysis_result = analyze_image(img_base64)
        
        if st.session_state.analysis_result:
            st.markdown(st.session_state.analysis_result)
            st.divider()
            for chat in st.session_state.chat_history:
                with st.chat_message(chat["role"]): st.write(chat["content"])
            if prompt := st.chat_input("이 문서에 대해 더 궁금한 점이 있나요?"):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.write(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("생각 중..."):
                        answer = ask_follow_up(prompt, st.session_state.analysis_result)
                        st.write(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})

st.divider()
st.caption("Powered by GPT-4o | Specialized for Professional Analysis")
