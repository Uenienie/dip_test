#Flaskとrender_template（HTMLを表示させるための関数）をインポート
from flask import Flask,render_template, request, jsonify
import pandas as pd
import implementation as imp

#Flaskオブジェクトの生成
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 日本語が文字化けして表示する のを防ぐ


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
			return render_template("app_content/templates/answer.html")


#ソースが直接実行されたら中身を実行
if __name__ == "__main__":
    app.run(debug=False)
    
# https://qiita.com/kiyokiyo_kzsby/items/0184973e9de0ea9011ed
# https://gametech.vatchlog.com/2019/12/17/flask-pokedex/
# https://panda-clip.com/flask-uploads/

# タグ https://html-coding.co.jp/annex/dictionary/html/input/