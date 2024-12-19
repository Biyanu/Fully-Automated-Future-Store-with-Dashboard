from flask import Flask, jsonify, request
import pandas as pd

app = Flask(__name__)

@app.route("/data", methods=["GET"])
def get_data():
    df = pd.read_csv(r"D:\MSBA\Courses\Fall_2024\BZAN545\Assignments\Group_ASS\final_project\data_sets\feature_store.csv")
    result = df.to_dict(orient="records")
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5000)