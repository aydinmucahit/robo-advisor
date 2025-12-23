import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import feedparser
from textblob import TextBlob

# ==========================================
# ⚙️ AYARLAR VE VERİTABANI
# ==========================================
st.set_page_config(page_title="Finans Asistanı V15", page_icon="🏦", layout="wide")

ASSET_DATABASE = [
    {"symbol": "TRY=X", "name": "DOLAR (USD)", "cat": "Döviz", "halal": True},
    {"symbol": "EURTRY=X", "name": "EURO (EUR)", "cat": "Döviz", "halal": True},
    {"symbol": "GC=F", "name": "ALTIN (Ons)", "cat": "Emtia", "halal": True},
    {"symbol": "SI=F", "name": "GÜMÜŞ (Ons)", "cat": "Emtia", "halal": True},
    {"symbol": "THYAO.IS", "name": "THY", "cat": "Borsa", "halal": True},
    {"symbol": "BIMAS.IS", "name": "BIM", "cat": "Borsa", "halal": True},
    {"symbol": "ASELS.IS", "name": "ASELSAN", "cat": "Borsa", "halal": True},
    {"symbol": "TUPRS.IS", "name": "TUPRAS", "cat": "Borsa", "halal": True},
    {"symbol": "AKBNK.IS", "name": "AKBANK", "cat": "Borsa", "halal": False},
    {"symbol": "GARAN.IS", "name": "GARANTI", "cat": "Borsa", "halal": False},
    {"symbol": "BTC-USD", "name": "BITCOIN", "cat": "Kripto", "halal": True},
    {"symbol": "ETH-USD", "name": "ETHEREUM", "cat": "Kripto", "halal": True},
    {"symbol": "SOL-USD", "name": "SOLANA", "cat": "Kripto", "halal": True}
]

# ==========================================
# 📰 HABER VE DUYGU ANALİZ MOTORU (YENİ)
# ==========================================
def analyze_news_sentiment(asset_name):
    """
    Google News RSS üzerinden son haberleri çeker ve NLP ile puanlar.
    Skor: -1 (Çok Kötü) ile +1 (Çok İyi) arası.
    """
    try:
        # Finansal terimler evrensel olduğu için İngilizce kaynak daha zengindir
        rss_url = f"https://news.google.com/rss/search?q={asset_name}+finance+when:1d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        
        polarity_sum = 0
        count = 0
        
        # Son 5 haberi analiz et
        for entry in feed.entries[:5]:
            analysis = TextBlob(entry.title)
            polarity_sum += analysis.sentiment.polarity
            count += 1
            
        if count == 0: return 0 # Haber yoksa Nötr
        
        avg_score = polarity_sum / count
        return avg_score
    except:
        return 0

# ==========================================
# 📱 ANA EKRAN
# ==========================================
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🏦 Finansal Asistan</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Matematik + Haber Analizi (Hibrit Zeka)</p>", unsafe_allow_html=True)
st.divider()

with st.container():
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("1. Parametreler")
        money = st.number_input("💰 Yatırım Tutarı (TL)", min_value=1000, value=100000, step=1000, format="%d")
        
        duration_options = {"1 Ay": 1, "3 Ay": 3, "6 Ay": 6, "1 Yıl": 12}
        selected_duration_label = st.selectbox("⏳ Vade Seçimi", list(duration_options.keys()), index=3)
        months = duration_options[selected_duration_label]
        
        st.markdown("---")
        is_halal = st.toggle("İslami Hassasiyet (Katılım Modu)", value=True)
        
        st.info("👇 Banka Oranı (Manuel Giriş)")
        st.markdown("""<a href="https://www.hangikredi.com/yatirim-araclari/mevduat-faiz-oranlari" target="_blank" style="text-decoration: none;"><div style="background-color: #f0f2f6; padding: 5px; border-radius: 5px; text-align: center; border: 1px solid #d0d0d0; font-size:12px;">🔗 Oranları Gör</div></a>""", unsafe_allow_html=True)
        
        if is_halal:
            user_rate = st.number_input("Katılım Kâr Payı (%)", 0.0, 100.0, 42.0, 0.5)
            bank_label = "Katılım Hesabı"
        else:
            user_rate = st.number_input("Mevduat Faizi (%)", 0.0, 100.0, 53.0, 0.5)
            bank_label = "Mevduat Hesabı"

    with col2:
        st.subheader("2. Strateji")
        risk_choice = st.radio(
            "Risk Profiliniz:",
            ("🛡️ Koruyucu", "⚖️ Dengeli", "🚀 Büyüme Odaklı"),
            captions=["Ana para koruması.", "Enflasyonu yenmek.", "Maksimum getiri."],
            horizontal=True
        )
        
        st.write("")
        c_fx, c_comm, c_stk, c_cry = st.columns(4)
        with c_fx: use_forex = st.checkbox("Döviz", value=True)
        with c_comm: use_commodity = st.checkbox("Emtia", value=True)
        with c_stk: use_stock = st.checkbox("Borsa", value=True)
        with c_cry: use_crypto = st.checkbox("Kripto", value=True)
        
        st.markdown("---")
        # YENİ ÖZELLİK: HABER ANALİZİ SEÇENEĞİ
        use_sentiment = st.checkbox("📰 **Haber Analizini (Sentiment) Dahil Et**", value=True, help="Yapay zeka Google News'teki son dakika haberlerini okur ve portföyü ona göre ayarlar.")
        
        btn_run = st.button("🚀 Hibrit Analizi Başlat", type="primary", use_container_width=True)

st.divider()

if btn_run:
    # 1. Banka Hesabı
    annual_rate = user_rate / 100.0
    gross_return = money * annual_rate * (months / 12)
    net_return_bank = gross_return * 0.95 
    total_bank = money + net_return_bank
    
    # 2. Robo Hazırlık
    active_cats = []
    if use_forex: active_cats.append("Döviz")
    if use_commodity: active_cats.append("Emtia")
    if use_stock: active_cats.append("Borsa")
    if use_crypto: active_cats.append("Kripto")
    
    candidates = [a for a in ASSET_DATABASE if a['cat'] in active_cats]
    if is_halal: candidates = [a for a in candidates if a['halal']]
    
    if len(candidates) < 2:
        st.error("⚠️ En az 2 varlık grubu seçmelisiniz.")
        st.stop()
        
    # --- AŞAMA 1: HABER ANALİZİ (SENTIMENT) ---
    sentiment_scores = {}
    if use_sentiment:
        with st.status("📰 Yapay Zeka Haberleri Okuyor...", expanded=True) as status:
            for cand in candidates:
                # Sadece Borsa ve Kripto haberlerine bak (Döviz/Altın genelde makrodur)
                if cand['cat'] in ['Borsa', 'Kripto']:
                    st.write(f"Analiz ediliyor: {cand['name']}...")
                    score = analyze_news_sentiment(cand['name'])
                    sentiment_scores[cand['symbol']] = score
                else:
                    sentiment_scores[cand['symbol']] = 0 # Nötr
            status.update(label="✅ Haber Analizi Tamamlandı!", state="complete", expanded=False)

    with st.spinner('Matematiksel Modeller Çalışıyor...'):
        try:
            tickers_map = {a['symbol']: a['name'] for a in candidates}
            df = yf.download(list(tickers_map.keys()), period="1y", progress=False)['Close']
            df.rename(columns=tickers_map, inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            df.ffill(inplace=True); df.bfill(inplace=True)
            
            # İstatistikler
            returns = np.log(df / df.shift(1))
            trading_days = int(252 * (months / 12))
            mean_ret = returns.mean() * trading_days
            cov = returns.cov() * trading_days
            
            num_ports = 3000
            best_score = -float('inf')
            best_weights = []
            
            for _ in range(num_ports):
                w = np.random.random(len(df.columns))
                w /= w.sum()
                
                port_ret = np.sum(mean_ret * w)
                port_vol = np.sqrt(np.dot(w.T, np.dot(cov, w)))
                
                # --- HİBRİT ZEKA KARAR MEKANİZMASI ---
                # 1. Matematiksel Skor
                if "Koruyucu" in risk_choice: math_score = -port_vol 
                elif "Agresif" in risk_choice: math_score = port_ret
                else: math_score = port_ret / port_vol if port_vol > 0 else 0
                
                # 2. Haber Etkisi (Sentiment Adjustment)
                sentiment_impact = 0
                if use_sentiment:
                    # Portföyün toplam duygu puanını hesapla
                    # (Varlığın ağırlığı * Varlığın haber puanı)
                    for idx, col in enumerate(df.columns):
                        # Sembolü bulmak için ters arama
                        sym = [k for k, v in tickers_map.items() if v == col][0]
                        s_score = sentiment_scores.get(sym, 0)
                        sentiment_impact += w[idx] * s_score
                
                # Final Skor = Matematik + (Haber * Katsayı)
                # Agresif modda haberler daha etkilidir
                impact_factor = 0.5 if "Agresif" in risk_choice else 0.2
                final_score = math_score + (sentiment_impact * impact_factor)
                
                if final_score > best_score:
                    best_score = final_score
                    best_weights = w
            
            # Sonuç Hesaplama
            robo_ret_pct = np.sum(mean_ret * best_weights)
            robo_risk_pct = np.sqrt(np.dot(best_weights.T, np.dot(cov, best_weights)))
            
            net_return_robo = money * robo_ret_pct
            total_robo = money + net_return_robo
            
            # --- SONUÇ EKRANI ---
            c1, c2 = st.columns(2)
            
            c1.info(f"🏦 **{bank_label}**")
            c1.metric("Garanti Tutar", f"{total_bank:,.0f} TL", f"+{net_return_bank:,.0f} TL")
            
            delta_color = "normal" if net_return_robo > net_return_bank else "off"
            c2.success(f"🦅 **Akıllı Portföy ({risk_choice.split(' ')[1]})**")
            c2.metric("Tahmini Tutar", f"{total_robo:,.0f} TL", f"+{net_return_robo:,.0f} TL", delta_color=delta_color)
            
            if use_sentiment:
                c2.caption(f"ℹ️ Haber Analizi: Portföy ağırlıkları son dakika gelişmelerine göre optimize edildi.")

            st.markdown("---")
            
            # Sentiment Göstergesi (Yeni)
            if use_sentiment:
                with st.expander("📰 Piyasa Duygu Raporu (Sentiment)", expanded=True):
                    cols = st.columns(len(sentiment_scores))
                    # Sadece seçilen varlıkları göster
                    relevant_assets = [k for k in sentiment_scores.keys() if tickers_map[k] in df.columns]
                    
                    for sym in relevant_assets:
                        score = sentiment_scores[sym]
                        name = tickers_map[sym]
                        if score > 0.1: icon = "🟢 Pozitif"; color="green"
                        elif score < -0.1: icon = "🔴 Negatif"; color="red"
                        else: icon = "⚪ Nötr"; color="gray"
                        st.markdown(f"**{name}**: :{color}[{icon}] ({score:.2f})")

            # Grafikler
            tab1, tab2 = st.tabs(["📈 Kârlılık", "🍰 Sepet"])
            with tab1:
                fig_bar = go.Figure(data=[
                    go.Bar(name='Banka', x=['Tutar'], y=[total_bank], marker_color='#95a5a6', text=[f"{total_bank:,.0f}"]),
                    go.Bar(name='Robo', x=['Tutar'], y=[total_robo], marker_color='#27ae60', text=[f"{total_robo:,.0f}"])
                ])
                st.plotly_chart(fig_bar, use_container_width=True)
            with tab2:
                portfolio = sorted(zip(df.columns, best_weights), key=lambda x:x[1], reverse=True)
                labels = [p[0] for p in portfolio if p[1] > 0.01]
                values = [p[1] for p in portfolio if p[1] > 0.01]
                c_pie, c_list = st.columns([1, 1])
                c_pie.plotly_chart(px.pie(values=values, names=labels, hole=0.4), use_container_width=True)
                
                final_data = []
                for asset, w in portfolio:
                    if w < 0.01: continue
                    # Haber etkisi ikonu
                    s_score = 0
                    for k,v in tickers_map.items(): 
                        if v == asset: s_score = sentiment_scores.get(k, 0)
                    
                    trend = "🔥" if s_score > 0.1 else "❄️" if s_score < -0.1 else ""
                    final_data.append({"Varlık": f"{asset} {trend}", "Oran": f"%{w*100:.1f}", "Tutar": f"{money*w:,.2f} TL"})
                c_list.dataframe(pd.DataFrame(final_data), hide_index=True)

        except Exception as e:
            st.error(f"Hata: {e}")