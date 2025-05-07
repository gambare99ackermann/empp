from flask import Flask, request, jsonify, send_file
import pandas as pd
import requests
import os
from io import BytesIO

app = Flask(__name__)

PDL_API_KEY = os.environ.get("PDL_API_KEY")
PDL_ENDPOINT = "https://api.peopledatalabs.com/v5/person/enrich"


def enrich_employee(name, company):
    first_name, last_name = name.split(" ", 1)
    params = {
        "api_key": PDL_API_KEY,
        "first_name": first_name,
        "last_name": last_name,
        "company": company
    }
    response = requests.get(PDL_ENDPOINT, params=params)
    if response.status_code == 200:
        data = response.json()
        return {
            "email": data.get("email", "N/A"),
            "title": data.get("job_title", "N/A")
        }
    else:
        return {"email": "N/A", "title": "N/A"}


@app.route("/enrich", methods=["POST"])
def enrich_employee_profiles():
    try:
        file = request.files['file']
        df = pd.read_excel(file)

        # Check required columns
        if not {'Name', 'Company'}.issubset(df.columns):
            return jsonify({"error": "Missing required columns: Name, Company"}), 400

        emails, titles = [], []
        for _, row in df.iterrows():
            enriched = enrich_employee(row['Name'], row['Company'])
            emails.append(enriched['email'])
            titles.append(enriched['title'])

        df['Email'] = emails
        df['Title'] = titles

        # Write to output Excel in memory
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="enriched_profiles.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
