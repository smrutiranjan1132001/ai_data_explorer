from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
import pandasql as psql

load_dotenv()
app = Flask(__name__)
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store uploaded CSV in memory
df = pd.DataFrame()

@app.route("/upload", methods=["POST"])
def upload():
    global df
    try:
        file = request.files['file']
        df = pd.read_csv(file)

        # Compute basic insights
        insights = {
            "shape": df.shape,
            "columns": list(df.columns),
            "column_types": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "summary_stats": df.describe(include='all').fillna("").to_dict()
        }

        # Add preview data to insights
        insights["head"] = df.head().to_dict(orient="records")

        return jsonify({
            "message": "CSV uploaded successfully",
            "insights": insights
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/ask", methods=["POST"])
def ask():
    global df
    question = request.json.get("question")
    prompt = f"""
    You are a data analyst. Given this pandas DataFrame called 'df':
    {str(df.head(3))}
    Write a SQL query to answer the following question:
    '{question}'
    Only return the SQL query. Use 'df' as the table name.
    """

    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        sql = completion.choices[0].message.content.strip()
        result = psql.sqldf(sql, {"df": df}).to_dict(orient="records")
        return jsonify({"sql": sql, "data": result})
    except Exception as e:
        return jsonify({"error": str(e), "sql": sql}), 400

if __name__ == "__main__":
    app.run(debug=True, port=8000)