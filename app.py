import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import feedparser
from textblob import TextBlob

# ==========================================
# ⚙️ 1. AYARLAR
# ==========================================
st.set_page_config(page_title="Finans Asistanı", page_icon="🏦", layout="wide")

# ==========================================
# 🧹 2. NÜKLEER TEMİZLİK (CSS & JS)
# ==========================================
hide_streamlit_style = """
<style>
    header {visibility: hidden !important; height: 0px !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .stDeployButton {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stFooter"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
</style>
<script>
    const observer = new MutationObserver(() => {
        const header = document.querySelector('header');
        if (header) header.style.display = 'none';
        const footer = document.querySelector('footer');
        if (footer) footer.style.display = 'none';
        const toolbar = document.querySelector('[data-testid="stToolbar"]');
        if (toolbar) toolbar.style.display = 'none';
    });
    observer.observe(document.body, { childList: true, subtree: true });
</script>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==========================================
# 🏦 3. VARLIK HAVUZLARI
# ==========================================

# A. SABİT VARLIKLAR
BASE_ASSETS = [
    {"symbol": "TRY=X", "name": "DOLAR (USD)", "cat": "Döviz", "halal": True, "search_term": "USDTRY currency"},
    {"symbol": "EURTRY=X", "name": "EURO (EUR)", "cat": "Döviz", "halal": True, "search_term": "EURTRY currency"},
    {"symbol": "GC=F", "name": "ALTIN (Ons)", "cat": "Emtia", "halal": True, "search_term": "Gold price forecast"},
    {"symbol": "SI=F", "name": "GÜMÜŞ (Ons)", "cat": "Emtia", "halal": True, "search_term": "Silver price forecast"}
]

# B. BIST HAVUZU
BIST_POOL = [
    {"symbol": "THYAO.IS", "name": "THY", "cat": "Borsa", "halal": True},
    {"symbol": "BIMAS.IS", "name": "BIM", "cat": "Borsa", "halal": True},
    {"symbol": "ASELS.IS", "name": "ASELSAN", "cat": "Borsa", "halal": True},
    {"symbol": "TUPRS.IS", "name": "TUPRAS", "cat": "Borsa", "halal": True},
    {"symbol": "EREGL.IS", "name": "EREGLI", "cat": "Borsa", "halal": True},
    {"symbol": "FROTO.IS", "name": "FORD OTO", "cat": "Borsa", "halal": True},
    {"symbol": "SASA.IS", "name": "SASA", "cat": "Borsa", "halal": True},
    {"symbol": "HEKTS.IS", "name": "HEKTAS", "cat": "Borsa", "halal": True},
    {"symbol": "ENKAI.IS", "name": "ENKA", "cat": "Borsa", "halal": True},
    {"symbol": "ALARK.IS", "name": "ALARKO", "cat": "Borsa", "halal": True},
    {"symbol": "KCHOL.IS", "name": "KOC HOLDING", "cat": "Borsa", "halal": True},
    {"symbol": "AKBNK.IS", "name": "AKBANK", "cat": "Borsa", "halal": False},
    {"symbol": "GARAN.IS", "name": "GARANTI", "cat": "Borsa", "halal": False},
    {"symbol": "ISCTR.IS", "name": "IS BANKASI", "cat": "Borsa", "halal": False},
    {"symbol": "YKBNK.IS", "name": "YAPI KREDI", "cat": "Borsa", "halal": False},
    {"symbol": "SAHOL.IS", "name": "SABANCI HOL.", "cat": "Borsa", "halal": False},
    {"symbol": "AEFES.IS", "name": "ANADOLU EFES", "cat": "Borsa", "halal": False}
]

# C. KRİPTO HAVUZU
CRYPTO_POOL = [
    {"symbol": "BTC-USD", "name": "BITCOIN", "cat": "Kripto", "halal": True},
    {"symbol": "ETH-USD", "name": "ETHEREUM", "cat": "Kripto", "halal": True},
    {"symbol": "BNB-USD", "name": "BNB", "cat": "Kripto", "halal": True},
    {"symbol": "SOL-USD", "name": "SOLANA", "cat": "Kripto", "halal": True},
    {"symbol": "XRP-USD", "name": "RIPPLE", "cat": "Kripto", "halal": True},
    {"symbol": "ADA-USD", "name": "CARDANO", "cat": "Kripto", "halal": True},
    {"symbol": "AVAX-USD", "name": "AVALANCHE", "cat": "Kripto", "halal": True},
    {"symbol": "DOGE-USD", "name": "DOGE", "cat": "Kripto", "halal": False},
    {"symbol": "DOT-USD", "name": "POLKADOT", "cat": "Kripto", "halal": True},
    {"symbol": "LINK-USD", "name": "CHAINLINK", "cat": "Kripto", "halal": True},
    {"symbol": "MATIC-USD", "name": "POLYGON", "cat": "Kripto", "halal": True}
]

# ==========================================
# 🛠️ 4. YARDIMCI FONKSİYONLAR
# ==========================================
def format_tl(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
# 📱 5. ANA EKRAN & ARAYÜZ
# ==========================================
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🏦 Finans Asistanı</h1>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-size: 0.9em; color: #555;'>
    <strong>Mücahit Aydın</strong> tarafından yapay zeka destekli hazırlanmıştır.<br>
    ⚠️ <em>Burada yer alan bilgiler kesinlikle yatırım tavsiyesi değildir, bilgilendirme ve simülasyon amaçlıdır.</em>
</div>
""", unsafe_allow_html=True)

st.divider()

with st.container():
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("1. Parametreler")
        money = st.number_input("💰 Yatırım Tutarı (TL)", min_value=1000, value=100000, step=1000)
        st.info(f"Girilen Tutar: **{format_tl(money)} TL**") 
        
        duration_options = {"1 Ay": 1, "3 Ay": 3, "6 Ay": 6, "1 Yıl": 12}
        selected_duration_label = st.selectbox("⏳ Vade Seçimi", list(duration_options.keys()), index=3)
        months = duration_options[selected_duration_label]
        
        st.markdown("---")
        is_halal = st.toggle("İslami Hassasiyet (Katılım Modu)", value=True)
        
        st.write("👇 Banka Oranı (Manuel Giriş)")
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
        with c_stk: use_stock = st.checkbox("Borsa (Oto-Seçim)", value=True)
        with c_cry: use_crypto = st.checkbox("Kripto (Oto-Seçim)", value=True)
        
        st.markdown("---")
        use_sentiment = st.checkbox("📰 **Haber Analizini Dahil Et**", value=True)
        
        btn_run = st.button("🚀 Geniş Tarama ve Analizi Başlat", type="primary", use_container_width=True)

st.divider()

# ==========================================
# 🧠 6. HESAPLAMA MOTORU
# ==========================================
if btn_run:
    # --- BANKA HESABI ---
    annual_rate = user_rate / 100.0
    gross_return = money * annual_rate * (months / 12)
    net_return_bank = gross_return * 0.95 
    total_bank = money + net_return_bank
    
    # --- VARLIK SEÇİMİ ---
    final_candidates = []
    
    # 1. Sabit Varlıklar
    for asset in BASE_ASSETS:
        if asset['cat'] == 'Döviz' and use_forex: final_candidates.append(asset)
        if asset['cat'] == 'Emtia' and use_commodity: final_candidates.append(asset)
    
    # --- TARAMA FONKSİYONU ---
    def pick_top_3(pool, is_stock=True):
        filtered_pool = [s for s in pool if (s['halal'] if is_halal else True)]
        tickers = {s['symbol']: s['name'] for s in filtered_pool}
        try:
            data = yf.download(list(tickers.keys()), period="6mo", progress=False)['Close']
            if "Koruyucu" in risk_choice:
                metric = data.pct_change().std()
                top_3 = metric.sort_values(ascending=True).head(3).index.tolist()
            else:
                metric = data.pct_change().mean()
                top_3 = metric.sort_values(ascending=False).head(3).index.tolist()
            selected_assets = []
            for sym in top_3:
                obj = next((item for item in filtered_pool if item["symbol"] == sym), None)
                if obj:
                    suffix = "stock news" if is_stock else "crypto news"
                    obj['search_term'] = f"{obj['name']} {suffix}"
                    selected_assets.append(obj)
            return selected_assets
        except: return []

    # 2. Borsa Taraması
    if use_stock:
        with st.status("🏢 Borsa İstanbul Taranıyor...", expanded=True) as status:
            picks = pick_top_3(BIST_POOL, is_stock=True)
            if picks:
                final_candidates.extend(picks)
                names = ", ".join([p['name'] for p in picks])
                st.write(f"✅ Seçilen Hisseler: **{names}**")
            status.update(label="✅ Borsa Taraması Bitti", state="complete", expanded=False)

    # 3. Kripto Taraması
    if use_crypto:
        with st.status("🪙 Kripto Piyasası Taranıyor...", expanded=True) as status:
            picks = pick_top_3(CRYPTO_POOL, is_stock=False)
            if picks:
                final_candidates.extend(picks)
                names = ", ".join([p['name'] for p in picks])
                st.write(f"✅ Seçilen Coinler: **{names}**")
            status.update(label="✅ Kripto Taraması Bitti", state="complete", expanded=False)

    if len(final_candidates) < 1:
        st.error("⚠️ Yeterli varlık bulunamadı. Lütfen seçimlerinizi kontrol edin.")
        st.stop()
        
    # --- HABER ANALİZİ ---
    sentiment_scores = {}
    if use_sentiment:
        with st.status("📰 Haberler Okunuyor...", expanded=True) as status:
            for cand in final_candidates:
                if 'search_term' in cand:
                    st.write(f"Analiz: {cand['search_term']}...")
                    score = analyze_news_sentiment(cand['search_term'])
                    sentiment_scores[cand['symbol']] = score
                else:
                    sentiment_scores[cand['symbol']] = 0
            status.update(label="✅ Duygu Analizi Tamamlandı!", state="complete", expanded=False)

    # --- MARKOWITZ OPTİMİZASYONU (DÜZELTİLMİŞ) ---
    with st.spinner('Portföy Optimize Ediliyor...'):
        try:
            tickers_map = {a['symbol']: a['name'] for a in final_candidates}
            
            # Veriyi indir
            raw_data = yf.download(list(tickers_map.keys()), period="1y", progress=False)
            
            # Veri yapısını kontrol et (MultiIndex mi yoksa tekil mi)
            if isinstance(raw_data, pd.DataFrame):
                if isinstance(raw_data.columns, pd.MultiIndex):
                    # Eğer 'Close' ana başlığı varsa onu al
                    if 'Close' in raw_data.columns.levels[0]:
                        df = raw_data['Close']
                    else:
                        df = raw_data
                elif 'Close' in raw_data.columns:
                    df = raw_data[['Close']] # Tek sütunlu DF olarak al
                else:
                    df = raw_data
            else:
                st.error("Veri formatı hatası.")
                st.stop()

            # --- Sütun İsimlerini Temizle ve Eşleştir ---
            # Yahoo bazen sembolü değiştirerek getirir (örn: 'GC=F' -> 'GC=F' olarak kalır mı?)
            # Elimizdeki tickers_map ile df.columns arasındaki kesişimi bulalım.
            valid_cols = [c for c in df.columns if c in tickers_map.keys()]
            
            if len(valid_cols) == 0:
                st.error("⚠️ Seçilen varlıklar için Yahoo Finance'den geçerli fiyat verisi alınamadı. Lütfen farklı varlıklar seçin veya Borsa/Kripto ekleyin.")
                st.stop()
                
            df = df[valid_cols]
            
            # Boş verileri temizle
            df.dropna(axis=0, how='any', inplace=True) # Satırda boşluk varsa o günü sil
            
            if df.empty:
                st.error("⚠️ Veri temizliği sonrası eldeki veri seti boş kaldı. Tarihsel veri yetersiz.")
                st.stop()

            # İsimleri güncelle (Sembol -> İsim)
            # Ama optimizasyon için sembolleri de tutmamız lazım.
            # df sütunları şu an sembol (örn: 'GC=F').
            
            returns = np.log(df / df.shift(1))
            returns.replace([np.inf, -np.inf], np.nan, inplace=True)
            returns.dropna(inplace=True)

            if returns.empty:
                 st.error("⚠️ Yeterli tarihsel veri olmadığı için optimizasyon yapılamadı.")
                 st.stop()

            trading_days = int(252 * (months / 12))
            mean_ret = returns.mean() * trading_days
            cov = returns.cov() * trading_days
            
            num_ports = 3000
            best_score = -float('inf')
            best_weights = []
            
            # Dinamik Kısıt
            if "Koruyucu" in risk_choice: max_w = 0.40 
            elif "Dengeli" in risk_choice: max_w = 0.60 
            else: max_w = 1.00 

            # Simülasyon
            for _ in range(num_ports):
                w = np.random.random(len(df.columns))
                w /= w.sum()
                
                if np.max(w) > max_w: continue 
                
                port_ret = np.sum(mean_ret * w)
                port_vol = np.sqrt(np.dot(w.T, np.dot(cov, w)))
                
                if "Koruyucu" in risk_choice: math_score = -port_vol 
                elif "Büyüme" in risk_choice: math_score = port_ret
                else: math_score = port_ret / port_vol if port_vol > 0 else 0
                
                # Haber Puanı Etkisi (DÜZELTİLMİŞ DÖNGÜ)
                sentiment_impact = 0
                if use_sentiment:
                    # df.columns içindeki sembol sırasına göre ağırlık (w) ile çarp
                    for idx, sym in enumerate(df.columns):
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
            
            # --- SONUÇ GÖRÜNTÜLEME ---
            c1, c2 = st.columns(2)
            c1.info(f"🏦 **{bank_label}**")
            c1.metric("Garanti Tutar", f"{format_tl(total_bank)} TL", f"+{format_tl(net_return_bank)} TL")
            
            delta_color = "normal" if net_return_robo > net_return_bank else "off"
            c2.success(f"🦅 **Akıllı Portföy ({risk_choice.split(' ')[1]})**")
            c2.metric("Tahmini Tutar", f"{format_tl(total_robo)} TL", f"+{format_tl(net_return_robo)} TL", delta_color=delta_color)
            
            st.markdown("---")
            
            # Haber Raporu
            if use_sentiment:
                with st.expander("📰 Piyasa Duygu Raporu", expanded=True):
                    st.caption("🟢: Olumlu (>0.05) | 🔴: Olumsuz (<-0.05) | ⚪: Nötr")
                    st.divider()
                    cols = st.columns(4) 
                    # Sadece df'de var olan ve analiz edilmiş sembolleri göster
                    relevant_assets = [s for s in sentiment_scores.keys() if s in df.columns]
                    
                    for i, sym in enumerate(relevant_assets):
                        col_idx = i % 4
                        score = sentiment_scores[sym]
                        name = tickers_map.get(sym, sym)
                        if score > 0.05: icon = "🟢"; color="green"
                        elif score < -0.05: icon = "🔴"; color="red"
                        else: icon = "⚪"; color="gray"
                        with cols[col_idx]:
                            st.markdown(f"**{name}**")
                            st.markdown(f":{color}[{icon}] ({score:.2f})")

            # Grafikler
            tab1, tab2 = st.tabs(["📈 Kârlılık", "🍰 Detaylı Kazanç Tablosu"])
            with tab1:
                fig_bar = go.Figure(data=[
                    go.Bar(name='Banka', x=['Tutar'], y=[total_bank], marker_color='#95a5a6', text=[f"{format_tl(total_bank)} TL"]),
                    go.Bar(name='Robo', x=['Tutar'], y=[total_robo], marker_color='#27ae60', text=[f"{format_tl(total_robo)} TL"])
                ])
                st.plotly_chart(fig_bar, use_container_width=True)
            with tab2:
                # df.columns sembolleri tutuyor, best_weights ağırlıkları
                # İsimleri göstermek için map kullanalım
                asset_names = [tickers_map.get(sym, sym) for sym in df.columns]
                
                portfolio = sorted(zip(asset_names, df.columns, best_weights), key=lambda x:x[2], reverse=True)
                
                labels = [p[0] for p in portfolio if p[2] > 0.01]
                values = [p[2] for p in portfolio if p[2] > 0.01]
                
                c_pie, c_list = st.columns([1, 1.5]) 
                c_pie.plotly_chart(px.pie(values=values, names=labels, hole=0.4), use_container_width=True)
                
                with c_list:
                    st.caption("🔥: Pozitif Haber | ❄️: Negatif Haber | ➖: Nötr")
                    final_data = []
                    for name, sym, w in portfolio:
                        if w < 0.01: continue
                        s_score = sentiment_scores.get(sym, 0)
                        
                        trend = "🔥" if s_score > 0.05 else "❄️" if s_score < -0.05 else "➖"
                        
                        yatirilan = money * w
                        portfoy_toplam_kar_orani = robo_ret_pct 
                        kazanc = yatirilan * portfoy_toplam_kar_orani
                        toplam = yatirilan + kazanc
                        
                        final_data.append({
                            "Varlık": f"{name} {trend}", 
                            "Oran": f"%{w*100:.1f}", 
                            "Yatırılan Para": f"{format_tl(yatirilan)} TL", 
                            "Tahmini Kâr": f"+{format_tl(kazanc)} TL",
                            "Vade Sonu": f"{format_tl(toplam)} TL"
                        })
                    st.dataframe(pd.DataFrame(final_data), hide_index=True)

        except Exception as e:
            st.error(f"Hata Oluştu: {e}")
            # Hata ayıklama için (gerekirse açın)
            # st.write(e)