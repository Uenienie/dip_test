import pandas as pd
import numpy as np
from sklearn import preprocessing
import re
import mojimoji
import pickle


def prediction(x):
	test_No = x["お仕事No."]
	x = x.dropna(how='any', axis=1).drop('お仕事No.', axis=1)
	
	# ----------------------------------------------------------------------------------------------------------------
	# testデータの前処理
	# ----------------------------------------------------------------------------------------------------------------
	
	# 休暇曜日に関して -----------------------------------------------------------------------------------------------
	x["weekday"] = x["休日休暇(月曜日)"] + x["休日休暇(火曜日)"] + x["休日休暇(水曜日)"] + x["休日休暇(木曜日)"] + x["休日休暇(金曜日)"]
	x["holiday"] = x["休日休暇(土曜日)"] + x["休日休暇(日曜日)"] + x["休日休暇(祝日)"]
	day = ["休日休暇(月曜日)", "休日休暇(火曜日)", "休日休暇(水曜日)", "休日休暇(木曜日)", "休日休暇(金曜日)", "休日休暇(土曜日)", "休日休暇(日曜日)", "休日休暇(祝日)", "土日祝のみ勤務", "平日休みあり", "土日祝休み"]
	x = x.drop(day, axis=1)
	
	# 年齢に関して----------------------------------------------------------------------------------------------------
	age = ["20代活躍中", "30代活躍中", "ミドル（40〜）活躍中"]
	x = x.drop(age, axis=1)
	
	# 最低出勤数/週 に関して -----------------------------------------------------------------------------------------
	attendance = ["週1日からOK", "週2・3日OK", "週4日勤務"]
	number_attendance = [1, 2.5, 4]
	x["attendance"] = 5.0
	for i, j in zip (number_attendance, attendance):
		for k in range(len(x)):
			if (x[j][k] == 1):
				x["attendance"][k] = i
	x = x.drop(attendance, axis=1)
	
	# 残業に関して ---------------------------------------------------------------------------------------------------
	overtime = ["残業なし", "残業月10時間未満", "残業月20時間未満", "残業月20時間以上"]
	number_overtime = [0, 10, 20, 30]
	x["overtime"] = 0
	for i, j in zip (number_overtime, overtime):
		for k in range(len(x)):
			if (x[j][k] == 1):
				x["overtime"][k] = i
	x = x.drop(overtime, axis=1)
	
	# 勤務時間に関して -----------------------------------------------------------------------------------------------
	business_low_time = ["短時間勤務OK(1日4h以内)", "1日7時間以下勤務OK"]
	number_business_low_time = ["4", "7"]
	x["business_low_time"] = 9
	for i, j in zip (number_business_low_time, business_low_time):
		for k in range(len(x)):
			if (x[j][k] == 1):
				x["business_low_time"][k] = i
	x = x.drop(business_low_time, axis=1)
	
	# 経験の有無について ---------------------------------------------------------------------------------------------
	experience = ["未経験OK", "経験者優遇"]
	x["experience"] = 2
	for i in range(len(x)):
		if ((x["未経験OK"][i] == 0) & (x["経験者優遇"][i] == 1)):
			x["experience"][i] = 1
		
		elif ((x["未経験OK"][i] == 1) & (x["経験者優遇"][i] == 0)):
			x["experience"][i] = 0
	x = x.drop(experience, axis=1)
	
	# 英語力の有無について -------------------------------------------------------------------------------------------
	english = ["英語力不要", "英語力を活かす"]
	number_english = [0, 1, 2]
	x["english"] = 1
	for i, j in zip (number_english, english):
		for k in range(len(x)):
			if (x[j][k] == 1):
				x["english"][k] = i
	x = x.drop(english, axis=1)
	
	# Microsoftのソフトを何種類使えるか ------------------------------------------------------------------------------
	microsoft = ["Wordのスキルを活かす", "Excelのスキルを活かす", "PowerPointのスキルを活かす"]
	x["microsoft"] = 0
	for i in microsoft:
		for j in range(len(x)):
			if (x[i][j] == 1):
				x["microsoft"][k] = x["microsoft"][k] + 1
	x = x.drop(microsoft, axis=1)
	
	# 輻輳について ---------------------------------------------------------------------------------------------------
	wear = ["制服あり", "服装自由"]
	x["wear"] = 0
	for i in range(len(x)):
		if (x["服装自由"][i] == 1):
			x["wear"][i] = 1
	x = x.drop(wear, axis=1)
	
	
	# "期間・時間　勤務時間" において，開始/終了 時間・勤務時間・休憩時間を抽出 --------------------------------------
	x["launch_work_time"], x["end_work_time"], x["work_time"], x["rest_time"] = 0, 0, 0, 0
	
	for i in range(len(x)):
	# ----------------------------------------------------------------------------------------------------------------
	# 開始/終了 時間(日付が変わってから何時間後か)を計算
	# ----------------------------------------------------------------------------------------------------------------
		work_regex = re.compile((r'(\d+):(\d+)〜(\d+):(\d+)'))
		work_time = work_regex.search(x["期間・時間　勤務時間"][i]).group()
		
		x["launch_work_time"][i] = work_time.split('〜')[0]  # この段階では 9:00 のような形で格納されている．
		x["launch_work_time"][i] = (int(x["launch_work_time"][i].split(':')[0])*60 + int(x["launch_work_time"][i].split(':')[1]))/60
		x["end_work_time"][i] = work_time.split('〜')[1]
		x["end_work_time"][i] = (int(x["end_work_time"][i].split(':')[0])*60 + int(x["end_work_time"][i].split(':')[1]))/60
		x["launch_work_time"][i], x["end_work_time"][i] = round(x["launch_work_time"][i], 3), round(x["end_work_time"][i], 3)
		
	# ----------------------------------------------------------------------------------------------------------------
	# 休憩時間の抽出，勤務時間の計算
	# ----------------------------------------------------------------------------------------------------------------
		x["期間・時間　勤務時間"][i] = mojimoji.zen_to_han(x["期間・時間　勤務時間"][i]) # 数字を半角変換
		
		# 休憩がない求人に着目し，労働時間を計算
		if (("休憩はありません" in x["期間・時間　勤務時間"][i]) | ("休憩はなし分です" in x["期間・時間　勤務時間"][i]) | ("休憩はなしです" in x["期間・時間　勤務時間"][i]) | ("休憩は有りません" in x["期間・時間　勤務時間"][i]) | ("休憩なし" in x["期間・時間　勤務時間"][i])):
			x["work_time"][i] = x["end_work_time"][i] - x["launch_work_time"][i]
			continue
		
		# 休憩がある求人に着目し，労働時間を計算
		if ("休憩" in x["期間・時間　勤務時間"][i]):
			x["期間・時間　勤務時間"][i] = x["期間・時間　勤務時間"][i].replace("休憩", "rest").replace("は", "").replace("計", "").replace("交替制で", "").replace("交代制で", "").replace("交替制", "").replace("交代制", "")
			rest_regex = re.compile((r'rest(\d+)'))
			rest_time = rest_regex.search(x["期間・時間　勤務時間"][i]).group().replace("rest", "")  # 何分か
			#all["rest_time"][i] = int(rest_time) / 60
			x["work_time"][i] = x["end_work_time"][i] - x["launch_work_time"][i] - round(int(rest_time) / 60, 3)
			x["rest_time"][i] = int(rest_time)
		
		# 休憩の記載がない求人に着目し，労働時間を計算
		else:
			x["work_time"][i] = x["end_work_time"][i] - x["launch_work_time"][i]
		
		
		x["launch_work_time"], x["end_work_time"] = x["launch_work_time"].astype("float"), x["end_work_time"].astype("float")
	
	# 拠点番号をカウントエンコーディング -----------------------------------------------------------------------------
	prefecture_figure = {"206東京":11527, "310愛知": 421, '214神奈川': 992, '404梅田': 985, '408奈良': 156, '212千葉': 316, '406兵庫': 280, '504広島': 154, '701福岡': 339, '403京都': 386, '204埼玉': 371, '201茨城': 330, '601香川': 105, '311豊田': 25, '306長野': 109, '307岐阜': 195, '407姫路': 22, '703大分': 72, '603徳島': 57, '702北九州': 114, '704佐賀': 75, '409和歌山': 81, '202栃木': 240, '103秋田': 23, '308静岡': 197, '106宮城': 215, '203群馬': 193, '305山梨': 78, '402滋賀': 52, '301新潟': 149, '107福島': 43, '503岡山': 67, '105山形': 30, '705長崎': 66, '102青森': 36, '101札幌': 125, '506山口': 43, '309浜松': 70, '706熊本': 40, '708鹿児島': 30, '707宮崎': 36, '304福井': 50, '604高知': 27, '302富山': 41, '401三重': 60, '303石川': 41, '104岩手': 54, '501鳥取': 15, '709沖縄': 5, '602愛媛': 41, '502島根': 36, '308沼津': 29}
	
	x["region"] = 0
	# ---------------------------------------------------------------------------
	# 各拠点番号に対して，辞書のkeyとセットになっているvalueを代入
	# ---------------------------------------------------------------------------
	for key, value in zip (prefecture_figure.keys(), prefecture_figure.values()):
		index = x.loc[x["拠点番号"] == key].index
		x["region"][index] = value
	
	# ----------------------------------------------------------------------------------------------------------------
	# 各路線をカウントエンコーディング
	# ----------------------------------------------------------------------------------------------------------------
	line_figure = {'東京メトロ千代田線': 276, '東京メトロ日比谷線': 496, '山手線': 4037, '小田急小田原線': 126, '常磐線': 256, '総武本線': 177, '中央・総武各駅停車': 599, '東京メトロ有楽町線': 482, '東京メトロ銀座線': 604, '京王井の頭線': 54, '都営大江戸線': 371, '東京メトロ丸ノ内線': 628, '東京メトロ東西線': 529, '都営浅草線': 180, '中央本線': 458, '京王線': 279, '都営三田線': 262, '京王相模原線': 21, '東急田園都市線': 134, 'なし': 762, '東京メトロ半蔵門線': 416,'東急大井町線': 30, '都営新宿線': 190, '多摩都市モノレール': 16, '東京メトロ南北線': 201, '東急東横線': 120, '京浜東北・根岸線': 451, '東武東上線': 94, '京葉線': 155, '埼京線': 96, '青梅線': 9, '武蔵野線': 44, '西武池袋・豊島線': 119, 'ゆりかもめ': 47, '横須賀線': 91, '京成電鉄本線': 14, '千代田・常磐各駅停車': 11, '西武新宿線': 81, '都電荒川線': 18, 'りんかい線': 95, '東京メトロ副都心線': 71, '西武拝島線': 12, 'つくばエクスプレス': 75, '東急池上線': 53, '東武伊勢崎・大師線': 52, '東京モノレール': 49, '京急本線': 145, '東急多摩川線': 7, '西武多摩川線': 4, '東京メトロ方南支線': 19, '東急目黒線': 12, '南武線': 38, '京急空港線': 12, '八高線': 10, '京成押上線': 10, '名古屋市営鶴舞線': 28, '東海道線': 859, '大阪メトロ御堂筋線': 234, '横浜線': 52, '大阪環状線': 142, '近鉄橿原線': 38, '内房線': 18, '大阪メトロ堺筋線': 51, '大阪メトロ四つ橋線': 62, '阪急神戸線': 47, '山陽本線': 139, '福岡市営空港線': 113, '大阪メトロ谷町線': 82, '神戸市営西神山手線': 37, '京都市営烏丸線': 136, '小田急江ノ島線': 41, 'みなとみらい線': 87, '近鉄難波・奈良線': 54, '埼玉新都市交通': 11, '阪和線': 15, 'ＪＲ東西線': 50, '近鉄けいはんな線': 8, '阪神本線': 55, '京阪本線': 42, 'ブルーライン': 50, '高崎線': 88, '西鉄天神大牟田線': 57, '阪急京都線': 65, '名古屋市営名城線': 20, '川越線': 10, 'しなの鉄道': 12, '名古屋市営東山線': 113, '六甲アイランド線': 10, '山陰本線': 26, '湘南モノレール': 3, '東武野田線': 13, '神戸電鉄粟生線': 6, '京阪中之島線': 18, '福岡市営箱崎線': 25, '大阪メトロ中央線': 31, '名古屋市営桜通線': 39, '近鉄京都線': 43, '神戸高速鉄道東西線': 7, '大阪メトロ長堀鶴見緑地線': 10, '外房線': 10, '南海本線': 47, '埼玉高速鉄道': 6, '新京成線': 19, '東北本線': 231, '福岡市営七隈線': 15, '山陽電気鉄道網干線': 3, '京急久里浜線': 9, '金沢シーサイドライン': 26, '桜島線': 3, '日豊本線': 81, '阪急宝塚線': 12, '北総線': 8, '愛知環状鉄道': 3, '牟岐線': 19, '鶴見線': 1, '千葉都市モノレール': 8, '阪急箕面線': 2, '相鉄本線': 8, '御殿場線': 9, '京成千葉線': 8, '名鉄西尾線': 5, '相模線': 15, '名古屋臨海高速鉄道あおなみ線': 22, '成田線': 7, '博多南線': 11, '紀勢本線': 37, '名古屋市営名港線': 5, '近鉄南大阪線': 10, '秩父鉄道線': 3, '南海高野線': 7, '阪急今津線': 5, '鹿児島本線': 169, '阪堺電気軌道阪堺線': 2, '奥羽本線': 49, '長良川鉄道': 6, '関西本線': 43, '阪急伊丹線': 2, '仙台市地下鉄南北線': 82, '関東鉄道常総線': 19, '東武宇都宮線': 33, '広島電鉄本線': 13, '名鉄名古屋本線': 11, '福知山線': 6, '名鉄空港線': 1, '西鉄甘木線': 2, '関西空港線': 7, '名鉄豊田線': 2, '上越線': 20, '北大阪急行南北線': 11, '流鉄流山線': 1, '泉北高速鉄道': 8, '名鉄常滑線': 3, '長崎本線': 47, '大阪メトロ千日前線': 5, '阪神なんば線': 4, '京都市営東西線': 22, '神戸新交通': 25, '桜井線': 15, '広島電鉄宮島線': 7, '神戸市営海岸線': 6, '信越本線': 110, '小田急多摩線': 4, '叡山電鉄': 29, '長崎電軌本線': 17, '山陽電気鉄道本線': 5, '芝山鉄道': 1, '近鉄大阪線': 14, '学研都市線': 8, '大阪メトロ南港ポートタウン線': 2, '八戸線': 2, '京福嵐山本線': 2, '札幌市営東西線': 26, 'アストラムライン': 17, '名鉄犬山線': 4, '札幌市営南北線': 53, 'グリーンライン': 5, '京福北野線': 6, '湘南新宿ライン(宇都宮・横須賀線)': 16, '徳島線': 4, '富士急行': 2, '高徳線': 29, '西鉄貝塚線': 4, '久大本線': 17, '大阪モノレール彩都線': 6, '東武小泉線': 42, 'えちぜん鉄道勝山線': 2, '熊本電気鉄道': 2, '小海線': 2, '筑豊本線': 14, '京成千原線': 1, '予讃線': 33, '富山地鉄不二越上滝': 9, '鹿島線': 10, '近鉄名古屋線': 14, '近鉄生駒線': 6, '越後線': 13, '鳴門線': 1, '仙石線': 13, '佐世保線': 15, 'しなの鉄道北しなの': 21, '大村線': 4, '宇部線': 5, '北陸鉄道石川線': 12, '飯田線': 7, '近鉄長野線': 3, '水戸線': 10, '名鉄小牧線': 4, '名鉄瀬戸線': 6, '阪急千里線': 3, '名鉄各務原線': 9, '指宿枕崎線': 5, '広島電鉄白島線': 3, '東海道・山陽新幹線': 3, '京阪鴨東線': 6, '上信電鉄上信線': 4, '長野電鉄長野線': 8, '高松琴平電鉄琴平線': 14, '長崎電軌桜町支線': 6, '羽越本線': 4, '北陸線': 50, 'のと鉄道・七尾線': 1, '身延線': 26, '静岡鉄道静岡清水線': 25, '鹿児島市電谷山線': 9, '両毛線': 31, '近鉄御所線': 1, '阿武隈急行': 3, '東武桐生線': 2, '名鉄竹鼻・羽島線': 6, '上越新幹線': 2, '南海加太線': 8, '和歌山線': 6, '近鉄湯の山線': 5, '高松琴平電鉄志度線': 6, '三岐鉄道三岐線': 4, '磐越西線': 2, '筑豊電気鉄道': 2, '近鉄吉野線': 1, '白新線': 10, '伊予鉄道環状線': 17, '広島電鉄皆実線': 2, '高山本線': 6, '芸備線': 2, '烏山線': 4, '千歳線': 7, '釜石線': 1, '根室本線': 6, '七尾線': 2, '土讃線': 3, '磐越東線': 2, '草津線': 9, '赤穂線': 2, '熊本市電健軍線': 4, '篠ノ井線': 34, '姫新線': 1, '伊予鉄道高浜線': 4, '福井鉄道福武線': 5, '四日市あすなろう鉄道内部・八王子線': 3, '近鉄山田鳥羽志摩線': 2, '養老鉄道': 6, '舞鶴線': 1, '香椎線': 6, '松本電気鉄道': 4, '東武日光線': 7, '日光線': 8, '奈良線': 3, '呉線': 6, '伊豆箱根鉄道駿豆線': 2, '樽見鉄道': 7, '湖西線': 5, '北九州高速鉄道': 8, '京阪石坂線': 5, '伊予鉄道横河原線': 1, '函館市電本線湯川線': 4, '大糸線': 6, '松浦鉄道西九州線': 11, '太多線': 5, '篠栗線': 3, '近江鉄道本線': 8, '京阪京津線': 2, '和歌山電鐵貴志川線': 4, '後藤寺線': 5, '水島臨海鉄道': 6, '札幌市営軌道線': 2, '遠州鉄道': 9, 'あいの風とやま鉄道': 14, '長崎電軌蛍茶屋支線': 5, '広島電鉄宇品線': 11, '近鉄天理線': 2, '宇野線': 7, '関東鉄道竜ヶ崎線': 2, '天竜浜名湖鉄道': 6, '可部線': 7, '富山ライトレール': 1, '土佐電気鉄道後免線': 1, '土佐電気鉄道伊野線': 1, '越美北線': 2, 'いわて銀河鉄道': 4, '花輪線': 1, '陸羽東線': 3, '豊肥本線': 1, '小浜線': 3, '仙台空港鉄道': 3, '学園都市線': 1, '近鉄田原本線': 1, '三岐鉄道北勢線': 1, 'えちぜん鉄道三国線': 1, '伊賀鉄道': 1, '岡山電軌清輝橋線': 1, '小野田線': 2, '明知鉄道': 1, '弥彦線': 4, '南海和歌山港線': 3, '唐津線': 2, '大湊線': 1, '札幌市営東豊線': 6, '鹿島臨海鉄道': 1, '山田線': 2, '函館本線': 17, 'ひたちなか海浜鉄道': 2, '山形新幹線': 1, '飯山線': 2, '高松琴平電鉄長尾線': 2, 'ＩＲいしかわ鉄道': 1, '山口線': 2, '境線': 1, '東武佐野線': 1, '北陸新幹線': 1, '水郡線': 5, '伊予鉄道郡中線': 1, '沖縄都市モノレール': 1, '西武多摩湖線': 2, '五日市線': 1, '東急世田谷線': 3, '日暮里舎人ライナー': 1, '能勢電鉄': 2, '相鉄いずみ野線': 1, '左沢線': 2, '大阪モノレール': 1, '東葉高速鉄道': 1, '阪神武庫川線': 1, '名鉄三河線': 1, '筑肥線': 3, '名鉄築港線': 2, '鹿児島市電唐湊線': 2, '名鉄広見線': 2, '宗谷本線': 2, '北陸鉄道浅野川線': 4, '室蘭本線': 1, '上毛電気鉄道上毛線': 2, '吉備線': 2, '東武亀戸線': 1}
	
	x["line"] = 0
	for key, value in zip (line_figure.keys(), line_figure.values()):
		index = x.loc[x["勤務地　最寄駅1（沿線名）"] == key].index
		x["line"][index] = value
	
	
	# objectの排除 ---------------------------------------------------------------------------------------------------
	object = ["掲載期間　開始日", "動画コメント", "休日休暇　備考", "（派遣）応募後の流れ", "期間・時間　勤務時間", "勤務地　備考", "拠点番号", "お仕事名", "期間・時間　勤務開始日", "動画タイトル", "仕事内容", "勤務地　最寄駅1（沿線名）", "応募資格", "派遣会社のうれしい特典", "掲載期間　終了日", "お仕事のポイント（仕事PR）", "動画ファイル名", "勤務地　最寄駅1（駅名）", "（派遣先）職場の雰囲気", "（派遣先）配属先部署"]
	x = x.drop(object, axis=1)
	
	x_column = x.columns
	
	# データの標準化 -------------------------------------------------------------------------------------------------
	scaler = preprocessing.StandardScaler()
	x = scaler.fit_transform(x)
	x = pd.DataFrame(x,  columns=x_column)
	
	x = x[['職場の様子', '勤務地固定', '大手企業', '交通費別途支給', '職種コード', 'ルーティンワークがメイン', '駅から徒歩5分以内', '対象者設定　年齢下限', '学校・公的機関（官公庁）', '給与/交通費　給与支払区分', 'CAD関連のスキルを活かす', '派遣スタッフ活躍中', '固定残業制', '大量募集', '公開区分', 'Accessのスキルを活かす', '検索対象エリア', '就業形態区分', 'フラグオプション選択', '期間・時間　勤務期間', '派遣形態', '勤務先公開', '16時前退社OK', '正社員登用あり', '雇用形態', 'Dip JobsリスティングS', '社員食堂あり', '資格取得支援制度あり', '対象者設定　年齢上限', '10時以降出社OK', '社会保険制度あり', '英語以外の語学力を活かす', '外資系企業', '履歴書不要', '研修制度あり', 'DTP関連のスキルを活かす', '会社概要　業界コード', '勤務地　都道府県コード', 'PCスキル不要', '車通勤OK', '仕事の仕方', '紹介予定派遣', 'シフト勤務', '給与/交通費　交通費', '新卒・第二新卒歓迎', '産休育休取得事例あり', '扶養控除内', '給与/交通費　給与下限', '対象者設定　性別', 'WEB登録OK', 'オフィスが禁煙・分煙', '勤務地　市区町村コード', 'weekday', 'holiday', 'attendance', 'overtime', 'business_low_time', 'experience', 'english', 'microsoft', 'wear', 'launch_work_time', 'end_work_time', 'work_time', 'rest_time', 'region', 'line']]
	
	
	# ----------------------------------------------------------------------------------------------------------------
	# 学習済みモデルを読み込み，予測
	# ----------------------------------------------------------------------------------------------------------------
	with open('model.pickle', mode='rb') as f:
		model = pickle.load(f)
	
	prediction = model.predict(x)
	prediction = np.where(prediction <= 0, 0, prediction)
	
	# ----------------------------------------------------------------------------------------------------------------
	# 予測結果をデータフレーム化
	# ----------------------------------------------------------------------------------------------------------------
	base = np.zeros((len(test_No), 2))
	ans = pd.DataFrame(base, columns=["お仕事No.", "応募数 合計"])
	ans["お仕事No."] = test_No
	ans["応募数 合計"] = prediction
	
	return(ans)
