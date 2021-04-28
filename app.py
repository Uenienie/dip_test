from flask import Flask,render_template, request, jsonify
import os
import pandas as pd
import implementation.implementation as imp

#Flaskオブジェクトの生成
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 日本語が文字化けして表示するのを防ぐ


#「/」へアクセスがあった場合
@app.route("/")
def top():
	return render_template("top.html")


#「/home」へアクセスがあった場合
@app.route("/")
def home():
	return render_template("home.html")


#「/answer」へアクセスがあった場合
@app.route("/answer", methods=["GET", "POST"])
def answer():
	if request.method == "POST" and "csv_file" in request.files:
		file = request.files['csv_file']
		
		if "csv" not in file.filename:
			return render_template("request_csv.html")
		
		else:
			df = pd.read_csv(file)
			if df.shape == (len(df), 212):
				answer = imp.prediction(df)
				answer.to_csv("answer.csv", index=False)
				return render_template("answer.html")
			else:
				return render_template("request_formal.html")


#ソースが直接実行されたら中身を実行
if __name__ == "__main__":
	app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
