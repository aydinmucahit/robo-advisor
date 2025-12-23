import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# ⚙️ AYARLAR VE VERİTABANI
# ==========================================
st.set_page_config(page_title="Finans Asistanı V14", page_icon="🏦", layout="wide")

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
# 📱 ANA EKRAN
# ==========================================
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🏦 Finansal Asistan</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Gerçek verilerle şeffaf hesaplama.</p>", unsafe_allow_html=True)
st.divider()

with st.container():
    # --- SOL KOLON: GİRDİLER ---
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("1. Parametreler")
        money = st.number_input("💰 Yatırım Tutarı (TL)", min_value=1000, value=100000, step=1000, format="%d")
        
        duration_options = {"1 Ay": 1, "3 Ay": 3, "6 Ay": 6, "1 Yıl": 12}
        selected_duration_label = st.selectbox("⏳ Vade Seçimi", list(duration_options.keys()), index=3)
        months = duration_options[selected_duration_label]
        
        st.markdown("---")
        
        # --- DÜZELTME 1: İKONSUZ VE SADELİK ---
        is_halal = st.toggle("İslami Hassasiyet (Katılım Modu)", value=True)
        
        st.info("👇 Banka/Katılım Oranını Giriniz")
        
        # --- DÜZELTME 2: YENİ SEKMEDE AÇILAN LİNK ---
        # Standart buton yerine HTML link kullanıyoruz ki sayfa kapanmasın.
        st.markdown("""
            <a href="https://www.hangikredi.com/yatirim-araclari/mevduat-faiz-oranlari" target="_blank" style="text-decoration: none;">
                <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid #d0d0d0; color: #31333F;">
                    🔗 Güncel Oranları Gör (Yeni Sekme)
                </div>
            </a>
            <br>
        """, unsafe_allow_html=True)
        
        if is_halal:
            user_rate = st.number_input("Katılım Kâr Payı Oranı (%)", min_value=0.0, max_value=100.0, value=42.0, step=0.5)
            bank_label = "Katılım Hesabı"
        else:
            user_rate = st.number_input("Mevduat Faiz Oranı (%)", min_value=0.0, max_value=100.0, value=53.0, step=0.5)
            bank_label = "Mevduat Hesabı"

    # --- SAĞ KOLON: STRATEJİ ---
    with col2:
        st.subheader("2. Strateji ve Tercihler")
        
        # --- DÜZELTME 3: İSİMLENDİRME (Muhafazakar -> Koruyucu) ---
        risk_choice = st.radio(
            "Risk Profiliniz:",
            ("🛡️ Koruyucu", "⚖️ Dengeli", "🚀 Büyüme Odaklı"),
            captions=[
                "Ana para koruması öncelikli. (Düşük Risk)",
                "Enflasyonu yenmek ve değer korumak. (Orta Risk)",
                "Maksimum getiri hedefi. (Yüksek Risk)"
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
        btn_run = st.button("🚀 Kıyaslamalı Analizi Başlat", type="primary", use_container_width=True)

st.divider()

if btn_run:
    # --- 1. BANKA HESABI ---
    annual_rate = user_rate / 100.0
    gross_return = money * annual_rate * (months / 12)
    net_return_bank = gross_return * 0.95 
    total_bank = money + net_return_bank
    
    # --- 2. ROBO HESABI ---
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
        
    with st.spinner('Piyasa verileri analiz ediliyor...'):
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
                
                # İsim değişikliğine göre mantık güncellemesi
                if "Koruyucu" in risk_choice: score = -port_vol 
                elif "Büyüme" in risk_choice: score = port_ret
                else: score = port_ret / port_vol if port_vol > 0 else 0
                
                if score > best_score:
                    best_score = score
                    best_weights = w
            
            robo_ret_pct = np.sum(mean_ret * best_weights)
            robo_risk_pct = np.sqrt(np.dot(best_weights.T, np.dot(cov, best_weights)))
            
            net_return_robo = money * robo_ret_pct
            total_robo = money + net_return_robo
            
            # --- SONUÇ KARTLARI ---
            st.subheader(f"📊 Analiz Sonucu")
            
            c1, c2 = st.columns(2)
            
            # BANKA SONUCU
            c1.info(f"🏦 **{bank_label} (Giriş: %{user_rate})**")
            c1.metric(label="Vade Sonu Garanti Tutar", 
                      value=f"{total_bank:,.0f} TL", 
                      delta=f"+{net_return_bank:,.0f} TL (Net Kazanç)")
            
            # ROBO SONUCU (Kartal Simgesi Silindi)
            delta_color = "normal" if net_return_robo > net_return_bank else "off"
            c2.success(f"**Akıllı Portföy ({risk_choice.split(' ')[1]})**")
            c2.metric(label="Vade Sonu Tahmini Tutar",
                      value=f"{total_robo:,.0f} TL",
                      delta=f"+{net_return_robo:,.0f} TL (Beklenen Kazanç)",
                      delta_color=delta_color)
            c2.caption(f"Risk Seviyesi: %{robo_risk_pct*100:.1f}")

            st.markdown("---")

            # GRAFİKLER
            tab1, tab2 = st.tabs(["📈 Kârlılık Karşılaştırması", "🍰 Portföy Detayı"])
            
            with tab1:
                fig_bar = go.Figure(data=[
                    go.Bar(name='Banka', x=['Vade Sonu Tutar'], y=[total_bank], marker_color='#95a5a6', text=[f"{total_bank:,.0f} TL"]),
                    go.Bar(name='Robo', x=['Vade Sonu Tutar'], y=[total_robo], marker_color='#27ae60', text=[f"{total_robo:,.0f} TL"])
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
                    st.write("**Sepet İçeriği**")
                    final_data = []
                    for asset, w in portfolio:
                        if w < 0.01: continue
                        final_data.append({"Varlık": asset, "Oran": f"%{w*100:.1f}", "Tutar": f"{money*w:,.2f} TL"})
                    st.dataframe(pd.DataFrame(final_data), hide_index=True)

        except Exception as e:
            st.error(f"Hata: {e}")