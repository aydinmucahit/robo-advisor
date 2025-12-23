import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# ==========================================
# ⚙️ AYARLAR VE VERİTABANI
# ==========================================
st.set_page_config(page_title="Robo-Advisor AI", page_icon="🦅", layout="wide")

ASSET_DATABASE = [
    {"symbol": "TRY=X", "name": "DOLAR (USD)", "cat": "Döviz", "halal": True},
    {"symbol": "EURTRY=X", "name": "EURO (EUR)", "cat": "Döviz", "halal": True},
    {"symbol": "GC=F", "name": "ALTIN (Ons)", "cat": "Emtia", "halal": True},
    {"symbol": "SI=F", "name": "GÜMÜŞ (Ons)", "cat": "Emtia", "halal": True},
    {"symbol": "CL=F", "name": "PETROL", "cat": "Emtia", "halal": True},
    {"symbol": "THYAO.IS", "name": "THY", "cat": "Borsa", "halal": True},
    {"symbol": "BIMAS.IS", "name": "BIM", "cat": "Borsa", "halal": True},
    {"symbol": "ASELS.IS", "name": "ASELSAN", "cat": "Borsa", "halal": True},
    {"symbol": "TUPRS.IS", "name": "TUPRAS", "cat": "Borsa", "halal": True},
    {"symbol": "FROTO.IS", "name": "FORD OTO", "cat": "Borsa", "halal": True},
    {"symbol": "EREGL.IS", "name": "EREGLI", "cat": "Borsa", "halal": True},
    {"symbol": "AKBNK.IS", "name": "AKBANK", "cat": "Borsa", "halal": False},
    {"symbol": "GARAN.IS", "name": "GARANTI", "cat": "Borsa", "halal": False},
    {"symbol": "AEFES.IS", "name": "ANADOLU EFES", "cat": "Borsa", "halal": False},
    {"symbol": "BTC-USD", "name": "BITCOIN", "cat": "Kripto", "halal": True},
    {"symbol": "ETH-USD", "name": "ETHEREUM", "cat": "Kripto", "halal": True},
    {"symbol": "SOL-USD", "name": "SOLANA", "cat": "Kripto", "halal": True},
    {"symbol": "AVAX-USD", "name": "AVALANCHE", "cat": "Kripto", "halal": True},
    {"symbol": "DOGE-USD", "name": "DOGECOIN", "cat": "Kripto", "halal": False},
]

# ==========================================
# 🎨 ARAYÜZ TASARIMI
# ==========================================
st.title("🦅 Yapay Zeka Finansal Danışman")
st.markdown("**Akademik hassasiyetle geliştirilmiş, kişiselleştirilmiş varlık yönetim sistemi.**")

# --- SOL MENÜ (Sidebar) ---
with st.sidebar:
    st.header("⚙️ Portföy Ayarları")
    money = st.number_input("Yatırım Tutarı (TL)", min_value=1000, value=100000, step=1000)
    
    st.subheader("Pazar Seçimi")
    use_forex = st.checkbox("Döviz (Koruma)", value=True)
    use_commodity = st.checkbox("Emtia (Güvenli Liman)", value=True)
    use_stock = st.checkbox("Borsa İstanbul (Büyüme)", value=True)
    use_crypto = st.checkbox("Kripto Paralar (Risk/Getiri)", value=True)
    
    st.markdown("---")
    is_halal = st.toggle("💚 İslami Hassasiyet (Helal Filtre)", value=True)
    if is_halal:
        st.success("Faiz ve şüpheli varlıklar eleniyor.")
    
    btn_run = st.button("🚀 Analizi Başlat", type="primary")

# ==========================================
# 🧠 ARKA PLAN MOTORU
# ==========================================
if btn_run:
    # 1. Filtreleme
    active_cats = []
    if use_forex: active_cats.append("Döviz")
    if use_commodity: active_cats.append("Emtia")
    if use_stock: active_cats.append("Borsa")
    if use_crypto: active_cats.append("Kripto")
    
    candidates = []
    for asset in ASSET_DATABASE:
        if asset['cat'] in active_cats:
            if is_halal and not asset['halal']: continue
            candidates.append(asset)
            
    if len(candidates) < 2:
        st.error("❌ Analiz için en az 2 farklı varlık türü veya varlık seçmelisiniz.")
    else:
        with st.spinner('Piyasa verileri çekiliyor ve Monte Carlo simülasyonu yapılıyor...'):
            # 2. Veri Çekme
            tickers_map = {a['symbol']: a['name'] for a in candidates}
            try:
                df = yf.download(list(tickers_map.keys()), start="2024-01-01", progress=False)['Close']
                
                # Sütun isimlerini düzelt (Sembol -> İsim)
                df.rename(columns=tickers_map, inplace=True)
                
                # Temizlik
                df.dropna(axis=1, how='all', inplace=True) # Boş sütunları at
                df.ffill(inplace=True)
                df.bfill(inplace=True)
                
                if df.empty:
                    st.error("Veri çekilemedi. Lütfen daha sonra tekrar deneyin.")
                    st.stop()

                # 3. Markowitz Optimizasyonu
                returns = np.log(df / df.shift(1))
                mean_ret = returns.mean() * 252
                cov = returns.cov() * 252
                
                num_ports = 3000
                best_sharpe = -1
                best_weights = []
                
                # Hızlı Simülasyon
                for _ in range(num_ports):
                    w = np.random.random(len(df.columns))
                    w /= w.sum()
                    ret = np.sum(mean_ret * w)
                    vol = np.sqrt(np.dot(w.T, np.dot(cov, w)))
                    if vol == 0: continue
                    sharpe = ret / vol
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_weights = w
                
                # 4. Sonuçları Hazırla
                portfolio = sorted(zip(df.columns, best_weights), key=lambda x:x[1], reverse=True)
                
                # --- SONUÇ EKRANI ---
                st.success("✅ Optimizasyon Tamamlandı!")
                
                # Metrikler
                col1, col2, col3 = st.columns(3)
                exp_ret = np.sum(mean_ret * best_weights) * 100
                exp_risk = np.sqrt(np.dot(best_weights.T, np.dot(cov, best_weights))) * 100
                
                col1.metric("Beklenen Yıllık Getiri", f"%{exp_ret:.2f}")
                col2.metric("Tahmini Risk", f"%{exp_risk:.2f}")
                col3.metric("Sharpe Oranı", f"{best_sharpe:.2f}")
                
                st.markdown("### 🏆 Sizin İçin Önerilen Dağılım")
                
                # Pasta Grafiği İçin Veri Hazırla
                labels = []
                values = []
                
                final_list = []
                for asset, weight in portfolio:
                    if weight < 0.01: continue # %1 altını gizle
                    amt = money * weight
                    labels.append(asset)
                    values.append(amt)
                    final_list.append({"Varlık": asset, "Oran (%)": f"%{weight*100:.1f}", "Tutar (TL)": f"{amt:,.2f}"})
                
                # Tablo ve Grafik Yan Yana
                c1, c2 = st.columns([1, 2])
                
                with c1:
                    st.dataframe(pd.DataFrame(final_list), hide_index=True)
                    
                with c2:
                    fig = px.pie(values=values, names=labels, title="Portföy Dağılımı", hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.info("💡 **Not:** Bu dağılım, geçmiş piyasa verileri ve risk profilinize göre matematiksel olarak hesaplanmıştır.")

            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")