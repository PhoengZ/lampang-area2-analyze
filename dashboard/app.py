import streamlit as st
import pandas as pd
import numpy as np  # noqa: F401
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from scipy import stats
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE
import os

st.set_page_config(page_title="Lampang Area 2 Election Dashboard", layout="wide", page_icon="🗳️")

# --- Data Loading ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "dewwts-analyze", "cleaned")
SOCIO_DIR = os.path.join(os.path.dirname(__file__), "..", "dewwts-analyze", "socioeconomic_data")

@st.cache_data
def load_data():
    results = pd.read_csv(os.path.join(DATA_DIR, "master_results_cleaned.csv"))
    summary = pd.read_csv(os.path.join(DATA_DIR, "master_summary_cleaned.csv"))
    coords = pd.read_csv(os.path.join(DATA_DIR, "coords_cleaned.csv"))
    pop_age = pd.read_csv(os.path.join(DATA_DIR, "pop_age_by_tambon.csv"))
    cand_66 = pd.read_csv(os.path.join(DATA_DIR, "election66_candidate.csv"))
    pl_66 = pd.read_csv(os.path.join(DATA_DIR, "election66_partylist.csv"))
    socio = pd.read_csv(os.path.join(SOCIO_DIR, "tambon_socioeconomic_election.csv"))

    # Name fixes for election data
    tambon_rename = {
        'บ้านหวอด': 'บ้านหวด',
        'หลวงเหนือ': 'หลวงใต้',
        'ทุ่งกว้าง': 'ทุ่งกว๋าว',
        'แจ้ห่ม(ในเขต)': 'แจ้ห่ม',
        'แจ้ห่ม(นอกเขต)': 'แจ้ห่ม',
    }
    results['sub-district'] = results['sub-district'].replace(tambon_rename)
    summary['sub-district'] = summary['sub-district'].replace(tambon_rename)

    return results, summary, coords, pop_age, cand_66, pl_66, socio

results, summary, coords, pop_age, cand_66, pl_66, socio = load_data()

PARTY_COLORS = {
    'ประชาชน': '#F4652A', 'เพื่อไทย': '#E0242B', 'กล้าธรรม': '#1651B5',
    'ภูมิใจไทย': '#003399', 'ประชาธิปัตย์': '#0055AA', 'รวมไทยสร้างชาติ': '#1E3A5F',
    'ก้าวไกล': '#F4652A', 'พลังประชารัฐ': '#1651B5', 'ไทยสร้างไทย': '#FF6B00',
    'เพื่อชาติไทย': '#994400',
}

# --- Sidebar ---
st.sidebar.title("Lampang Area 2")
st.sidebar.markdown("**เขตเลือกตั้งที่ 2 จ.ลำปาง**")

page = st.sidebar.radio("เลือกหน้า", [
    "1. Swing Unit Map",
    "2. Turnout Heatmap",
    "3. Invalid Ballot Map",
    "4. Clustering (KMeans)",
    "5. Party Share by District",
    "6. Candidate vs Party",
    "7. Election 66 vs 69",
    "8. Aging Society vs Voting",
    "9. DBSCAN Clustering",
])

# =============================================================================
# PAGE 1: Swing Unit Map
# =============================================================================
if page == "1. Swing Unit Map":
    st.title("Swing Unit Map")
    st.markdown("แผนที่หน่วยเลือกตั้ง จัดสีตามส่วนต่างคะแนนอันดับ 1 vs 2 (Battleground Analysis)")

    # Compute margin per unit
    cand = results[results['type'] == 'เขต'].copy()
    unit_scores = cand.groupby(['district', 'sub-district', 'unit_number', 'name'])['score'].sum().reset_index()
    unit_total = unit_scores.groupby(['district', 'sub-district', 'unit_number'])['score'].sum().reset_index()
    unit_total.columns = ['district', 'sub-district', 'unit_number', 'total_score']

    # Top 2 per unit
    top2 = unit_scores.sort_values('score', ascending=False).groupby(
        ['district', 'sub-district', 'unit_number']).head(2)
    top2['rank'] = top2.groupby(['district', 'sub-district', 'unit_number']).cumcount() + 1

    top1 = top2[top2['rank'] == 1][['district', 'sub-district', 'unit_number', 'name', 'score']].copy()
    top1.columns = ['district', 'sub-district', 'unit_number', 'winner', 'score1']
    top2_only = top2[top2['rank'] == 2][['district', 'sub-district', 'unit_number', 'score']].copy()
    top2_only.columns = ['district', 'sub-district', 'unit_number', 'score2']

    margin_df = top1.merge(top2_only, on=['district', 'sub-district', 'unit_number'], how='left')
    margin_df = margin_df.merge(unit_total, on=['district', 'sub-district', 'unit_number'])
    margin_df['score2'] = margin_df['score2'].fillna(0)
    margin_df['margin_pct'] = (margin_df['score1'] - margin_df['score2']) / margin_df['total_score'] * 100

    # Merge with coords
    margin_map = margin_df.merge(coords, on=['district', 'sub-district', 'unit_number'], how='inner')

    def get_color(margin):
        if margin < 10:
            return '#e74c3c'
        elif margin < 25:
            return '#f39c12'
        elif margin < 50:
            return '#3498db'
        else:
            return '#27ae60'

    threshold = st.slider("Battleground threshold (%)", 5, 30, 10)

    m = folium.Map(location=[18.8, 99.9], zoom_start=10, tiles='CartoDB positron')
    battleground_count = 0
    for _, r in margin_map.iterrows():
        color = get_color(r['margin_pct'])
        if r['margin_pct'] < threshold:
            battleground_count += 1
        folium.CircleMarker(
            location=[r['latitude'], r['longitude']],
            radius=5,
            color=color, fill=True, fill_opacity=0.7,
            popup=f"{r['district']} {r['sub-district']} หน่วย {r['unit_number']}<br>"
                  f"ชนะ: {r['winner']}<br>Margin: {r['margin_pct']:.1f}%",
        ).add_to(m)

    col1, col2, col3 = st.columns(3)
    col1.metric("หน่วยทั้งหมด", len(margin_map))
    col2.metric(f"Battleground (<{threshold}%)", battleground_count)
    col3.metric("Margin เฉลี่ย", f"{margin_map['margin_pct'].mean():.1f}%")
    st_folium(m, width=900, height=600)

    st.markdown("""
    **สี:** 🔴 Battleground (<10%) | 🟠 Contested (10-25%) | 🔵 Leaning (25-50%) | 🟢 Safe (>50%)
    """)

# =============================================================================
# PAGE 2: Turnout Heatmap
# =============================================================================
elif page == "2. Turnout Heatmap":
    st.title("Turnout Heatmap")
    st.markdown("แผนที่อัตราการมาใช้สิทธิ์รายหน่วยเลือกตั้ง")

    sum_khet = summary[summary['type'] == 'เขต'].copy()
    sum_khet['turnout'] = sum_khet['valid_ballots'] / sum_khet['total_ballots'] * 100
    turnout_map = sum_khet.merge(coords, on=['district', 'sub-district', 'unit_number'], how='inner')

    avg_turnout = turnout_map['turnout'].mean()
    col1, col2, col3 = st.columns(3)
    col1.metric("Turnout เฉลี่ย", f"{avg_turnout:.1f}%")
    col2.metric("ต่ำสุด", f"{turnout_map['turnout'].min():.1f}%")
    col3.metric("สูงสุด", f"{turnout_map['turnout'].max():.1f}%")

    m = folium.Map(location=[18.8, 99.9], zoom_start=10, tiles='CartoDB positron')
    for _, r in turnout_map.iterrows():
        t = r['turnout']
        if t >= 70:
            color = '#27ae60'
        elif t >= 60:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        folium.CircleMarker(
            location=[r['latitude'], r['longitude']],
            radius=5, color=color, fill=True, fill_opacity=0.7,
            popup=f"{r['district']} {r['sub-district']} หน่วย {r['unit_number']}<br>Turnout: {t:.1f}%",
        ).add_to(m)
    st_folium(m, width=900, height=600)
    st.markdown("**สี:** 🟢 สูง (>=70%) | 🟠 กลาง (60-70%) | 🔴 ต่ำ (<60%)")

# =============================================================================
# PAGE 3: Invalid Ballot Map
# =============================================================================
elif page == "3. Invalid Ballot Map":
    st.title("Invalid Ballot Map")
    st.markdown("แผนที่อัตราบัตรเสีย + งดออกเสียง รายหน่วยเลือกตั้ง")

    sum_khet = summary[summary['type'] == 'เขต'].copy()
    sum_khet['invalid_rate'] = (sum_khet['invalid_ballots'] + sum_khet['no_vote_ballots']) / sum_khet['total_ballots'] * 100
    inv_map = sum_khet.merge(coords, on=['district', 'sub-district', 'unit_number'], how='inner')

    col1, col2, col3 = st.columns(3)
    col1.metric("อัตราเฉลี่ย", f"{inv_map['invalid_rate'].mean():.1f}%")
    col2.metric("ต่ำสุด", f"{inv_map['invalid_rate'].min():.1f}%")
    col3.metric("สูงสุด", f"{inv_map['invalid_rate'].max():.1f}%")

    m = folium.Map(location=[18.8, 99.9], zoom_start=10, tiles='CartoDB positron')
    for _, r in inv_map.iterrows():
        rate = r['invalid_rate']
        if rate >= 15:
            color = '#8b0000'
        elif rate >= 10:
            color = '#e74c3c'
        elif rate >= 7:
            color = '#f39c12'
        else:
            color = '#27ae60'
        folium.CircleMarker(
            location=[r['latitude'], r['longitude']],
            radius=5, color=color, fill=True, fill_opacity=0.7,
            popup=f"{r['district']} {r['sub-district']} หน่วย {r['unit_number']}<br>บัตรเสีย+งดออกเสียง: {rate:.1f}%",
        ).add_to(m)
    st_folium(m, width=900, height=600)

    # By district
    st.subheader("อัตราบัตรเสียรายอำเภอ")
    by_dist = inv_map.groupby('district')['invalid_rate'].mean().sort_values(ascending=False)
    fig = px.bar(x=by_dist.index, y=by_dist.values, labels={'x': 'อำเภอ', 'y': 'อัตราบัตรเสีย+งดออกเสียง (%)'},
                 color=by_dist.values, color_continuous_scale='Reds')
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# PAGE 4: KMeans Clustering
# =============================================================================
elif page == "4. Clustering (KMeans)":
    st.title("KMeans Clustering")
    st.markdown("แบ่งหน่วยเลือกตั้งเป็นกลุ่มตามพฤติกรรมการลงคะแนน")

    n_clusters = st.sidebar.slider("จำนวน Clusters", 2, 6, 4)

    pl = results[results['type'] == 'บช'].copy()
    top_parties = pl.groupby('name')['score'].sum().nlargest(5).index.tolist()
    pivot = pl[pl['name'].isin(top_parties)].pivot_table(
        index=['district', 'sub-district', 'unit_number'], columns='name', values='score', aggfunc='sum', fill_value=0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # Add turnout
    sum_bch = summary[summary['type'] == 'บช'].groupby(['district', 'sub-district', 'unit_number']).agg(
        valid_ballots=('valid_ballots', 'sum'), total_ballots=('total_ballots', 'sum'),
        invalid_ballots=('invalid_ballots', 'sum'))
    pivot_pct['turnout'] = sum_bch['valid_ballots'] / sum_bch['total_ballots'] * 100
    pivot_pct['invalid_rate'] = sum_bch['invalid_ballots'] / sum_bch['total_ballots'] * 100
    pivot_pct = pivot_pct.dropna()

    scaler = StandardScaler()
    X = scaler.fit_transform(pivot_pct)
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    pivot_pct['cluster'] = km.fit_predict(X)

    # Auto-name clusters based on profile
    def name_cluster(cluster_data, all_data, party_cols):
        means = cluster_data[party_cols].mean()
        top_party = means.idxmax()
        top_pct = means.max()
        second_pct = means.nlargest(2).iloc[1]
        turnout_mean = cluster_data['turnout'].mean()
        n = len(cluster_data)

        if top_pct >= 65 and turnout_mean >= 80:
            return f"ป้อม{top_party} (turnout สูง)"
        elif top_pct >= 65:
            return f"ฐานแน่น {top_party}"
        elif top_pct - second_pct < 5:
            second_party = means.nlargest(2).index[1]
            return f"สมรภูมิ {top_party}-{second_party}"
        elif top_pct >= 40:
            return f"ทั่วไป ({top_party} นำ)"
        else:
            return f"แข่งขันสูง ({top_party} นำเล็กน้อย)"

    party_cols_for_name = [c for c in top_parties if c in pivot_pct.columns]
    cluster_names = {}
    for c in sorted(pivot_pct['cluster'].unique()):
        cdata = pivot_pct[pivot_pct['cluster'] == c]
        cluster_names[c] = name_cluster(cdata, pivot_pct, party_cols_for_name)

    pivot_pct['cluster_name'] = pivot_pct['cluster'].map(cluster_names)

    # Merge coords
    cluster_map = pivot_pct.reset_index().merge(coords, on=['district', 'sub-district', 'unit_number'], how='inner')

    cluster_colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c']

    m = folium.Map(location=[18.8, 99.9], zoom_start=10, tiles='CartoDB positron')
    for _, r in cluster_map.iterrows():
        c = int(r['cluster'])
        folium.CircleMarker(
            location=[r['latitude'], r['longitude']],
            radius=5, color=cluster_colors[c], fill=True, fill_opacity=0.7,
            popup=f"{cluster_names[c]}<br>{r['district']} {r['sub-district']} หน่วย {r['unit_number']}",
        ).add_to(m)
    st_folium(m, width=900, height=600)

    # Legend
    st.markdown("**กลุ่ม:**")
    for c in sorted(cluster_names.keys()):
        n = len(pivot_pct[pivot_pct['cluster'] == c])
        color = cluster_colors[c]
        st.markdown(f'<span style="color:{color}; font-size:20px;">&#9679;</span> **{cluster_names[c]}** ({n} หน่วย)', unsafe_allow_html=True)

    # Cluster summary
    st.subheader("สรุป Cluster")
    cluster_summary = pivot_pct.groupby('cluster')[party_cols_for_name + ['turnout', 'invalid_rate']].mean().round(1)
    cluster_summary.index = [f"{cluster_names[i]}" for i in cluster_summary.index]
    st.dataframe(cluster_summary, use_container_width=True)

# =============================================================================
# PAGE 5: Party Share by District
# =============================================================================
elif page == "5. Party Share by District":
    st.title("Party Share by District")
    st.markdown("สัดส่วนคะแนนบัญชีรายชื่อแต่ละพรรค รายอำเภอ")

    pl = results[(results['type'] == 'บช') & (results['district'] != 'นอกเขต')].copy()
    top_parties = pl.groupby('name')['score'].sum().nlargest(8).index.tolist()
    pl_top = pl[pl['name'].isin(top_parties)]
    district_party = pl_top.groupby(['district', 'name'])['score'].sum().reset_index()
    district_total = district_party.groupby('district')['score'].sum().reset_index()
    district_total.columns = ['district', 'total']
    district_party = district_party.merge(district_total, on='district')
    district_party['pct'] = district_party['score'] / district_party['total'] * 100

    colors = [PARTY_COLORS.get(p, '#999999') for p in top_parties]
    fig = px.bar(district_party, x='pct', y='district', color='name', orientation='h',
                 color_discrete_map=PARTY_COLORS,
                 labels={'pct': 'สัดส่วน (%)', 'district': 'อำเภอ', 'name': 'พรรค'},
                 title='สัดส่วนคะแนนบัญชีรายชื่อรายอำเภอ')
    fig.update_layout(barmode='stack', height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.subheader("ตารางคะแนนดิบ")
    pivot_table = district_party.pivot_table(index='district', columns='name', values='score', fill_value=0)
    st.dataframe(pivot_table.style.format("{:,.0f}"), use_container_width=True)

# =============================================================================
# PAGE 6: Candidate vs Party
# =============================================================================
elif page == "6. Candidate vs Party":
    st.title("Candidate vs Party Performance")
    st.markdown("เปรียบเทียบคะแนนผู้สมัครเขต vs คะแนนพรรคบัญชีรายชื่อ รายหน่วย")

    cand = results[results['type'] == 'เขต'].copy()
    top3_cand = cand.groupby('name')['score'].sum().nlargest(3).index.tolist()

    party_map = {}
    bch = results[results['type'] == 'บช'].copy()
    for c_name in top3_cand:
        # Find matching party by selecting candidate
        st.write(f"**{c_name}**")

    # Build scatter data
    for cand_name in top3_cand:
        cand_scores = cand[cand['name'] == cand_name].groupby(
            ['district', 'sub-district', 'unit_number'])['score'].sum().reset_index()
        cand_scores.columns = ['district', 'sub-district', 'unit_number', 'cand_score']

        # Get party list total per unit
        bch_total = bch.groupby(['district', 'sub-district', 'unit_number'])['score'].sum().reset_index()
        bch_total.columns = ['district', 'sub-district', 'unit_number', 'party_total']

        merged = cand_scores.merge(bch_total, on=['district', 'sub-district', 'unit_number'])
        fig = px.scatter(merged, x='party_total', y='cand_score', color='district',
                        trendline='ols',
                        labels={'party_total': 'คะแนนรวมบัญชีรายชื่อ (หน่วย)', 'cand_score': f'คะแนน {cand_name}'},
                        title=f'{cand_name}')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# PAGE 7: Election 66 vs 69
# =============================================================================
elif page == "7. Election 66 vs 69":
    st.title("เปรียบเทียบผลเลือกตั้ง ปี 66 vs 69")

    tab1, tab2, tab3 = st.tabs(["บัญชีรายชื่อ", "ส.ส.เขต", "สถิติบัตร"])

    # Aggregate 69 data
    pl_69 = results[results['type'] == 'บช'].groupby('name')['score'].sum().reset_index()
    pl_69.columns = ['party', 'score']
    pl_69 = pl_69.sort_values('score', ascending=False)
    pl_69['score_pct'] = pl_69['score'] / pl_69['score'].sum() * 100

    cand_69 = results[results['type'] == 'เขต'].groupby('name')['score'].sum().reset_index()
    cand_69.columns = ['candidate_name', 'score']
    cand_69 = cand_69.sort_values('score', ascending=False)
    cand_69['score_pct'] = cand_69['score'] / cand_69['score'].sum() * 100

    with tab1:
        st.subheader("Swing Analysis บัญชีรายชื่อ")
        party_mapping = {
            'เพื่อไทย': 'เพื่อไทย', 'ก้าวไกล': 'ประชาชน',
            'รวมไทยสร้างชาติ': 'รวมไทยสร้างชาติ', 'ภูมิใจไทย': 'ภูมิใจไทย',
            'ประชาธิปัตย์': 'ประชาธิปัตย์',
        }
        comp = []
        for p66, p69 in party_mapping.items():
            s66 = pl_66[pl_66['party'] == p66]
            s69 = pl_69[pl_69['party'] == p69]
            if len(s66) > 0 and len(s69) > 0:
                comp.append({
                    'พรรค 66': p66, 'พรรค 69': p69,
                    '% ปี 66': round(s66.iloc[0]['score_pct'], 1),
                    '% ปี 69': round(s69.iloc[0]['score_pct'], 1),
                    'เปลี่ยนแปลง': round(s69.iloc[0]['score_pct'] - s66.iloc[0]['score_pct'], 1),
                })
        comp_df = pd.DataFrame(comp)

        # Swing chart
        fig = go.Figure()
        colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in comp_df['เปลี่ยนแปลง']]
        labels = [f"{r['พรรค 66']} → {r['พรรค 69']}" if r['พรรค 66'] != r['พรรค 69'] else r['พรรค 66']
                  for _, r in comp_df.iterrows()]
        fig.add_trace(go.Bar(x=comp_df['เปลี่ยนแปลง'], y=labels, orientation='h',
                             marker_color=colors, text=[f"{v:+.1f}" for v in comp_df['เปลี่ยนแปลง']],
                             textposition='outside'))
        fig.update_layout(title='Swing: สัดส่วนคะแนนบัญชีรายชื่อ ปี 66 → 69', xaxis_title='เปลี่ยนแปลง (% จุด)',
                         height=400)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(comp_df, use_container_width=True)

        # Side by side pie
        col1, col2 = st.columns(2)
        with col1:
            top5_66 = pl_66.head(5)
            fig66 = px.pie(top5_66, values='score', names='party', title='บัญชีรายชื่อ ปี 66 (Top 5)',
                          color='party', color_discrete_map=PARTY_COLORS)
            st.plotly_chart(fig66, use_container_width=True)
        with col2:
            top5_69 = pl_69.head(5)
            fig69 = px.pie(top5_69, values='score', names='party', title='บัญชีรายชื่อ ปี 69 (Top 5)',
                          color='party', color_discrete_map=PARTY_COLORS)
            st.plotly_chart(fig69, use_container_width=True)

    with tab2:
        st.subheader("ส.ส.เขต Top 5")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**ปี 66**")
            st.dataframe(cand_66[['candidate_name', 'party', 'score', 'score_pct']].head(5).style.format(
                {'score': '{:,.0f}', 'score_pct': '{:.1f}%'}), use_container_width=True)
        with col2:
            st.markdown("**ปี 69**")
            st.dataframe(cand_69[['candidate_name', 'score', 'score_pct']].head(5).style.format(
                {'score': '{:,.0f}', 'score_pct': '{:.1f}%'}), use_container_width=True)

    with tab3:
        st.subheader("สถิติบัตร")
        sum_69 = summary[summary['type'] == 'เขต']
        ballot_data = {
            'รายการ': ['ผู้มาใช้สิทธิ์', 'บัตรเสีย', 'งดออกเสียง'],
            'ปี 66': ['119,599 (77.8%)', '7,339 (6.1%)', '2,638 (2.2%)'],
            'ปี 69': [
                f"{sum_69['total_ballots'].sum():,.0f}",
                f"{sum_69['invalid_ballots'].sum():,.0f} ({sum_69['invalid_ballots'].sum()/sum_69['total_ballots'].sum()*100:.1f}%)",
                f"{sum_69['no_vote_ballots'].sum():,.0f} ({sum_69['no_vote_ballots'].sum()/sum_69['total_ballots'].sum()*100:.1f}%)",
            ]
        }
        st.table(pd.DataFrame(ballot_data))

# =============================================================================
# PAGE 8: Aging Society vs Voting
# =============================================================================
elif page == "8. Aging Society vs Voting":
    st.title("สังคมสูงวัย vs พฤติกรรมการเลือกตั้ง")

    # Prep pop data
    pop_age['age_group'] = pd.cut(pop_age['age'], bins=[-1, 14, 24, 59, 200],
                                   labels=['0-14', '15-24', '25-59', '60+'])
    pop_tambon = pop_age.groupby(['district', 'sub_district', 'age_group'], observed=True)['total'].sum().unstack(fill_value=0)
    pop_tambon['pop_total'] = pop_tambon.sum(axis=1)
    pop_tambon['pct_elderly'] = pop_tambon['60+'] / pop_tambon['pop_total'] * 100
    pop_tambon = pop_tambon.reset_index()

    # Prep election data
    pl = results[(results['type'] == 'บช') & (results['district'] != 'นอกเขต')].copy()
    pl_tambon = pl.groupby(['district', 'sub-district', 'name'])['score'].sum().reset_index()
    idx = pl_tambon.groupby(['district', 'sub-district'])['score'].idxmax()
    winner = pl_tambon.loc[idx].copy()
    winner.columns = ['district', 'sub_district', 'winner_party', 'winner_score']
    total_by = pl_tambon.groupby(['district', 'sub-district'])['score'].sum().reset_index()
    total_by.columns = ['district', 'sub_district', 'total_score']
    winner = winner.merge(total_by, on=['district', 'sub_district'])

    for party in ['ประชาชน', 'เพื่อไทย', 'กล้าธรรม', 'ภูมิใจไทย']:
        ps = pl_tambon[pl_tambon['name'] == party][['district', 'sub-district', 'score']].copy()
        ps.columns = ['district', 'sub_district', f'pct_{party}']
        winner = winner.merge(ps, on=['district', 'sub_district'], how='left')
        winner[f'pct_{party}'] = winner[f'pct_{party}'].fillna(0) / winner['total_score'] * 100

    merged = pop_tambon.merge(winner, on=['district', 'sub_district'], how='inner')

    st.metric("ตำบลที่ match ได้", f"{len(merged)} ตำบล")

    # Scatter plots
    st.subheader("สัดส่วนผู้สูงวัย vs คะแนนพรรค")
    party_to_plot = st.multiselect("เลือกพรรค", ['ประชาชน', 'เพื่อไทย', 'กล้าธรรม', 'ภูมิใจไทย'],
                                    default=['ประชาชน', 'เพื่อไทย', 'ภูมิใจไทย'])

    for party in party_to_plot:
        col_name = f'pct_{party}'
        r_val, p_val = stats.pearsonr(merged['pct_elderly'], merged[col_name])
        fig = px.scatter(merged, x='pct_elderly', y=col_name, color='district',
                        trendline='ols', hover_data=['sub_district'],
                        labels={'pct_elderly': 'สัดส่วนผู้สูงวัย 60+ (%)', col_name: f'{party} (%)'},
                        title=f'{party} (r={r_val:.2f}, p={p_val:.3f})',
                        color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Correlation heatmap
    st.subheader("Correlation Heatmap")
    corr_cols = ['pct_elderly'] + [f'pct_{p}' for p in ['ประชาชน', 'เพื่อไทย', 'กล้าธรรม', 'ภูมิใจไทย']]
    corr = merged[corr_cols].corr()
    fig = px.imshow(corr, text_auto='.2f', color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
                    labels=dict(color="Correlation"),
                    x=['สูงวัย%', 'ประชาชน%', 'เพื่อไทย%', 'กล้าธรรม%', 'ภูมิใจไทย%'],
                    y=['สูงวัย%', 'ประชาชน%', 'เพื่อไทย%', 'กล้าธรรม%', 'ภูมิใจไทย%'])
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# PAGE 9: DBSCAN Clustering
# =============================================================================
elif page == "9. DBSCAN Clustering":
    st.title("DBSCAN Clustering")
    st.markdown("Density-based clustering (จาก phao-analyze)")

    eps = st.sidebar.slider("eps", 0.1, 1.0, 0.3, 0.05)
    min_samples = st.sidebar.slider("min_samples", 3, 20, 10)

    # Prepare data same as phao-analyze
    pl = results[results['type'] == 'บช'].copy()
    cand = results[results['type'] == 'เขต'].copy()

    all_names = results['name'].unique()
    pivot = results.pivot_table(index=['district', 'sub-district', 'unit_number', 'type'],
                                columns='name', values='score', aggfunc='sum', fill_value=0)
    pivot = pivot.groupby(level=['district', 'sub-district', 'unit_number']).sum()

    # Normalize by valid ballots
    sum_unit = summary.groupby(['district', 'sub-district', 'unit_number'])['valid_ballots'].sum()
    for col in pivot.columns:
        pivot[col] = pivot[col] / sum_unit
    pivot = pivot.dropna()
    pivot = pivot[(pivot <= 1.5).all(axis=1)]  # Remove anomalies

    # DBSCAN
    dbs = DBSCAN(eps=eps, min_samples=min_samples)
    pivot['cluster'] = dbs.fit_predict(pivot)

    cluster_counts = pivot['cluster'].value_counts().sort_index()
    cluster_names = {-1: 'มันคือแป้ง (Outlier)', 0: 'ปกติ', 1: 'ประชาชนหวานเจี๊ยบ'}

    st.subheader("จำนวนหน่วยในแต่ละ Cluster")
    for c, count in cluster_counts.items():
        name = cluster_names.get(c, f'Cluster {c}')
        st.write(f"**{name}**: {count} หน่วย")

    # t-SNE visualization
    if len(pivot) > 10:
        with st.spinner("กำลังคำนวณ t-SNE..."):
            feature_cols = [c for c in pivot.columns if c != 'cluster']
            tsne = TSNE(n_components=2, perplexity=min(30, len(pivot)-1), random_state=42)
            tsne_result = tsne.fit_transform(pivot[feature_cols])

            tsne_df = pd.DataFrame(tsne_result, columns=['x', 'y'])
            tsne_df['cluster'] = pivot['cluster'].values
            tsne_df['cluster_name'] = tsne_df['cluster'].map(
                lambda c: cluster_names.get(c, f'Cluster {c}'))

            fig = px.scatter(tsne_df, x='x', y='y', color='cluster_name',
                            title='t-SNE Visualization', opacity=0.7,
                            color_discrete_sequence=px.colors.qualitative.Set1)
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

    # Top parties per cluster
    st.subheader("Top 5 พรรคในแต่ละ Cluster")
    party_cols_bch = [n for n in pl['name'].unique() if n in pivot.columns]
    for c in sorted(pivot['cluster'].unique()):
        name = cluster_names.get(c, f'Cluster {c}')
        cluster_data = pivot[pivot['cluster'] == c]
        top5 = cluster_data[party_cols_bch].mean().nlargest(5)
        st.write(f"**{name}** ({len(cluster_data)} หน่วย)")
        st.dataframe(pd.DataFrame({'พรรค': top5.index, 'สัดส่วนเฉลี่ย': (top5.values * 100).round(1)}).reset_index(drop=True),
                    use_container_width=True)

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.markdown("Lampang Area 2 Election Analysis")
