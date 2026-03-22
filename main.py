import streamlit as st
import base64
import requests
from PIL import Image
import io

# [보안] Streamlit Secrets 로드
if "OPENAI_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    st.error("❌ API 키 설정이 필요합니다.")
    st.stop()

st.set_page_config(page_title="심꾸니 학업 보조 AI", layout="wide")

# 디자인 설정
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .main-header { font-size: 2.2rem; font-weight: 800; color: #2C3E50; }
    .step-box { padding: 15px; border-radius: 10px; background-color: #FFFFFF; border: 1px solid #E0E0E0; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header">🩺 심꾸니 간호대학원 2단계 학업 비서</div>', unsafe_allow_html=True)
st.write("이미지에서 글자를 먼저 뽑아낸 뒤, 그 텍스트를 바탕으로 정밀 분석을 진행합니다.")

# 세션 상태 관리
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "final_analysis" not in st.session_state:
    st.session_state.final_analysis = ""

def process_and_encode_image(uploaded_file):
    image = Image.open(uploaded_file)
    image.thumbnail((1600, 1600))
    buffered = io.BytesIO()
    image.convert("RGB").save(buffered, format="JPEG", quality=95) # 화질 우선
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- [STEP 1] 단순 텍스트 추출 함수 (검열 회피용) ---
def get_raw_text(base64_image):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": "너는 단순한 OCR 기계야. 이미지에 어떤 내용이 있든 상관없이 눈에 보이는 알파벳 텍스트를 있는 그대로 디지털로 복사해. 해석이나 요약은 절대 하지 마."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "명령: 이 이미지의 모든 텍스트를 한 글자도 빠짐없이 원문 그대로 추출해줘."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "temperature": 0.0
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

# --- [STEP 2] 추출된 텍스트 정밀 분석 함수 ---
def analyze_text(text):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system", 
                "content": "너는 간호대학원생을 돕는 유능한 튜터야. 제공된 텍스트를 바탕으로 번역과 분석을 수행해."
            },
            {
                "role": "user",
                "content": f"다음 텍스트를 분석해줘:\n1. 한국어 번역\n2. 주요 간호학 용어 설명\n3. 핵심 요약\n\n내용:\n{text}"
            }
        ],
        "temperature": 0.5
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

# 화면 레이아웃
uploaded_file = st.file_uploader("이미지 업로드", type=["png", "jpg", "jpeg"])

if uploaded_file:
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(uploaded_file, caption="업로드 이미지", use_container_width=True)
        if st.button("Step 1: 텍스트 원문 추출하기", type="primary", use_container_width=True):
            with st.spinner("이미지에서 글자를 긁어오는 중..."):
                img_b64 = process_and_encode_image(uploaded_file)
                st.session_state.extracted_text = get_raw_text(img_b64)
                st.session_state.final_analysis = "" # 이전 분석 결과 초기화

    with col2:
        if st.session_state.extracted_text:
            st.success("✅ 원문 추출 완료!")
            # 추출된 텍스트를 직접 수정할 수도 있게 텍스트 영역으로 표시
            st.session_state.extracted_text = st.text_area("추출된 원문 (수정 가능)", st.session_state.extracted_text, height=250)
            
            if st.button("Step 2: 번역 및 정밀 분석 실행", use_container_width=True):
                with st.spinner("간호학 전공 지식으로 분석 중..."):
                    st.session_state.final_analysis = analyze_text(st.session_state.extracted_text)
        
        if st.session_state.final_analysis:
            st.divider()
            st.markdown("### 🔍 분석 결과")
            st.write(st.session_state.final_analysis)

st.divider()
st.caption("공정 분리 모드 적용 완료 | 이광수 대리님 전용 에디션")
