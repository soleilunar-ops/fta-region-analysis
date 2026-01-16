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
    # [최종 해결책] 엔진 변경 및 컬럼 강제 지정
    # -----------------------------------------------------------
    # 1. engine='python'을 쓰면 인코딩 오류를 훨씬 잘 견딥니다.
    # 2. 깨진 글자가 있어도 일단 불러오게 합니다.
    try:
        df = pd.read_csv(file_path, encoding='cp949', engine='python')
    except:
        df = pd.read_csv(file_path, encoding='euc-kr', engine='python')

    # [중요] 컬럼 이름이 깨져있을 것이 확실하므로, 우리가 아는 이름으로 강제로 덮어씌웁니다.
    # 데이터 구조: 맨 앞 '연도' + 7개 지역 * 5개 항목 = 총 36개 컬럼
    
    regions_order = ['마산', '대불', '율촌', '김제', '울산', '군산', '동해'] # 데이터 원본 순서
    metrics_order = ['수출실적(천달러)', '수입실적(천달러)', '무역수지(천달러)', '고용인원', '업체수']
    
    new_columns = ['연도']
    for reg in regions_order:
        for met in metrics_order:
            new_columns.append(f"{reg}_{met}")
            
    # 파일의 컬럼 개수와 우리가 만든 이름 개수가 맞는지 확인 후 덮어쓰기
    if len(df.columns) == len(new_columns):
        df.columns = new_columns
        # st.success("✅ 깨진 컬럼 이름을 자동으로 복구했습니다!") # (확인용, 주석처리 가능)
    else:
        # 만약 컬럼 개수가 다르면 어쩔 수 없이 원본 사용 (이 경우엔 파일 확인 필요)
        st.warning(f"⚠️ 컬럼 개수 불일치! (파일: {len(df.columns)}개 vs 예상: {len(new_columns)}개)")

    # -----------------------------------------------------------

    # --- 사이드바 설정 ---
    st.sidebar.header("🔍 검색 필터")
    # 사용자가 선택할 지역 리스트 (사이드바용)
    select_regions = ['마산', '대불', '율촌', '김제', '울산', '군산', '동해']
    selected_region = st.sidebar.selectbox("분석 지역 선택", select_regions)
    
    # 연도 데이터 정제
    df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
    df = df.dropna(subset=['연도'])
    df['연도'] = df['연도'].astype(int)

    year_range = st.sidebar.slider("연도 범위", 
                                   int(df['연도'].min()), 
                                   int(df['연도'].max()), 
                                   (2010, 2023))

    # --- 데이터 가공 ---
    money_metrics = ['수출실적(천달러)', '수입실적(천달러)', '무역수지(천달러)']
    count_metrics = ['고용인원', '업체수']
    
    # 데이터 필터링
    target_df = df[df['연도'].between(year_range[0], year_range[1])].copy()
    
    plot_df = pd.DataFrame({'연도': target_df['연도']})
    for m in money_metrics + count_metrics:
        # 컬럼명을 위에서 강제로 통일했으므로 이제 무조건 찾을 수 있습니다.
        col_name = f"{selected_region}_{m}"
        plot_df[m] = target_df[col_name]

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

    