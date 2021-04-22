from flask import Flask,render_template, request, jsonify
import pandas as pd
import app_content.implementation as imp

#Flaskオブジェクトの生成
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 日本語が文字化けして表示するのを防ぐ


#「/」へアクセスがあった場合
@app.route("/")
def hello():
	return render_template("home.html")


#「/answer」へアクセスがあった場合
@app.route("/answer", methods=["GET", "POST"])
def answer():
	if request.method == "POST" and "csv_file" in request.files:
		file = request.files['csv_file']
		
		if "csv" not in file.filename:
			return ("csvファイルの入力をお願いします")
		
		else:
			df = pd.read_csv(file)
			answer = imp.prediction(df)
			answer.to_csv("my_answer.csv", index=False)
			return render_template("answer.html")


#ソースが直接実行されたら中身を実行
if __name__ == "__main__":
    app.run(debug=True)
