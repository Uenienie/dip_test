#Flaskとrender_template（HTMLを表示させるための関数）をインポート
from flask import Flask,render_template, request, jsonify
import pandas as pd
import implementation.implementation as imp

#Flaskオブジェクトの生成
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 日本語が文字化けして表示するのを防ぐ


#「/」へアクセスがあった場合
@app.route("/")
def hello():
	return render_template("home.html")


#「/index」へアクセスがあった場合
@app.route("/index", methods=["GET", "POST"])
def index():
	if request.method == "POST":
		result=request.form.get("Name")
		return render_template("index.html", user_name=result)


@app.route("/index2")
def index2():
	result=request.form.get("Name")
	return render_template("index2.html", user_name=result)


@app.route("/index3", methods=["GET", "POST"])
def index3():
	if request.method == "POST" and "csv_file" in request.files:
		file = request.files['csv_file']
		
		if "csv" not in file.filename:
			return ("csvファイル以外だめでよ～")
		else:
			df = pd.read_csv(file)
			# return df.to_html(justify="match-parent",header="true", table_id="table")  # csvファイル読込み
			imp.head(df).to_csv("abc.csv", index=False)
			return imp.head(df).to_html(justify="match-parent",header="true", table_id="table")  # .pyに従って表示

#ソースが直接実行されたら中身を実行
if __name__ == "__main__":
    app.run(debug=True)
    
# https://qiita.com/kiyokiyo_kzsby/items/0184973e9de0ea9011ed
# https://gametech.vatchlog.com/2019/12/17/flask-pokedex/
# https://panda-clip.com/flask-uploads/

# タグ https://html-coding.co.jp/annex/dictionary/html/input/