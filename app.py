import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import feedparser
from textblob import TextBlob

# ==========================================
# ⚙️ AYARLAR
# ==========================================
st.set_page_config(page_title="Finans Asistanı V16.2", page_icon="🏦", layout="wide")

ASSET_DATABASE = [
    {"symbol": "TRY=X", "name": "DOLAR (USD)", "cat": "Döviz", "halal": True, "search_term": "USDTRY currency"},
    {"symbol": "EURTRY=X", "name": "EURO (EUR)", "cat": "Döviz", "halal": True, "search_term": "EURTRY currency"},
    {"symbol": "GC=F", "name": "ALTIN (Ons)", "cat": "Emtia", "halal": True, "search_term": "Gold price forecast"},
    {"symbol": "SI=F", "name": "GÜMÜŞ (Ons)", "cat": "Emtia", "halal": True, "search_term": "Silver price forecast"},
    {"symbol": "THYAO.IS", "name": "THY", "cat": "Borsa", "halal": True, "search_term": "Turkish Airlines stock"},
    {"symbol": "BIMAS.IS", "name": "BIM", "cat": "Borsa", "halal": True, "search_term": "BIMAS stock"},
    {"symbol": "ASELS.IS", "name": "ASELSAN", "cat": "Borsa", "halal": True, "search_term": "Aselsan defense stock"},
    {"symbol": "TUPRS.IS", "name": "TUPRAS", "cat": "Borsa", "halal": True, "search_term": "Tupras refinery stock"},
    {"symbol": "AKBNK.IS", "name": "AKBANK", "cat": "Borsa", "halal": False, "search_term": "Akbank stock"},
    {"symbol": "GARAN.IS", "name": "GARANTI", "cat": "Borsa", "halal": False, "search_term": "Garanti BBVA stock"},
    {"symbol": "BTC-USD", "name": "BITCOIN", "cat": "Kripto", "halal": True, "search_term": "Bitcoin crypto news"},
    {"symbol": "ETH-USD", "name": "ETHEREUM", "cat": "Kripto", "halal": True, "search_term": "Ethereum crypto news"},
    {"symbol": "SOL-USD", "name": "SOLANA", "cat": "Kripto", "halal": True, "search_term": "Solana crypto news"}
]

def analyze_news_sentiment(search_term):
    try:
        query = search_term.replace(" ", "%20")
        rss_url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        polarity_sum = 0
        count = 0
        for entry in feed.entries[:5]:
            analysis = TextBlob(entry.title)
            polarity_sum += analysis.sentiment.polarity
            count += 1
        return polarity_sum / count if count > 0 else 0
    except: return 0

# ==========================================
# 📱 ANA EKRAN
# ==========================================
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🏦 Finansal Asistan</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Dinamik Risk Yönetimi ile Hibrit Analiz</p>", unsafe_allow_html=True)
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
            captions=[
                "Ana para koruması. (Maks. %40 Tek Varlık)",
                "Enflasyonu yenmek. (Maks. %60 Tek Varlık)",
                "Maksimum getiri. (Limit Yok, %100 Tek Varlık Olabilir)"
            ],
            horizontal=True
        )
        
        st.write("")
        c_fx, c_comm, c_stk, c_cry = st.columns(4)
        with c_fx: use_forex = st.checkbox("Döviz", value=True)
        with c_comm: use_commodity = st.checkbox("Emtia", value=True)
        with c_stk: use_stock = st.checkbox("Borsa", value=True)
        with c_cry: use_crypto = st.checkbox("Kripto", value=True)
        
        st.markdown("---")
        use_sentiment = st.checkbox("📰 **Haber Analizini Dahil Et**", value=True)
        
        btn_run = st.button("🚀 Hibrit Analizi Başlat", type="primary", use_container_width=True)

st.divider()

if btn_run:
    # Banka Hesabı
    annual_rate = user_rate / 100.0
    gross_return = money * annual_rate * (months / 12)
    net_return_bank = gross_return * 0.95 
    total_bank = money + net_return_bank
    
    # Robo Hazırlık
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
        
    sentiment_scores = {}
    if use_sentiment:
        with st.status("📰 Yapay Zeka Haberleri Tarıyor...", expanded=True) as status:
            for cand in candidates:
                if cand['cat'] in ['Borsa', 'Kripto', 'Emtia', 'Döviz']:
                    st.write(f"Aranıyor: {cand['search_term']}...")
                    score = analyze_news_sentiment(cand['search_term'])
                    sentiment_scores[cand['symbol']] = score
                else:
                    sentiment_scores[cand['symbol']] = 0
            status.update(label="✅ Haber Analizi Tamamlandı!", state="complete", expanded=False)

    with st.spinner('Matematiksel Modeller Çalışıyor...'):
        try:
            tickers_map = {a['symbol']: a['name'] for a in candidates}
            df = yf.download(list(tickers_map.keys()), period="1y", progress=False)['Close']
            df.rename(columns=tickers_map, inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            df.ffill(inplace=True); df.bfill(inplace=True)
            
            returns = np.log(df / df.shift(1))
            trading_days = int(252 * (months / 12))
            mean_ret = returns.mean() * trading_days
            cov = returns.cov() * trading_days
            
            num_ports = 3000
            best_score = -float('inf')
            best_weights = []
            
            # --- DİNAMİK KISIT ---
            if "Koruyucu" in risk_choice:
                max_single_asset_weight = 0.40 
            elif "Dengeli" in risk_choice:
                max_single_asset_weight = 0.60 
            else:
                max_single_asset_weight = 1.00 

            for _ in range(num_ports):
                w = np.random.random(len(df.columns))
                w /= w.sum()
                
                if np.max(w) > max_single_asset_weight: 
                    continue 
                
                port_ret = np.sum(mean_ret * w)
                port_vol = np.sqrt(np.dot(w.T, np.dot(cov, w)))
                
                if "Koruyucu" in risk_choice: math_score = -port_vol 
                elif "Büyüme" in risk_choice: math_score = port_ret
                else: math_score = port_ret / port_vol if port_vol > 0 else 0
                
                sentiment_impact = 0
                if use_sentiment:
                    for idx, col in enumerate(df.columns):
                        sym = [k for k, v in tickers_map.items() if v == col][0]
                        s_score = sentiment_scores.get(sym, 0)
                        sentiment_impact += w[idx] * s_score
                
                impact_factor = 0.5 if "Büyüme" in risk_choice else 0.2
                final_score = math_score + (sentiment_impact * impact_factor)
                
                if final_score > best_score:
                    best_score = final_score
                    best_weights = w
            
            robo_ret_pct = np.sum(mean_ret * best_weights)
            robo_risk_pct = np.sqrt(np.dot(best_weights.T, np.dot(cov, best_weights)))
            
            net_return_robo = money * robo_ret_pct
            total_robo = money + net_return_robo
            
            c1, c2 = st.columns(2)
            c1.info(f"🏦 **{bank_label}**")
            c1.metric("Garanti Tutar", f"{total_bank:,.0f} TL", f"+{net_return_bank:,.0f} TL")
            
            delta_color = "normal" if net_return_robo > net_return_bank else "off"
            c2.success(f"🦅 **Akıllı Portföy ({risk_choice.split(' ')[1]})**")
            c2.metric("Tahmini Tutar", f"{total_robo:,.0f} TL", f"+{net_return_robo:,.0f} TL", delta_color=delta_color)
            
            if use_sentiment: c2.caption(f"ℹ️ Haber Analizi Dahil Edildi")
            st.markdown("---")
            
            if use_sentiment:
                with st.expander("📰 Piyasa Duygu Raporu", expanded=True):
                    st.caption("🟢: Olumlu Haberler (>0.05) | 🔴: Olumsuz Haberler (<-0.05) | ⚪: Nötr/Yatay")
                    st.divider()
                    cols = st.columns(4) 
                    relevant_assets = [k for k in sentiment_scores.keys() if tickers_map[k] in df.columns]
                    for i, sym in enumerate(relevant_assets):
                        col_idx = i % 4
                        score = sentiment_scores[sym]
                        name = tickers_map[sym]
                        if score > 0.05: icon = "🟢"; color="green"
                        elif score < -0.05: icon = "🔴"; color="red"
                        else: icon = "⚪"; color="gray"
                        with cols[col_idx]:
                            st.markdown(f"**{name}**")
                            st.markdown(f":{color}[{icon}] ({score:.2f})")

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
                
                with c_list:
                    # --- YENİ EKLENTİ: SEPET REHBERİ ---
                    st.caption("🔥: Haberler Pozitif | ❄️: Haberler Negatif | ➖: Nötr")
                    # -----------------------------------
                    final_data = []
                    for asset, w in portfolio:
                        if w < 0.01: continue
                        s_score = 0
                        for k,v in tickers_map.items(): 
                            if v == asset: s_score = sentiment_scores.get(k, 0)
                        trend = "🔥" if s_score > 0.05 else "❄️" if s_score < -0.05 else "➖"
                        final_data.append({"Varlık": asset, "Trend": trend, "Oran": f"%{w*100:.1f}", "Tutar": f"{money*w:,.2f} TL"})
                    st.dataframe(pd.DataFrame(final_data), hide_index=True)

        except Exception as e:
            st.error(f"Hata: {e}")