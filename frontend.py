import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="AI Data Explorer", layout="wide")
st.title("🧠 AI-Powered Data Explorer")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
question = st.text_input("Ask a question about your data")

if uploaded_file:
    with st.spinner("Uploading CSV..."):
        response = requests.post("http://localhost:8000/upload", files={"file": uploaded_file})
        if response.ok:
            st.success("CSV uploaded!")
            insights = response.json().get("insights", {})

            st.subheader("📊 Basic Insights")
            st.write(f"**Shape:** {insights.get('shape')}")
            st.write("**Column Types:**")
            st.json(insights.get("column_types", {}))
            st.write("**Missing Values:**")
            st.json(insights.get("missing_values", {}))
            st.write("**Summary Statistics:**")
            st.json(insights.get("summary_stats", {}))

            # Load the head of the dataframe for charting
            preview_data = pd.DataFrame(insights.get("head", []))
            if not preview_data.empty:
                st.write("**🔎 Sample Data:**")
                st.dataframe(preview_data)

                numeric_cols = preview_data.select_dtypes(include='number').columns
                if len(numeric_cols) >= 1:
                    st.write("📈 Charts of numeric columns:")
                    for col in numeric_cols:
                        st.markdown(f"**📊 Distribution of {col}**")
                        st.bar_chart(preview_data[col], use_container_width=True)

        else:
            st.error("Upload failed.")
            st.text(response.text)

if st.button("Ask") and question:
    with st.spinner("Thinking..."):
        res = requests.post("http://localhost:8000/ask", json={"question": question})
        try:
            result = res.json()
            if res.ok:
                st.subheader("🔍 Generated SQL")
                st.code(result['sql'], language="sql")

                df = pd.DataFrame(result['data'])
                if not df.empty:
                    st.dataframe(df)
                    st.bar_chart(df)  # auto try chart if numeric
            else:
                st.error(f"Error: {result.get('error')}")
                st.code(result.get("sql", ""))
        except Exception:
            st.error("Failed to parse response from server.")
            st.text(res.text)