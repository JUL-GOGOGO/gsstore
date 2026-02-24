import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib
import os
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="경기도 편의점 현황 EDA 대시보드",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 적용 (프리미엄 컨설팅 스타일)
st.markdown("""
    <style>
    .main {
        background-color: #ffffff;
    }
    .stHeading h1 {
        color: #004098;
        font-family: 'Malgun Gothic', sans-serif;
        border-bottom: 2px solid #004098;
        padding-bottom: 10px;
    }
    .stHeading h2 {
        color: #004098;
        margin-top: 30px;
    }
    .stAlert {
        background-color: #f0f4fa;
        border-left: 5px solid #004098;
    }
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로드 환경 설정
BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "rest_area_data.csv"
IMAGE_DIR = BASE_DIR / "images"

def read_csv_safely(file_path, separators=[',', '\t', ';']):
    """다양한 인코딩과 구분자를 시도하여 CSV 파일을 안전하게 읽는 함수"""
    encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
    
    for encoding in encodings:
        for sep in separators:
            try:
                # 데이터 유효성 검사를 위해 샘플링 로드 시도
                df = pd.read_csv(file_path, encoding=encoding, sep=sep, nrows=5)
                # 성공하면 전체 로드
                return pd.read_csv(file_path, encoding=encoding, sep=sep)
            except Exception:
                continue
    
    # 모든 시도가 실패할 경우의 폴백 (latin1 및 errors='replace')
    try:
        return pd.read_csv(file_path, encoding='latin1', sep=None, engine='python', on_bad_lines='skip')
    except Exception as e:
        st.error(f"파일을 읽는 데 실패했습니다: {e}")
        return None

@st.cache_data
def load_data():
    if DATA_PATH.exists():
        return read_csv_safely(DATA_PATH)
    return None

def main():
    st.title("🏪 경기도 편의점 현황 심층 분석 대시보드")
    st.markdown("### 데이터 기반의 권역별 성장 로드맵 및 운영 효율화 인사이트")

    df = load_data()

    if df is not None:
        # 사이드바 필터
        st.sidebar.header("🔍 분석 필터")
        cities = sorted(df['시군명'].unique().tolist()) if '시군명' in df.columns else []
        selected_city = st.sidebar.multiselect("시군 선택", options=cities, default=cities[:5] if cities else [])

        # 데이터 필터링
        filtered_df = df.copy()
        if selected_city:
            filtered_df = filtered_df[filtered_df['시군명'].isin(selected_city)]

        # 탭 구성
        tab1, tab2, tab3 = st.tabs(["📊 분석 요약", "📍 지역별 상세", "🖼️ 시각화 갤러리"])

        with tab1:
            st.header("1. 분석 개요 및 핵심 KPI")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 점포 수", f"{len(df):,}개")
            with col2:
                brand_count = df[df['사업장명'].str.contains('CU|GS25|세븐일레븐|이마트24', na=False, case=False)].shape[0] if '사업장명' in df.columns else 0
                st.metric("주요 브랜드 점포", f"{brand_count:,}개")
            with col3:
                city_count = len(df['시군명'].unique()) if '시군명' in df.columns else 0
                st.metric("분석 대상 시군", f"{city_count}개")
            with col4:
                operating_count = df[df['영업상태명'] == '영업/정상'].shape[0] if '영업상태명' in df.columns else len(df)
                st.metric("정상 영업 비중", f"{(operating_count/len(df)*100):.1f}%")

            st.info("""
            **핵심 인사이트:** 
            - 경기도 내 편의점 시장은 상위 4대 브랜드 중심의 강력한 과점 체제를 형성하고 있습니다.
            - 인구 밀집도가 높은 남부권(화성, 수원 등)에 점포가 집중되어 있으며, 신규 출점보다는 브랜드 전환 전략이 유효한 시점입니다.
            """)

            # 리포트 요약 표시
            st.subheader("📋 EDA 리포트 주요 내용")
            st.markdown("""
            1. **시장 집중도**: 상위 4대 브랜드가 시장의 대부분을 점유하고 있어 프랜차이즈 비중이 압도적임.
            2. **지역 거점 전략**: 남부권 시군에 점포가 집중되어 있으며, 이는 소비 수요와 직결됨.
            3. **지속적 성장**: 시장 포화에도 불구하고 브랜드 간의 출점 경쟁은 연도별로 지속되는 경향을 보임.
            """)

        with tab2:
            st.header("2. 지역별 상세 현황")
            if '시군명' in filtered_df.columns:
                city_stats = filtered_df['시군명'].value_counts().reset_index()
                city_stats.columns = ['시군명', '점포 수']
                
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.bar_chart(city_stats.set_index('시군명'))
                with col_right:
                    st.dataframe(city_stats, use_container_width=True)

        with tab3:
            st.header("3. 심층 시각화 결과 (EDA Report)")
            
            image_list = [
                ("01_brand_share.png", "브랜드 점유율 분석"),
                ("02_brand_counts.png", "브랜드별 점포 수 현황"),
                ("03_city_distribution.png", "시군별 점포 분포"),
                ("06_geographic_distribution.png", "지리적 분포 Scatter Map"),
                ("04_yearly_permits.png", "연도별 인허가 추이"),
                ("08_brand_yearly_heatmap.png", "브랜드별 연도별 히트맵"),
                ("07_city_brand_stacked.png", "주요 시군별 브랜드 구성")
            ]

            for img_name, caption in image_list:
                img_path = IMAGE_DIR / img_name
                if img_path.exists():
                    st.subheader(caption)
                    st.image(str(img_path), use_container_width=True)
                    st.divider()
                else:
                    st.warning(f"이미지 파일을 찾을 수 없습니다: {img_name}")

    else:
        st.error("데이터 파일을 찾을 수 없습니다. `data/rest_area_data.csv` 경로를 확인해주세요.")

if __name__ == "__main__":
    main()
