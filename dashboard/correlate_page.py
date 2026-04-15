import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import plotly.express as px

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "phao-analyze")
mpl.font_manager.fontManager.addfont(os.path.join(DEFAULT_PATH, "thsarabunnew-webfont.ttf"))

mpl.rc('font', family='TH Sarabun New', size=14)


def correlation_volunteer(df_results, df_osm, df_summary, df_names):
    st.title("ความสัมพันธ์ระหว่างจำนวนอาสาสมัครกับผลการเลือกตั้ง")
    tab1, tab2 = st.tabs(["บัญชีรายชื่อ", "ส.ส.เขต"])
    results_groupby = df_results.groupby(['sub-district', 'name'])['score_clean'].sum().unstack("name")
    df_osm = df_osm.rename({"Unnamed: 0": 'ตำบล'}, axis=1)
    df_osm = df_osm.set_index("ตำบล")
    index2have = df_osm.index.tolist()
    results_groupby = results_groupby.rename(index={'แจ้ห่ม(ในเขต)':"แจ้ห่ม"})
    results_groupby = results_groupby[results_groupby.index.isin(index2have)]
    df_1khet = df_summary.loc[df_summary['type'] == 'เขต'].groupby('sub-district')['valid_ballots'].sum()
    df_1party = df_summary.loc[df_summary['type'] == 'บช'].groupby('sub-district')['valid_ballots'].sum()
    df_1khet = df_1khet.rename(index={'แจ้ห่ม(ในเขต)':"แจ้ห่ม"})
    df_1party = df_1party.rename(index={'แจ้ห่ม(ในเขต)':"แจ้ห่ม"})
    results_groupby['valid_ballots_khet'] = df_1khet
    results_groupby['valid_ballots_party'] = df_1party
    results_groupby['อสม'] = df_osm['จำนวนจิตอาสารวม']
    people_names = df_names.loc[57:, 'Name'].tolist()
    party_names = df_names.loc[:56, 'Name'].tolist()
    results_groupby[people_names] = results_groupby[people_names].div(results_groupby['valid_ballots_khet'], axis=0)
    results_groupby[party_names] = results_groupby[party_names].div(results_groupby['valid_ballots_party'], axis=0)
    results_groupby["อสม_normalize"] = results_groupby['อสม']/1000
    df_final = results_groupby[people_names + party_names + ['อสม_normalize']]
    # print(df_final)
    with tab1:
        choosing = st.multiselect("เลือกพรรคการเมือง (เลือกได้หลายพรรค)", party_names)
        if choosing:
            corr_matrix = df_final[choosing + ["อสม_normalize"]].corr()
            fig_heat = px.imshow(
                corr_matrix,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title="Heatmap ความสัมพันธ์: พรรคการเมือง vs จำนวน อสม."
            )
            st.plotly_chart(fig_heat, use_container_width=True)

            df_melted_party = results_groupby.reset_index().melt(
                id_vars=['sub-district', 'อสม_normalize'],
                value_vars=choosing,
                var_name='พรรคการเมือง',
                value_name='สัดส่วนคะแนน'
            )
            fig_scatter = px.scatter(
                df_melted_party,
                x='อสม_normalize',
                y='สัดส่วนคะแนน',
                color='พรรคการเมือง',
                trendline="ols",
                hover_data=['sub-district'],
                title="แนวโน้มคะแนนเลือกตั้งพรรคเทียบกับจำนวน อสม. (แบ่งตามตำบล)",
                labels={'อสม_normalize': 'จำนวน อสม. ต่อประชากร 1000 คน'}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("กรุณาเลือกพรรคการเมืองอย่างน้อย 1 พรรค")
    with tab2:
        choosing = st.multiselect("เลือกผู้สมัครคนใด (เลือกได้หลายคน)", people_names)
        if choosing:
            # 1. Plotly Heatmap
            corr_matrix = df_final[choosing + ["อสม_normalize"]].corr()
            fig_heat = px.imshow(
                corr_matrix,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title="Heatmap ความสัมพันธ์: ผู้สมัคร ส.ส. vs จำนวน อสม."
            )
            st.plotly_chart(fig_heat, use_container_width=True)

            # 2. Plotly Scatter & Regression
            df_melted_people = results_groupby.reset_index().melt(
                id_vars=['sub-district', 'อสม_normalize'],
                value_vars=choosing,
                var_name='ผู้สมัคร',
                value_name='สัดส่วนคะแนน'
            )

            fig_scatter = px.scatter(
                df_melted_people,
                x='อสม_normalize',
                y='สัดส่วนคะแนน',
                color='ผู้สมัคร',
                trendline="ols",
                hover_data=['sub-district'],
                title="แนวโน้มคะแนนเลือกตั้ง ส.ส.เขต เทียบกับจำนวน อสม. (แบ่งตามตำบล)",
                labels={'อสม_normalize': 'จำนวน อสม. ต่อประชากร 1000 คน'}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("กรุณาเลือกผู้สมัครอย่างน้อย 1 คน")
    
    st.write(f"**ไม่มีตำบล บ้านใหม่ เนื่องจากไม่พบข้อมูลจำนวน อสม ของตำบลบ้านใหม่**")