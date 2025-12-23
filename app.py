import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# ⚙️ AYARLAR VE VERİTABANI
# ==========================================
st.set_page_config(page_title="Robo-Advisor Pro V7", page_icon="🦅", layout="wide")

# Güncel Piyasa Oranları (Temsili - Ortalama)
BANK_RATES = {
    "Faiz": {"name": "Mevduat Faizi (Ort.)", "rate": 0.48}, # %48 Yıllık
    "Katilim": {"name": "Katılım Kâr Payı (Ort.)", "rate": 0.42} # %42 Yıllık Tahmini
}

ASSET_DATABASE = [
    {"symbol": "TRY=X", "name": "DOLAR (USD)", "cat": "Döviz", "halal": True},
    {"symbol": "EURTRY=X", "name": "EURO (EUR)", "cat": "Döviz", "halal": True},
    {"symbol": "GC=F", "name": "ALTIN (Ons)", "cat": "Emtia", "halal": True},
    {"symbol": "SI=F", "name": "GÜMÜŞ (Ons)", "cat": "Emtia", "halal": True},
    {"symbol": "THYAO.IS", "name": "THY", "cat": "Borsa", "halal": True},
    {"symbol": "BIMAS.IS", "name": "BIM", "cat": "Borsa", "halal": True},
    {"symbol": "ASELS.IS", "name": "ASELSAN", "cat": "Borsa", "halal": True},
    {"symbol": "AKBNK.IS", "name": "AKBANK", "cat": "Borsa", "halal": False},
    {"symbol": "GARAN.IS", "name": "GARANTI", "cat": "Borsa", "halal": False},
    {"symbol": "BTC-USD", "name": "BITCOIN", "cat": "Kripto", "halal": True},
    {"symbol": "ETH-USD", "name": "ETHEREUM", "cat": "Kripto", "halal": True},
    {"symbol": "SOL-USD", "name": "SOLANA", "cat": "Kripto", "halal": True}
]

# ==========================================
# 🎨 YAN MENÜ (GİRDİLER)
# ==========================================
with st.sidebar:
    st.header("🦅 Finansal Kokpit")
    
    # 1. Temel Bilgiler
    money = st.number_input("Yatırım Tutarı (TL)", min_value=1000, value=100000, step=1000, format="%d")
    
    # 2. Vade Seçimi
    duration_options = {"1 Ay": 1, "3 Ay": 3, "6 Ay": 6, "1 Yıl": 12}
    selected_duration_label = st.selectbox("Vade Seçimi", list(duration_options.keys()), index=3)
    months = duration_options[selected_duration_label]
    
    st.divider()
    
    # 3. Hassasiyet Ayarı
    is_halal = st.toggle("💚 İslami Hassasiyet (Katılım)", value=True)
    
    st.divider()
    
    # 4. Varlık Tercihleri
    st.subheader("Portföy Sepeti")
    use_forex = st.checkbox("Döviz", value=True)
    use_commodity = st.checkbox("Emtia (Altın/Gümüş)", value=True)
    use_stock = st.checkbox("Borsa İstanbul", value=True)
    use_crypto = st.checkbox("Kripto Paralar", value=True)
    
    btn_run = st.button("🚀 Hesapla ve Karşılaştır", type="primary")

# ==========================================
# 🧠 HESAPLAMA MOTORU
# ==========================================
if btn_run:
    st.title(f"📊 {selected_duration_label} Vadeli Yatırım Analizi")
    
    # --- BÖLÜM 1: BANKA/KATILIM GETİRİSİ (Benchmark) ---
    col_bank, col_robo = st.columns(2)
    
    with col_bank:
        st.subheader("🏦 Banka Seçeneği")
        
        if is_halal:
            rate_info = BANK_RATES["Katilim"]
            st.info(f"Mod: **Katılım Bankacılığı** (Kâr Payı)")
        else:
            rate_info = BANK_RATES["Faiz"]
            st.info(f"Mod: **Mevduat Faizi** (Standart)")
            
        annual_rate = rate_info["rate"]
        
        # Basit Faiz/Getiri Hesabı: Ana Para * Oran * (Ay / 12)
        gross_return = money * annual_rate * (months / 12)
        net_return_bank = gross_return * 0.95 # %5 Stopaj tahmini
        total_bank = money + net_return_bank
        
        st.metric(label=f"{rate_info['name']} Getirisi", 
                  value=f"{total_bank:,.2f} TL", 
                  delta=f"+{net_return_bank:,.2f} TL")
        
        st.progress(value=min(1.0, (annual_rate * (months/12))), text=f"Tahmini Dönemlik Oran: %{(annual_rate * (months/12) * 100):.1f}")

    # --- BÖLÜM 2: ROBO-ADVISOR SEPETİ ---
    
    # 1. Varlık Filtreleme
    active_cats = []
    if use_forex: active_cats.append("Döviz")
    if use_commodity: active_cats.append("Emtia")
    if use_stock: active_cats.append("Borsa")
    if use_crypto: active_cats.append("Kripto")
    
    candidates = [a for a in ASSET_DATABASE if a['cat'] in active_cats]
    if is_halal: candidates = [a for a in candidates if a['halal']]
    
    if len(candidates) < 2:
        st.error("Lütfen en az 2 varlık grubu seçin.")
        st.stop()
        
    with st.spinner('Yapay Zeka piyasayı analiz ediyor...'):
        # 2. Veri Çekme
        tickers_map = {a['symbol']: a['name'] for a in candidates}
        try:
            df = yf.download(list(tickers_map.keys()), start="2024-01-01", progress=False)['Close']
            df.rename(columns=tickers_map, inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            df.ffill(inplace=True); df.bfill(inplace=True)
            
            # 3. Markowitz Optimizasyonu
            returns = np.log(df / df.shift(1))
            mean_ret_daily = returns.mean()
            cov_matrix = returns.cov()
            
            # Dönemselleştirme
            trading_days = int(252 * (months / 12))
            
            mean_ret_period = mean_ret_daily * trading_days
            cov_period = cov_matrix * trading_days
            
            # Simülasyon
            num_ports = 3000
            best_sharpe = -1
            best_weights = []
            
            for _ in range(num_ports):
                w = np.random.random(len(df.columns))
                w /= w.sum()
                ret = np.sum(mean_ret_period * w)
                vol = np.sqrt(np.dot(w.T, np.dot(cov_period, w)))
                if vol == 0: continue
                sharpe = ret / vol
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_weights = w
            
            # 4. Robo Sonuçları
            robo_return_pct = np.sum(mean_ret_period * best_weights)
            robo_risk_pct = np.sqrt(np.dot(best_weights.T, np.dot(cov_period, best_weights)))
            
            net_return_robo = money * robo_return_pct
            total_robo = money + net_return_robo
            
            with col_robo:
                st.subheader("🦅 Robo-Advisor Sepeti")
                st.metric(label="Optimize Sepet Getirisi (Beklenen)", 
                          value=f"{total_robo:,.2f} TL", 
                          delta=f"+{net_return_robo:,.2f} TL",
                          delta_color="normal")
                
                risk_label = "Düşük" if robo_risk_pct < 0.05 else "Orta" if robo_risk_pct < 0.15 else "Yüksek"
                st.caption(f"Risk Seviyesi: **{risk_label}** (Volatilite: %{robo_risk_pct*100:.1f})")

            # --- BÖLÜM 3: DETAYLI RAPOR VE GRAFİKLER ---
            st.markdown("---")
            
            # Kıyaslama Grafiği
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=["Banka / Katılım", "Akıllı Sepet"],
                y=[net_return_bank, net_return_robo],
                marker_color=['#95a5a6', '#27ae60'],
                text=[f"{net_return_bank:,.0f} TL", f"{net_return_robo:,.0f} TL"],
                textposition='auto'
            ))
            fig_comp.update_layout(title="Kazanç Karşılaştırması", yaxis_title="Tahmini Net Getiri (TL)")
            
            # Pasta Grafiği
            portfolio = sorted(zip(df.columns, best_weights), key=lambda x:x[1], reverse=True)
            labels = [p[0] for p in portfolio if p[1] > 0.01]
            values = [p[1] for p in portfolio if p[1] > 0.01]
            
            fig_pie = px.pie(values=values, names=labels, title="Önerilen Varlık Dağılımı", hole=0.4)
            
            # Ekrana Bas
            c1, c2 = st.columns([1, 1])
            with c1:
                st.plotly_chart(fig_comp, use_container_width=True)
            with c2:
                st.plotly_chart(fig_pie, use_container_width=True)
                
            # Tablo
            st.subheader("📝 Varlık Dağılım Detayı")
            final_data = []
            for asset, w in portfolio:
                if w < 0.01: continue
                amt = money * w
                final_data.append({"Varlık": asset, "Oran": f"%{w*100:.1f}", "Tutar": f"{amt:,.2f} TL"})
            
            st.dataframe(pd.DataFrame(final_data), use_container_width=True)

            st.warning(f"⚠️ **Yasal Uyarı:** Yukarıdaki veriler geçmiş piyasa hareketlerine ve ortalama banka oranlarına ({annual_rate*100}%) dayanmaktadır. Gelecek getiriyi garanti etmez.")
        
        except Exception as e:
            st.error(f"Hata oluştu: {e}. Lütfen sayfayı yenileyip tekrar deneyin.")