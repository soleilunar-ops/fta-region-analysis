import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import os

# -----------------------------------------------------------
# 1. 기본 설정
# -----------------------------------------------------------
st.set_page_config(page_title="자유무역지역 현황", layout="wide")
sns.set_style("white")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['axes.unicode_minus'] = False

font_path = 'NanumGothic.ttf'
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
else:
    if os.name == 'nt': plt.rc('font', family='Malgun Gothic')
    elif os.name == 'posix': plt.rc('font', family='AppleGothic')
    else: plt.rc('font', family='NanumGothic')

# -----------------------------------------------------------
# 2. 데이터 로드 함수 (UI 코드 제거됨)
# -----------------------------------------------------------
@st.cache_data
def load_and_fix_data(file_path):
    df = None
    
    # 1. UTF-8 시도
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except:
        # 2. CP949 시도
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except:
            pass

    # 3. 에러 무시하고 읽기
    if df is None:
        try:
            df = pd.read_csv(file_path, encoding='utf-8', encoding_errors='ignore')
        except:
            df = pd.read_csv(file_path, encoding='cp949', encoding_errors='ignore')

    if df is None:
        raise ValueError("파일을 도저히 읽을 수 없습니다.")

    # --- 컬럼 복구 로직 ---
    
    df.columns = df.columns.astype(str).str.replace(' ', '').str.strip()

    # 연도 컬럼 찾기
    year_col_name = None
    for col in df.columns:
        try:
            temp = pd.to_numeric(df[col], errors='coerce')
            if temp.between(1970, 2030).any():
                year_col_name = col
                break
        except:
            continue
            
    if year_col_name:
        df = df.rename(columns={year_col_name: '연도'})
    else:
        df = df.rename(columns={df.columns[0]: '연도'})

    # 깨짐 여부 확인
    current_headers = "".join(df.columns)
    is_broken = "占" in current_headers or "ï" in current_headers or "" in current_headers

    if is_broken:
        # 데이터 구조 재구축
        regions_order = ['마산', '대불', '율촌', '김제', '울산', '군산', '동해']
        metrics_order = ['수출', '수입', '수지', '고용', '업체']
        
        new_columns = ['연도']
        for region in regions_order:
            for metric in metrics_order:
                new_columns.append(f"{region}_{metric}")
        
        if len(df.columns) == len(new_columns):
            df.columns = new_columns
        else:
            limit = min(len(df.columns), len(new_columns))
            df.columns = new_columns[:limit] + list(df.columns[limit:])

    # 숫자 데이터 정리
    df['연도'] = pd.to_numeric(df['연도'], errors='coerce').fillna(0).astype(int)
    df = df[df['연도'] > 0]
    
    # [수정됨] 여기서 st.toast를 하지 않고, 복구 여부(is_broken)를 리턴합니다.
    return df, is_broken

# -----------------------------------------------------------
# 3. 메인 로직
# -----------------------------------------------------------
st.title("📊 자유무역지역 수출입 및 고용 현황")

current_dir = os.path.dirname(os.path.abspath(__file__))
file_name = "산업통상부_자유무역지역 수출입실적 현황_20231231.csv"
file_path = os.path.join(current_dir, file_name)

try:
    if not os.path.exists(file_path):
        st.error(f"❌ 파일을 찾을 수 없습니다: {file_path}")
    else:
        # [수정됨] 함수에서 데이터와 복구 여부를 함께 받습니다.
        df, was_fixed = load_and_fix_data(file_path)

        # [수정됨] UI 알림은 함수 밖에서 실행합니다. (에러 해결 핵심)
        if was_fixed:
            st.toast("✅ 깨진 컬럼명을 자동으로 복구했습니다!", icon="🛠️")

        # --- 사이드바 ---
        st.sidebar.header("🔍 설정")
        regions = ['마산', '대불', '율촌', '김제', '울산', '군산', '동해']
        selected_region = st.sidebar.selectbox("지역 선택", regions)

        min_y, max_y = int(df['연도'].min()), int(df['연도'].max())
        year_range = st.sidebar.slider("연도 범위", min_y, max_y, (2010, 2023))

        # --- 데이터 필터링 ---
        money_cols = ['수출', '수입', '수지']
        count_cols = ['고용', '업체']
        
        target_money = [c for c in df.columns if selected_region in c and any(m in c for m in money_cols)]
        target_count = [c for c in df.columns if selected_region in c and any(c_key in c for c_key in count_cols)]

        mask = (df['연도'] >= year_range[0]) & (df['연도'] <= year_range[1])
        plot_df = df.loc[mask].sort_values('연도')

        # --- 시각화 ---
        st.subheader(f"✨ {selected_region} 지역 상세 분석")

        if not target_money and not target_count:
            st.warning("데이터 매칭 실패. 컬럼 이름을 확인해주세요.")
            st.write(df.columns.tolist())
        else:
            fig, ax1 = plt.subplots(figsize=(14, 8))

            # 1. 막대 그래프
            if target_money:
                melted = plot_df.melt(id_vars='연도', value_vars=target_money, var_name='항목', value_name='금액')
                melted['항목'] = melted['항목'].str.replace(f"{selected_region}_", "")
                sns.barplot(data=melted, x='연도', y='금액', hue='항목', ax=ax1, palette='Blues_d', alpha=0.7)
                ax1.legend(loc='upper left', ncol=3, frameon=False)
            
            ax1.set_ylabel("금액 (천달러)", fontsize=12, fontweight='bold', color='navy')
            ax1.grid(axis='y', linestyle='--', alpha=0.5)

            # 2. 선 그래프
            ax2 = ax1.twinx()
            colors = {'고용': 'firebrick', '업체': 'orange'}
            markers = {'고용': 'o', '업체': 's'}

            for col in target_count:
                key = '고용' if '고용' in col else '업체'
                sns.lineplot(x=ax1.get_xticks(), y=plot_df[col], ax=ax2, 
                             marker=markers.get(key, 'o'), 
                             color=colors.get(key, 'black'), 
                             linewidth=3, label=key)

            ax2.set_ylabel("")
            ax2.text(1.0, -0.08, "인원 / 업체수", transform=ax2.transAxes, 
                     ha="right", va="top", fontsize=11, fontweight='bold', color='firebrick')
            ax2.legend(loc='upper right', ncol=2, frameon=False)
            
            plt.title(f"{selected_region} 연도별 주요 실적 추이", fontsize=20, fontweight='bold', y=1.05)
            st.pyplot(fig)

            with st.expander("데이터 상세 보기"):
                st.dataframe(plot_df[['연도'] + target_money + target_count])

except Exception as e:
    st.error(f"❌ 오류 발생: {e}")