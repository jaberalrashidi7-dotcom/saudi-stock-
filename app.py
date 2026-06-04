import streamlit as st
import yfinance as yf
import pandas as pd
import math
import plotly.graph_objects as go # أضفنا هذه المكتبة للرسوم التفاعلية القادمة

# 1. إعدادات الصفحة
st.set_page_config(page_title="منصة التحليل المالي", layout="wide")

# تنسيق التصميم (CSS) للنمط الصلصالي والألوان المخصصة
st.markdown("""
<style>
    .stApp { background-color: #FDFBF7; }
    h1, h2, h3, p, span, label { color: #5C4033 !important; }
    h1 { text-shadow: 2px 2px 4px rgba(184, 115, 51, 0.3); }
    div[data-testid="stMetric"] {
        background-color: #FDFBF7;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 8px 8px 16px #e3e1dd, -8px -8px 16px #ffffff, inset 2px 2px 5px rgba(184, 115, 51, 0.05);
        border: 1px solid rgba(142, 68, 173, 0.1);
    }
    div.stButton > button {
        background-color: #FDFBF7;
        color: #8E44AD !important; 
        border-radius: 12px;
        border: 2px solid #B87333; 
        box-shadow: 4px 4px 10px #e3e1dd, -4px -4px 10px #ffffff;
        transition: all 0.3s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #8E44AD; 
        color: #FDFBF7 !important; 
        border-color: #5C4033; 
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 منصة التحليل المالي للأسهم السعودية")

# 2. إدخال رمز السهم
st.sidebar.header("إعدادات البحث")
symbol = st.sidebar.text_input("أدخل رمز السهم (مثال: 2222 لأرامكو):", "2222")

if symbol:
    saudi_symbol = f"{symbol}.SR"
    
    with st.spinner('جاري جلب البيانات...'):
        stock = yf.Ticker(saudi_symbol)
        data = stock.history(period="1y")

        if not data.empty:
            info = stock.info
            
            # --- بداية تقسيم التبويبات ---
            tab1, tab2, tab3 = st.tabs(["معلومات الأسهم", "نماذج التقييم", "الحاسبة"])
            
            # التبويب الأول: معلومات الأسهم
            with tab1:
                st.subheader(f"البيانات التاريخية لسهم ({symbol})")
                
                data['SMA_50'] = data['Close'].rolling(window=50).mean()
                data['SMA_200'] = data['Close'].rolling(window=200).mean()
                
                st.line_chart(data[['Close', 'SMA_50', 'SMA_200']])
                
                st.write("### معلومات السهم الأساسية")
                col1, col2, col3 = st.columns(3)
                col1.metric("السعر الحالي", f"{info.get('currentPrice', 'N/A')} ريال")
                col2.metric("مكرر الربحية (PE)", info.get('trailingPE', 'N/A'))
                col3.metric("ربحية السهم (EPS)", info.get('trailingEps', 'N/A'))

            # التبويب الثاني: نماذج التقييم
            with tab2:
                st.write("### 📈 تقييم السعر العادل (نموذج بيتر لينش)")
                eps = info.get('trailingEps')
                growth_rate_decimal = info.get('earningsGrowth', 0)
                if growth_rate_decimal is None: growth_rate_decimal = 0
                growth_rate = growth_rate_decimal * 100 
                
                dividend_yield_decimal = info.get('dividendYield', 0)
                if dividend_yield_decimal is None: dividend_yield_decimal = 0
                dividend_yield = dividend_yield_decimal * 100 
                
                if eps and eps > 0 and (growth_rate > 0 or dividend_yield > 0):
                    fair_value_lynch = eps * (growth_rate + dividend_yield)
                    col4, col5, col6 = st.columns(3)
                    col4.metric("ربحية السهم (EPS)", f"{eps} ريال")
                    col5.metric("معدل النمو المتوقع", f"{growth_rate:.2f}%")
                    col6.metric("عائد التوزيعات", f"{dividend_yield:.2f}%")
                    st.success(f"**السعر العادل التقديري:** {fair_value_lynch:.2f} ريال")
                else:
                    st.warning("لا تتوفر بيانات كافية لحساب السعر العادل وفق نموذج بيتر لينش.")

                st.divider()
                st.write("### 📜 تقييم السعر العادل (رقم بنجامين جراهام)")
                bvps = info.get('bookValue')
                if eps and bvps and eps > 0 and bvps > 0:
                    fair_value_graham = math.sqrt(22.5 * eps * bvps)
                    col7, col8 = st.columns(2)
                    col7.metric("ربحية السهم (EPS)", f"{eps} ريال")
                    col8.metric("القيمة الدفترية للسهم (BVPS)", f"{bvps} ريال")
                    st.success(f"**السعر العادل التقديري (رقم جراهام):** {fair_value_graham:.2f} ريال")
                else:
                    st.warning("لا تتوفر بيانات كافية لحساب رقم جراهام لهذا السهم.")

                st.divider()
                st.write("### 💸 تقييم السعر العادل (نموذج التدفقات النقدية المخصومة - DCF)")
                col_dcf1, col_dcf2 = st.columns(2)
                discount_rate = col_dcf1.number_input("معدل الخصم المستهدف (%)", value=10.0, step=0.5) / 100
                growth_rate_dcf = col_dcf2.number_input("معدل نمو التدفقات (5 سنوات) (%)", value=5.0, step=0.5) / 100
                
                try:
                    cashflow = stock.cashflow
                    operating_cf = cashflow.loc['Operating Cash Flow'].iloc[0]
                    cap_ex = cashflow.loc['Capital Expenditure'].iloc[0]
                    fcf = operating_cf + cap_ex
                except:
                    fcf = None
                
                shares = info.get('sharesOutstanding')
                
                if fcf and shares and fcf > 0:
                    total_pv = 0
                    temp_fcf = fcf
                    for year in range(1, 6):
                        temp_fcf = temp_fcf * (1 + growth_rate_dcf)
                        pv = temp_fcf / ((1 + discount_rate) ** year)
                        total_pv += pv
                    fair_value_dcf = total_pv / shares
                    st.metric("التدفق النقدي الحر الأخير للشركة", f"{fcf:,.0f} ريال")
                    st.success(f"**السعر العادل التقديري بناءً على التدفقات المستقبليّة:** {fair_value_dcf:.2f} ريال")
                else:
                    st.warning("لم نتمكن من جلب بيانات التدفق النقدي الحر بشكل تلقائي لتطبيق نموذج DCF.")

            # التبويب الثالث: الحاسبة
            with tab3:
                st.write("### 🧮 حاسبة التكلفة الذكية (التعديل العكسي للمحفظة)")
                col_calc1, col_calc2 = st.columns(2)
                
                current_shares = col_calc1.number_input("عدد الأسهم المملوكة حالياً", min_value=0, value=100, step=10)
                current_avg_price = col_calc1.number_input("متوسط سعر الشراء الحالي (ريال)", min_value=0.0, value=50.0, step=0.5)
                
                current_market_price = info.get('currentPrice', current_avg_price * 0.9)
                if current_market_price is None: current_market_price = 45.0
                
                new_price = col_calc2.number_input("سعر الشراء الجديد المتوقع", min_value=0.0, value=float(current_market_price), step=0.5)
                target_avg_price = col_calc2.number_input("متوسط السعر المستهدف (ريال)", min_value=0.0, value=45.0, step=0.5)
                
                if st.button("احسب الكمية المطلوبة"):
                    denominator = target_avg_price - new_price
                    numerator = current_shares * (current_avg_price - target_avg_price)
                    
                    if denominator == 0:
                        st.error("عذراً، السعر المستهدف لا يمكن أن يساوي سعر الشراء الجديد.")
                    else:
                        required_shares = numerator / denominator
                        if required_shares > 0:
                            total_cost = required_shares * new_price
                            st.success(f"🎯 **النتيجة:** يجب عليك شراء **{int(required_shares)}** سهم إضافي على سعر {new_price} ريال.")
                        else:
                            st.warning("⚠️ الحسابات غير منطقية. تأكد من أن السعر المستهدف يقع بين السعر الحالي وسعر الشراء الجديد.")
        else:
            st.error("لم يتم العثور على بيانات لهذا السهم. تأكد من صحة الرمز.")
