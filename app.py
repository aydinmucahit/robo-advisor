import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# ⚙️ AYARLAR VE VERİTABANI
# ==========================================
st.set_page_config(page_title="Robo-Advisor V11", page_icon="🏦", layout="wide")

# GÜNCEL BANKA ORANLARI (Temsili Veri Tabanı)
# Not: Gerçek bir uygulamada burası canlı API ile beslenir.
LIVE_BANK_DATA = {
    "Faiz": [
        {"bank": "ON Plus / Burgan", "rate": 0.54},
        {"bank": "Fibabanka Kiraz", "rate": 0.52},
        {"bank": "Enpara", "rate": 0.45},
        {"bank": "Garanti BBVA", "rate": 0.48}
    ],
    "Katilim": [
        {"bank": "Vakıf Katılım", "rate": 0.46},
        {"bank": "Ziraat Katılım", "rate": 0.44},
        {"bank": "Kuveyt Türk", "rate": 0.43},
        {"bank": "Albaraka", "rate": 0.42}
    ]
}

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
# 📱 ANA EKRAN GİRDİ ALANI
# ==========================================
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🏦 Yapay Zeka Finans Danışmanı</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Paranızın değerini korumak ve büyütmek için size özel strateji.</p>", unsafe_allow_html=True)

st.divider()

# --- GİRDİ FORMU ---
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        money = st.number_input("💰 Yatırım Tutarı (TL)", min_value=1000, value=100000, step=1000, format="%d")
    
    with col2:
        duration_options = {"1 Ay": 1, "3 Ay": 3, "6 Ay": 6, "1 Yıl": 12}
        selected_duration_label = st.selectbox("⏳ Vade (Paraya ne zaman ihtiyacınız var?)", list(duration_options.keys()), index=3)
        months = duration_options[selected_duration_label]

    st.markdown("### 🎯 Stratejinizi Seçin")
    
    # GÜNCELLENMİŞ RİSK AÇIKLAMALARI
    risk_choice = st.radio(
        "Risk Profiliniz:",
        ("🛡️ Muhafazakar", "⚖️ Dengeli", "🚀 Agresif"),
        captions=[
            "Paraya 1 yıl içinde ihtiyacınız varsa.",
            "3-5 yıl dokunmayacaksanız.",
            "'Bu para batarsa üzülmem' diyorsanız."
        ],
        horizontal=True
    )

    st.markdown("### ⚙️ Tercihler")
    
    c_fx, c_comm, c_stk, c_cry = st.columns(4)
    with c_fx: use_forex = st.checkbox("Döviz", value=True)
    with c_comm: use_commodity = st.checkbox("Emtia", value=True)
    with c_stk: use_stock = st.checkbox("Borsa", value=True)
    with c_cry: use_crypto = st.checkbox("Kripto", value=True)
    
    st.write("") 
    is_halal = st.toggle("💚 **İslami Hassasiyet (Helal Filtre)**", value=True)
    if is_halal:
        st.caption("Faizsiz Katılım Bankacılığı oranları baz alınır.")

    st.write("")
    btn_run = st.button("🚀 Portföyü Analiz Et ve Oluştur", type="primary", use_container_width=True)

st.divider()

# ==========================================
# 🧠 HESAPLAMA MOTORU
# ==========================================
if btn_run:
    # --- 1. EN İYİ BANKA ORANINI BUL ---
    category_key = "Katilim" if is_halal else "Faiz"
    bank_list = LIVE_BANK_DATA[category_key]
    
    # En yüksek oranı veren bankayı bul
    best_bank_offer = max(bank_list, key=lambda x: x['rate'])
    annual_rate = best_bank_offer['rate']
    bank_name = best_bank_offer['bank']
    
    gross_return = money * annual_rate * (months / 12)
    net_return_bank = gross_return * 0.95 
    total_bank = money + net_return_bank
    
    # --- 2. ROBO HESAPLAMA ---
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
        
    with st.spinner('Yapay Zeka piyasayı tarıyor, en iyi kombinasyonu hesaplıyor...'):
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
            
            num_ports = 5000
            best_score = -float('inf')
            best_weights = []
            
            for _ in range(num_ports):
                w = np.random.random(len(df.columns))
                w /= w.sum()
                
                port_ret = np.sum(mean_ret * w)
                port_vol = np.sqrt(np.dot(w.T, np.dot(cov, w)))
                
                if "Muhafazakar" in risk_choice: score = -port_vol 
                elif "Agresif" in risk_choice: score = port_ret
                else: score = port_ret / port_vol if port_vol > 0 else 0
                
                if score > best_score:
                    best_score = score
                    best_weights = w
            
            # Sonuçlar
            robo_ret_pct = np.sum(mean_ret * best_weights)
            robo_risk_pct = np.sqrt(np.dot(best_weights.T, np.dot(cov, best_weights)))
            
            net_return_robo = money * robo_ret_pct
            total_robo = money + net_return_robo
            
            # --- SONUÇ GÖRÜNTÜLEME ---
            st.subheader(f"📊 Analiz Sonucu ({risk_choice.split(' ')[1]} Mod)")
            
            c1, c2 = st.columns(2)
            
            # BANKA KARTI (GELİŞMİŞ)
            c1.info(f"🏦 **En İyi Teklif: {bank_name}**\n\n"
                    f"Oran (Yıllık): **%{annual_rate*100:.0f}**\n"
                    f"Garanti Getiri: **+{net_return_bank:,.0f} TL**")
            
            # UYARI METNİ (İstediğiniz Yasal Uyarı)
            c1.caption(f"⚠️ *Bu oran piyasa ortalamasıdır. Gerçek oranlar için {bank_name} veya kendi bankanızla iletişime geçiniz.*")
            
            # ROBO KARTI
            delta_color = "normal" if net_return_robo > net_return_bank else "off"
            c2.success(f"🦅 **Akıllı Portföy**\n\n"
                       f"Hedeflenen Tutar: **{total_robo:,.0f} TL**\n"
                       f"Beklenen Kazanç: **+{net_return_robo:,.0f} TL**")
            
            c2.caption(f"Risk Seviyesi: %{robo_risk_pct*100:.1f} (Geçmiş veriye dayalı tahmindir).")

            st.markdown("---")

            # Grafikler
            tab1, tab2 = st.tabs(["📈 Karşılaştırma", "🍰 Sepet Detayı"])
            
            with tab1:
                fig_bar = go.Figure(data=[
                    go.Bar(name=f'{bank_name}', x=['Net Kazanç'], y=[net_return_bank], marker_color='#95a5a6', text=[f"{net_return_bank:,.0f} TL"]),
                    go.Bar(name='Robo', x=['Net Kazanç'], y=[net_return_robo], marker_color='#27ae60', text=[f"{net_return_robo:,.0f} TL"])
                ])
                fig_bar.update_layout(title="Hangi Seçenek Daha Kârlı?", barmode='group')
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with tab2:
                portfolio = sorted(zip(df.columns, best_weights), key=lambda x:x[1], reverse=True)
                labels = [p[0] for p in portfolio if p[1] > 0.01]
                values = [p[1] for p in portfolio if p[1] > 0.01]
                
                c_pie, c_table = st.columns([1, 1])
                with c_pie:
                    fig_pie = px.pie(values=values, names=labels, title="Varlık Dağılımı", hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True)
                with c_table:
                    st.write("**Dağılım Tablosu**")
                    final_data = []
                    for asset, w in portfolio:
                        if w < 0.01: continue
                        final_data.append({"Varlık": asset, "Oran": f"%{w*100:.1f}", "Tutar": f"{money*w:,.2f} TL"})
                    st.dataframe(pd.DataFrame(final_data), hide_index=True)

        except Exception as e:
            st.error(f"Hata oluştu: {e}. Lütfen sayfayı yenileyin.")