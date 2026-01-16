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
    # -----------------------------------------------------------
    # [수정된 부분] 인코딩 자동 감지 로직 적용
    # -----------------------------------------------------------
    try:
        # 1. 먼저 utf-8로 시도 (요즘 표준)
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            # 2. 실패하면 cp949로 시도 (윈도우 엑셀 저장 방식)
            df = pd.read_csv(file_path, encoding='cp949')
        except UnicodeDecodeError:
            # 3. 그것도 안 되면 euc-kr로 시도 (옛날 방식)
            df = pd.read_csv(file_path, encoding='euc-kr')
    # -----------------------------------------------------------

    # --- 사이드바 설정 ---
    st.sidebar.header("🔍 검색 필터")
    regions = ['마산', '대불', '율촌', '김제', '울산', '군산', '동해']
    selected_region = st.sidebar.selectbox("분석 지역 선택", regions)
    year_range = st.sidebar.slider("연도 범위", 
                                   int(df['연도'].min()), 
                                   int(df['연도'].max()), 
                                   (2010, 2023))

    # --- 데이터 가공 ---
    money_metrics = ['수출실적(천달러)', '수입실적(천달러)', '무역수지(천달러)']
    count_metrics = ['고용인원', '업체수']
    
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
    
    # [수정 3] 중앙 우측 '고용인원' 글자 제거 (빈 문자열로 설정)
    ax2.set_ylabel('') 

    # [수정 2] '인원 / 업체수'를 우측 하단(하늘색 위치)으로 이동 (가로 정렬)
    # (1.0, -0.08) 좌표는 그래프 오른쪽 끝 아래를 의미합니다.
    ax2.text(1.0, -0.08, "인원 / 업체수", transform=ax2.transAxes, 
             ha="right", va="top", rotation=0, 
             fontsize=12, fontweight='bold', color='firebrick')

    ax2.legend(loc='upper right', bbox_to_anchor=(1, 1.15), ncol=2, frameon=False, prop={'family': plt.rcParams['font.family']})
    
    # [수정 1] 제목 위치 조정 (pad를 50 -> 20으로 줄여서 아래로 내림)
    plt.title(f"{selected_region} 연도별 주요 실적 추이", fontsize=20, fontweight='bold', pad=20)
    ax1.set_xlabel("조회 연도")
    
    st.pyplot(fig)

    # --- 하단 데이터 표 ---
    with st.expander("데이터 상세 보기"):
        st.table(plot_df.sort_values(by='연도', ascending=False))

except FileNotFoundError:
    st.error(f"❌ 데이터 파일을 찾을 수 없습니다: {file_path}")
    st.info("GitHub 저장소에 파일이 제대로 올라갔는지(0kb가 아닌지) 확인해주세요.")
except Exception as e:
    st.error(f"❌ 오류가 발생했습니다: {e}")