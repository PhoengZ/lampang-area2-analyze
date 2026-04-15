import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

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
            fig, axs = plt.subplots(2, 1, figsize=(15, 20))
            sns.heatmap(df_final[choosing + ["อสม_normalize"]].corr(), cmap='coolwarm', annot=True, ax=axs[0])
            axs[0].set_title(f"Heatmap ความสัมพันธ์: พรรคการเมือง vs จำนวน อสม.")

            for party in choosing:
                sns.regplot(
                    data=results_groupby, 
                    x='อสม_normalize', 
                    y=party,
                    label=party,
                    scatter_kws={'s': 40, 'alpha': 0.4},
                    line_kws={'linewidth': 2},
                    ax=axs[1] 
                )
            
            axs[1].set_title("แนวโน้มคะแนนเลือกตั้งพรรคเทียบกับจำนวน อสม. (แบ่งตามตำบล)")
            axs[1].set_xlabel("จำนวน อสม. ต่อประชากร 1000 คน")
            axs[1].set_ylabel("สัดส่วนคะแนนที่ได้รับ")
            axs[1].legend(loc='upper right')
            
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.write("กรุณาเลือกพรรคการเมืองอย่างน้อย 1 พรรค")
    with tab2:
        choosing = st.multiselect("เลือกผู้สมัครคนใด (เลือกได้หลายคน)", people_names)
        if choosing:
            fig, axs = plt.subplots(2, 1, figsize=(15, 20))
            sns.heatmap(df_final[choosing + ["อสม_normalize"]].corr(), cmap='coolwarm', annot=True, ax=axs[0])
            axs[0].set_title(f"Heatmap ความสัมพันธ์:ผู้สมัคร สส. vs จำนวน อสม.")

            for people in choosing:
                sns.regplot(
                    data=results_groupby, 
                    x='อสม_normalize', 
                    y=people,
                    label=people,
                    scatter_kws={'s': 40, 'alpha': 0.4},
                    line_kws={'linewidth': 2},
                    ax=axs[1] 
                )
            
            axs[1].set_title("แนวโน้มคะแนนเลือกตั้งสส.เขต เทียบกับจำนวน อสม. (แบ่งตามตำบล)")
            axs[1].set_xlabel("จำนวน อสม. ต่อประชากร 1000 คน")
            axs[1].set_ylabel("สัดส่วนคะแนนที่ได้รับ")
            axs[1].legend(loc='upper right')
            
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.write("กรุณาเลือกผู้สมัครอย่างน้อย 1 คน")
