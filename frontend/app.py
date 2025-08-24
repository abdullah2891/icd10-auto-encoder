# frontend/app.py
import requests, streamlit as st

st.title("ICD-10 Auto-Coder (Demo)")
note = st.text_area("Clinical note / chief complaint", height=160, placeholder="e.g., 28F with dysuria, frequency, suprapubic pain, afebrile.")
top_k = st.slider("Top-K", 1, 10, 5)

if st.button("Suggest Codes"):
    with st.spinner("Analyzing..."):
        r = requests.post("http://backend:8000/suggest", json={"note": note, "top_k": top_k}).json()
        print("results:", r)

        for item in r["results"]:
            st.write(f"**{item['code']} — {item['title']}**  \nConfidence: {item['confidence']}")
            st.caption(item["rationale"])

