# -*- coding: utf-8 -*-

# ===== 라이브러리 임포트 =====
import streamlit as st
import pandas as pd
import plotly.express as px

# ===== 페이지 환경 설정 =====
# Streamlit 앱에서 가장 먼저 실행되어야 하는 레이아웃 및 타이틀 설정
st.set_page_config(page_title="Titanic 대시보드", layout="wide")

# ===== 데이터 로드 및 캐싱 =====
@st.cache_data
def load_data():
    # csv 파일을 읽어와 데이터프레임으로 반환합니다.
    return pd.read_csv("titanic.csv")

df = load_data()

# ===== 기존 정의 함수 구역 =====
def filter_data(df, sexes, classes, age_range):
    # 성별, 객실등급을 기준으로 데이터를 1차 필터링합니다.
    # 만약 나이 슬라이더가 전체 범위(0~80)이면 나이 결측 승객(NaN)도 필터에 포함시킵니다. [수정]
    if age_range[0] == 0 and age_range[1] == 80:
        condition = (
            df['sex'].isin(sexes) &
            df['pclass'].isin(classes) &
            ((df['age'] >= age_range[0]) & (df['age'] <= age_range[1]) | df['age'].isna())  # [수정]
        )
    else:
        condition = (
            df['sex'].isin(sexes) &
            df['pclass'].isin(classes) &
            (df['age'] >= age_range[0]) &
            (df['age'] <= age_range[1])
        )
    return df[condition]

def kpi(df):
    # 대시보드 KPI 카드에 사용할 승객 수, 생존율, 평균 나이를 계산합니다.
    if df.empty:
        return 0, 0, 0
    passenger_count = len(df)
    survival_rate = round(df['survived'].mean() * 100, 1)
    average_age = round(df['age'].mean(), 1)
    if pd.isna(average_age):
        average_age = 0.0
    return passenger_count, survival_rate, average_age

def class_rate_bar(df):
    # 객실 등급별 생존율 막대그래프를 생성합니다.
    df_survival = df.groupby('pclass')['survived'].mean().reset_index()
    df_survival['survived'] = round(df_survival['survived'] * 100, 1)
    fig = px.bar(
        df_survival,
        x='pclass',
        y='survived',
        text='survived',
        title='객실 등급별 생존율 (%)',
        labels={'pclass': '객실 등급', 'survived': '생존율 (%)'}
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(xaxis=dict(tickmode='array', tickvals=[1, 2, 3]))
    return fig

def age_hist(df):
    # 생존 여부에 따른 나이 분포 히스토그램을 생성합니다.
    fig = px.histogram(
        df,
        x='age',
        color='survived',
        barmode='overlay',
        opacity=0.6,
        title='생존 여부에 따른 나이 분포',
        labels={'age': '나이', 'survived': '생존 여부', 'count': '승객 수'}
    )
    return fig

# ===== 사이드바 필터 설정 =====
st.sidebar.header("필터 조건 설정")

# 1. 성별 멀티셀렉트 (기본값으로 모든 성별 선택)
unique_sexes = df['sex'].unique().tolist()
selected_sexes = st.sidebar.multiselect("성별 선택", unique_sexes, default=unique_sexes)

# 2. 객실 등급 멀티셀렉트 (기본값으로 모든 등급 선택)
unique_classes = sorted(df['pclass'].unique().tolist())
selected_classes = st.sidebar.multiselect("객실 등급 선택", unique_classes, default=unique_classes)

# 3. 나이 선택 슬라이더 (0세부터 80세까지)
selected_age_range = st.sidebar.slider("나이 범위 선택", 0, 80, (0, 80))

# ===== 예외 처리: 성별이나 객실 등급이 하나도 선택되지 않은 경우 [수정] =====
if not selected_sexes or not selected_classes:  # [수정]
    st.warning("⚠️ 성별과 객실 등급을 최소 하나 이상 선택해 주세요.")  # [수정]
    st.stop()  # [수정]

# ===== 데이터 필터 및 본문 출력 =====
# 사이드바 필터 조건을 적용하여 데이터를 정제합니다.
filtered_df = filter_data(df, selected_sexes, selected_classes, selected_age_range)

# ===== 예외 처리: 필터링 결과가 0명인 경우 [수정] =====
if filtered_df.empty:  # [수정]
    st.warning("⚠️ 조건에 맞는 승객이 없습니다.")  # [수정]
    st.stop()  # [수정]

# 메인 타이틀 표시
st.title("타이타닉, 누가 살아남았나?")

# KPI 카드에 출력할 데이터 계산
p_count, s_rate, a_age = kpi(filtered_df)

# 가로로 정렬된 3개의 컬럼 영역 생성
col1, col2, col3 = st.columns(3)

# 각 컬럼에 계산된 지표 메트릭 배치
col1.metric("승객 수", f"{p_count} 명")
col2.metric("생존율", f"{s_rate} %")
col3.metric("평균 나이", f"{a_age} 세")

# ===== 차트 시각화 구역 =====
# KPI 지표 아래 차트를 가로로 병렬 배치하기 위해 2개의 컬럼 생성
chart_col1, chart_col2 = st.columns(2)

# 왼쪽 컬럼에 객실 등급별 생존율 차트 출력
with chart_col1:
    fig_bar = class_rate_bar(filtered_df)
    st.plotly_chart(fig_bar, use_container_width=True)

# 오른쪽 컬럼에 생존 여부에 따른 나이 분포 차트 출력
with chart_col2:
    fig_hist = age_hist(filtered_df)
    st.plotly_chart(fig_hist, use_container_width=True)

# ===== 상세 데이터 조회 구역 =====
# 접이식 Expander 안에 필터링된 데이터 테이블을 표 형태로 노출
with st.expander("🔍 데이터 보기"):
    st.dataframe(filtered_df, use_container_width=True)
