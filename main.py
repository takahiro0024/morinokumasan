import openai
import googlemaps
import streamlit as st
import random
import pandas as pd

# APIキーを設定
api_key = os.getenv("OPENAI_API_KEY")
gmaps = googlemaps.Client(key='AIzaSyC7MCzsFZqsGH1wQaGnxV7YfLfJqef_ROM')


# 住所を緯度と経度に変換する関数
def geocode_address(address):
    try:
        geocode_result = gmaps.geocode(address, language='ja')
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            return None, None
    except Exception as e:
        st.error(f"ジオコーディング中にエラーが発生しました: {str(e)}")
        return None, None

# サウナのリストをGoogle Maps APIから取得し、最寄りの3つを返す関数
def get_saunas_nearby(lat, lng, radius=5000, limit=3):  # 半径5kmのサウナを検索
    try:
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius,
            keyword='sauna',
            language='ja'  # 日本語でのレスポンスを要求
        )
        saunas = places_result['results']
        
        # 現在地からの距離でソート
        saunas_sorted = sorted(saunas, key=lambda x: gmaps.distance_matrix(
            origins=(lat, lng),
            destinations=(x['geometry']['location']['lat'], x['geometry']['location']['lng']),
            mode='walking',
            language='ja'
        )['rows'][0]['elements'][0]['distance']['value'])
        
        # 最寄りのサウナ3件を返す
        return saunas_sorted[:limit]
    except Exception as e:
        st.error(f"サウナの検索中にエラーが発生しました: {str(e)}")
        return []

# ラーメン屋のリストをGoogle Maps APIから取得する関数
def get_restaurants_nearby(lat, lng, radius=5000):  # サウナの近くの半径5km以内のラーメン屋を検索
    try:
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius,
            keyword='ラーメン',
            language='ja'  # 日本語でのレスポンスを要求
        )
        return places_result['results']
    except Exception as e:
        st.error(f"ラーメン屋の検索中にエラーが発生しました: {str(e)}")
        return []

# OpenAIを使って気分を判定する関数
def analyze_mood(prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは日本語で応答するアシスタントです。短く簡潔に答えてください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # 応答の一貫性を高めるために低めに設定
            max_tokens=50  # 応答の長さを制限
        )
        mood = response.choices[0].message.content.strip()
        return mood
    except Exception as e:
        st.error(f"気分解析中にエラーが発生しました: {str(e)}")
        return None

# 乗換案内APIを使って行き方を提案する関数
def get_route_directions(start_lat, start_lng, end_lat, end_lng):
    try:
        url = f"https://api.norikaeapi.com/v1/route?start={start_lat},{start_lng}&end={end_lat},{end_lng}&key={norikae_api_key}"
        response = requests.get(url)
        data = response.json()
        if data['routes']:
            return data['routes'][0]['summary']
        else:
            return "経路が見つかりませんでした。"
    except Exception as e:
        st.error(f"経路取得中にエラーが発生しました: {str(e)}")
        return "経路の取得に失敗しました。"

# サウナをレコメンドする関数
def recommend_sauna(saunas, mood):
    random.seed(mood)
    return random.choice(saunas) if saunas else None

# Streamlit UI
st.title("サウナとラーメン最高じゃね！？")

address = st.text_input("現在地の住所を入力してください（例: 東京都新宿区西新宿2-8-1）")
user_input = st.text_input("今日はどんな気分ですか？自由に入力してください。")

if st.button("サウナとラーメン屋をレコメンド"):
    if address and user_input:
        lat, lng = geocode_address(address)
        if lat and lng:
            saunas = get_saunas_nearby(lat, lng)
            mood = analyze_mood(f"今日は{user_input}気分です。おすすめのサウナを教えてください。")
            if mood:
                st.write(f"解析された気分: {mood}")

                recommended_sauna = recommend_sauna(saunas, mood)
                if recommended_sauna:
                    st.write(f"あなたにオススメのサウナは: **{recommended_sauna['name']}**")
                    st.write(f"住所: {recommended_sauna['vicinity']}")
                    if 'rating' in recommended_sauna:
                        st.write(f"評価: {recommended_sauna['rating']}")

                    # 地図表示
                    sauna_location = pd.DataFrame({
                        'lat': [recommended_sauna['geometry']['location']['lat']],
                        'lon': [recommended_sauna['geometry']['location']['lng']]
                    })
                    st.map(sauna_location)

                    # サウナの近くのラーメン屋を検索
                    restaurants = get_restaurants_nearby(
                        recommended_sauna['geometry']['location']['lat'],
                        recommended_sauna['geometry']['location']['lng']
                    )
                    if restaurants:
                        st.write("近くのラーメン屋:")
                        for restaurant in restaurants[:5]:  # 上位5件を表示
                            st.write(f"**{restaurant['name']}**")
                            st.write(f"住所: {restaurant['vicinity']}")
                            if 'rating' in restaurant:
                                st.write(f"評価: {restaurant['rating']}")
                            st.write(f"[Google Mapsで表示](https://www.google.com/maps/search/?api=1&query={restaurant['geometry']['location']['lat']},{restaurant['geometry']['location']['lng']})")
                    else:
                        st.write("近くのラーメン屋が見つかりませんでした。")
                else:
                    st.write("ご指定の気分に合ったサウナが見つかりませんでした。")
            else:
                st.write("気分の解析に失敗しました。")
        else:
            st.write("住所のジオコーディングに失敗しました。")
    else:
        st.write("住所と気分を入力してください。")
