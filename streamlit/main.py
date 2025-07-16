from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import pickle
import os, io

from sklearn.base import BaseEstimator, TransformerMixin
from typing import Literal
from function import ModusImputer,ModusTwoGroups
lokasi_file = Path(__file__).resolve()
# print("Lokasi file:", lokasi_file)

lokasi_folder_utama = lokasi_file.parents[1]
# print("Direktori folder utama:", lokasi_folder_utama)

path_model = lokasi_folder_utama / 'model' / 'logreg_for_marketing.sav'
# print("Path lengkap ke model:", path_model)

path_data_clean = lokasi_folder_utama / 'data' / 'bank_marketing_clean.csv'
# print("Path lengkap ke model:", path_data_clean)



st.set_page_config(
    page_title="Bank Marketing Campaign Predict",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈",
)

st.title("Bank Marketing Campaign Customer Predictor")

st.header("Dataset Overview")
st.markdown("""
Dataset [Bank Marketing Campaigns Dataset](https://www.kaggle.com/datasets/volodymyrgavrysh/bank-marketing-campaigns-dataset/data) 
merupakan kumpulan data hasil kampanye telemarketing oleh sebuah bank di Portugal untuk mempromosikan produk deposito berjangka (term deposit) selama 10 bulan. 
Dataset ini merekam berbagai informasi demografis dan finansial nasabah, termasuk data riwayat interaksi selama kampanye pemasaran seperti jumlah kontak, hasil kampanye sebelumnya, 
serta metode dan waktu komunikasi. Selain itu, dataset ini juga mencakup beberapa indikator ekonomi makro seperti indeks harga konsumen, indeks kepercayaan konsumen, dan suku bunga acuan.
""")

st.header("Main Objective")
st.markdown("""
Memprediksi apakah seorang nasabah kemungkinan besar akan menerima atau menolak penawaran sebelum dihubungi secara langsung. Hasil prediksi ini dinyatakan dalam dua kategori, yaitu:

* "yes": nasabah bersedia dan akhirnya membuka deposito berjangka,
* "no": nasabah tidak tertarik atau menolak penawaran yang diberikan.
""")

st.header("Features")

st.subheader("Customer Profile")
st.markdown("""
* **Age (`age`)**: Umur nasabah
* **Job (`job`)**: Jenis pekerjaan nasabah
* **Marital Status (`marital`)**: Status pernikahan nasabah (menikah, single, bercerai)
* **Education (`education`)**: Tingkat pendidikan nasabah
* **Has Housing Loan? (`housing`)**: Apakah nasabah memiliki pinjaman rumah (yes/no)
* **Has Personal Loan? (`loan`)**: Apakah nasabah memiliki pinjaman pribadi (yes/no)
""")

st.subheader("Campaign Information")
st.markdown("""
* **Campaign (Contact Count) (`campaign`)**: Jumlah kontak yang dilakukan selama kampanye ini
* **Previous Contacts (`previous`)**: Jumlah kontak pada kampanye sebelumnya
* **Previously Contacted (`previous_contacted`)**: Apakah nasabah pernah dihubungi sebelumnya (0 = belum, 1 = sudah)
* **Contact Communication Type (`contact`)**: Media kontak terakhir (telepon rumah atau ponsel)
* **Last Contact Month (`month`)**: Bulan saat kontak terakhir dilakukan
* **Day of Week Contacted (`day_of_week`)**: Hari dalam seminggu saat kontak terakhir
* **Previous Campaign Outcome (`poutcome`)**: Hasil kampanye sebelumnya (nonexistent, failure, success)
""")

st.subheader("Additional Information")
st.markdown("""
* **Consumer Price Index (`cons.price.idx`)**: Indeks harga konsumen, indikator inflasi
* **Consumer Confidence Index (`cons.conf.idx`)**: Indeks kepercayaan konsumen terhadap kondisi ekonomi
* **Number of Employed (`nr.employed`)**: Rata-rata jumlah tenaga kerja, indikator kondisi pasar kerja
""")


#__________________________________________________________________ side bar __________________________________

example_csv = """age,campaign,previous,cons.price.idx,cons.conf.idx,nr.employed,previous_contacted,job,marital,education,housing,loan,contact,month,day_of_week,poutcome
68,22,6,92.289,-31.0,5051.1,1,services,single,basic.4y,no,yes,cellular,sep,thu,failure
31,44,1,94.534,-42.3,4980.4,0,entrepreneur,divorced,professional.course,yes,yes,telephone,apr,wed,nonexistent
88,25,3,92.865,-44.1,5045.9,1,self-employed,married,basic.4y,no,no,telephone,aug,mon,success
77,49,0,93.901,-37.8,5049.6,1,technician,single,basic.4y,yes,yes,cellular,may,thu,success
37,27,3,93.001,-47.4,5156.6,1,retired,married,basic.6y,yes,no,cellular,jun,thu,nonexistent
40,50,0,92.643,-40.3,5107.3,1,retired,divorced,basic.9y,yes,no,cellular,may,fri,success
85,7,3,94.697,-38.8,5043.5,1,retired,married,high.school,no,no,cellular,aug,wed,success
18,2,3,94.113,-42.4,5039.2,0,technician,divorced,basic.9y,no,yes,telephone,jul,fri,nonexistent
54,2,1,93.098,-27.4,5086.1,0,retired,single,university.degree,no,no,telephone,oct,wed,success
60,44,5,92.94,-46.0,5109.4,0,management,divorced,professional.course,no,no,telephone,jul,tue,failure
96,39,3,92.777,-27.6,5077.1,0,technician,single,professional.course,yes,yes,cellular,jul,thu,failure
35,33,0,94.582,-27.3,5164.2,1,blue-collar,single,professional.course,no,no,telephone,jul,mon,nonexistent
55,44,1,93.695,-45.7,5171.9,1,retired,single,basic.4y,yes,yes,telephone,jul,thu,failure
73,15,6,93.747,-39.6,5140.3,1,retired,single,basic.9y,yes,no,cellular,mar,mon,success
27,49,5,93.204,-42.4,5201.3,1,entrepreneur,single,university.degree,no,no,cellular,jul,mon,success
32,18,0,93.512,-40.7,5212.6,0,management,married,high.school,yes,no,telephone,jun,tue,failure
97,55,4,92.681,-37.7,4984.4,0,entrepreneur,single,university.degree,yes,no,cellular,jul,tue,failure
77,5,4,93.707,-49.0,5075.2,0,retired,single,basic.4y,no,no,telephone,may,thu,success
26,40,4,93.31,-45.6,4969.5,0,retired,single,high.school,yes,no,cellular,jul,wed,failure
86,54,4,92.756,-48.0,5186.2,1,retired,divorced,professional.course,yes,no,telephone,aug,mon,nonexistent
"""

def input_feature_sidebar():
    age = st.sidebar.slider("Age", 17, 98, 35)
    campaign = st.sidebar.slider("Campaign (Contact Count)", 1, 56, 2)
    previous = st.sidebar.slider("Previous Contacts", 0, 7, 0)
    cons_price_idx = st.sidebar.slider("Consumer Price Index", 92.201, 94.767, 93.5)
    cons_conf_idx = st.sidebar.slider("Consumer Confidence Index", -50.8, -26.9, -40.0)
    nr_employed = st.sidebar.slider("Number of Employed", 4963.6, 5228.1, 5170.0)
    previous_contacted = st.sidebar.selectbox("Previously Contacted?", [0, 1])
    
    job = st.sidebar.selectbox("Job", ['housemaid', 'services', 'admin.', 'blue-collar', 'technician', 
                                        'retired', 'management', 'unemployed', 'self-employed', 
                                        'entrepreneur', 'student'])
    
    marital = st.sidebar.selectbox("Marital Status", ['married', 'single', 'divorced'])
    education = st.sidebar.selectbox("Education", ['basic.4y', 'high.school', 'basic.6y', 
                                                'basic.9y', 'professional.course', 'university.degree'])
    housing = st.sidebar.selectbox("Has Housing Loan?", ['yes', 'no'])
    loan = st.sidebar.selectbox("Has Personal Loan?", ['yes', 'no'])
    contact = st.sidebar.selectbox("Contact Communication Type", ['telephone', 'cellular'])
    month = st.sidebar.selectbox("Last Contact Month", ['may', 'jun', 'jul', 'aug', 'oct', 'nov', 
                                                        'dec', 'mar', 'apr', 'sep'])
    day_of_week = st.sidebar.selectbox("Day of Week Contacted", ['mon', 'tue', 'wed', 'thu', 'fri'])
    poutcome = st.sidebar.selectbox("Previous Campaign Outcome", ['nonexistent', 'failure', 'success'])
    
    # Susun ke dalam dataframe
    data = {
        'age': age,
        'campaign': campaign,
        'previous': previous,
        'cons.price.idx': cons_price_idx,
        'cons.conf.idx': cons_conf_idx,
        'nr.employed': nr_employed,
        'previous_contacted': previous_contacted,
        'job': job,
        'marital': marital,
        'education': education,
        'housing': housing,
        'loan': loan,
        'contact': contact,
        'month': month,
        'day_of_week': day_of_week,
        'poutcome': poutcome
    }

    return pd.DataFrame([data])


st.sidebar.markdown(
    """Made By : <br>
        1. [Muhammad Khisanul Fakhrudin Akbar](https://www.linkedin.com/in/muhammad-khisanul-fakhrudin-akbar/) <br>
        2. [Cindy Handoko Tantowibowo](https://www.linkedin.com/in/cindy-handoko-tantowibowo-55a2751a7/)
    """,unsafe_allow_html=True
)
st.sidebar.header("Batch Input Feature:")
st.sidebar.write("")

csv_bytes = io.BytesIO(example_csv.encode('utf-8'))

st.sidebar.download_button(
    label="Download Example CSV",
    data=csv_bytes,
    file_name="example_data.csv",
    mime="text/csv",
)
upload_csv = st.sidebar.file_uploader("Upload your input CSV file", type=["csv"])
st.sidebar.write("")
if upload_csv is not None:
    input_df = pd.read_csv(upload_csv)

else:
    st.sidebar.header("Input Feature:")
    st.sidebar.write("")
    input_df = input_feature_sidebar()

#__________________________________________________________________ main bar __________________________________


st.subheader("User Input Features: ")
st.dataframe(input_df[:1])


if os.path.exists(path_model):
    model = pickle.load(open(path_model, "rb"))
else:
    st.error(f"Model file not found: {path_model}")

model = pickle.load(open(path_model, "rb"))

target_map =   {0:'Not Subscribed ❌', 
                1:'Subscribed ✅'}

predictions = model.predict(input_df)  # shape: (n_samples,)
probas = model.predict_proba(input_df)  # shape: (n_samples, 2)

# binner ke label
predicted_labels = [target_map[pred] for pred in predictions]

proba_df = pd.DataFrame(probas, columns=["Prediction Probability Not Subscribed", "Prediction Probability Subscribed"])
proba_df["Prediction Result"] = predicted_labels


st.subheader("Prediction Probability & Result :")
st.dataframe(proba_df)


