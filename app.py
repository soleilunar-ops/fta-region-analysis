import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import os

# -----------------------------------------------------------
# 1. Streamlit 페이지 설정
# -----------------------------------------------------------
st.set_page_config(page_title="자유무역지역 현황", layout="wide")

# -----------------------------------------------------------
# 2. 시각화 스타일 및 폰트 설정
# -----------------------------------------------------------
sns.set_style("white") 
plt.rcParams['figure.dpi'] = 150 

font_path = 'NanumGothic.ttf' 

if os.path.exists(font_path):
    fm.fontManager.addfont(font_path) 
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name) 
else:
    plt.rc('font', family='Malgun Gothic') 

plt.rcParams['axes.unicode_minus'] = False

# -----------------------------------------------------------
# 3. 메인 앱 로직
# -----------------------------------------------------------
st.title("📊 자유무역지역 수출입 및 고용 현황")

file_path = "산업통상부_자유무역지역 수출입실적 현황_20231231.csv"

try:
    # --- 데이터 로드 및 컬럼 검증 (안전장치 추가) ---
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='euc-kr')

    # [중요] 컬럼명 앞뒤 공백 제거 (예: '연도 ' -> '연도')
    df.columns = df.columns.str.strip()

    # '연도' 컬럼 확인
    if '연도' not in df.columns:
        st.error("🚨 데이터에서 '연도' 컬럼을 찾을 수 없습니다!")
        st.write("현재 파일에 있는 컬럼 목록입니다. 아래 이름 중 하나여야 합니다:")
        st.write(list(df.columns))
        st.stop() # 프로그램 중단하고 오류 메시지 보여줌

    # --- 사이드바 설정 ---
    st.sidebar.header("🔍 검색 필터")
    regions = ['마산', '대불', '율촌', '김제', '울산', '군산', '동해']
    selected_region = st.sidebar.selectbox("분석 지역 선택", regions)
    
    # 연도 데이터 정수형 변환 (혹시 모를 에러 방지)
    df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
    df = df.dropna(subset=['연도']) # 연도가 숫자가 아닌 행 제거
    df['연도'] = df['연도'].astype(int)

    year_range = st.sidebar.slider("연도 범위", 
                                   int(df['연도'].min()), 
                                   int(df['연도'].max()), 
                                   (2010, 2023))

    # --- 데이터 가공 ---
    money_metrics = ['수출실적(천달러)', '수입실적(천달러)', '무역수지(천달러)']
    count_metrics = ['고용인원', '업체수']
    
    # 해당 지역의 컬럼이 실제로 있는지 확인
    expected_cols = [f"{selected_region}_{m}" for m in money_metrics + count_metrics]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"🚨 선택한 지역({selected_region})의 데이터 컬럼이 없습니다.")
        st.write(f"없는 컬럼: {missing_cols}")
        st.stop()

    target_df = df[df['연도'].between(year_range[0], year_range[1])].copy()
    
    plot_df = pd.DataFrame({'연도': target_df['연도']})
    for m in money_metrics + count_metrics:
        plot_df[m] = target_df[f"{selected_region}_{m}"]

    # --- 그래프 그리기 ---
    st.subheader(f"✨ {selected_region} 지역 종합 분석(금액, 인원, 업체)")
    
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # [왼쪽 축] 막대 그래프 (금액)
    df_money = plot_df.melt(id_vars='연도', value_vars=money_metrics, var_name='항목', value_name='금액')
    sns.barplot(data=df_money, x='연도', y='금액', hue='항목', ax=ax1, palette='Blues_d', alpha=0.7)
    
    ax1.set_ylabel("금액 (천달러)", fontsize=12, fontweight='bold', color='navy')
    ax1.legend(loc='upper left', bbox_to_anchor=(0, 1.15), ncol=3, frameon=False, prop={'family': plt.rcParams['font.family']})
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # [오른쪽 축] 선 그래프 (인원/업체수)
    ax2 = ax1.twinx()
    
    sns.lineplot(data=plot_df, x=ax1.get_xticks(), y='고용인원', ax=ax2, 
                 marker='o', color='firebrick', linewidth=3, label='고용인원')
    sns.lineplot(data=plot_df, x=ax1.get_xticks(), y='업체수', ax=ax2, 
                 marker='s', color='orange', linewidth=3, label='업체수')
    
    ax2.set_ylabel('') 
    ax2.text(1.0, -0.08, "인원 / 업체수", transform=ax2.transAxes, 
             ha="right", va="top", rotation=0, 
             fontsize=12, fontweight='bold', color='firebrick')

    ax2.legend(loc='upper right', bbox_to_anchor=(1, 1.15), ncol=2, frameon=False, prop={'family': plt.rcParams['font.family']})
    
    plt.title(f"{selected_region} 연도별 주요 실적 추이", fontsize=20, fontweight='bold', pad=20)
    ax1.set_xlabel("조회 연도")
    
    st.pyplot(fig)

    # --- 하단 데이터 표 ---
    with st.expander("데이터 상세 보기"):
        st.table(plot_df.sort_values(by='연도', ascending=False))

except FileNotFoundError:
    st.error(f"❌ 데이터 파일을 찾을 수 없습니다: {file_path}")
except Exception as e:
    st.error(f"❌ 오류가 발생했습니다: {e}")