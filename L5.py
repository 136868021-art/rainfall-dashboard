import pandas as pd
import streamlit as st
import plotly.express as px

# ตั้งค่าหน้าเว็บ Streamlit ให้แสดงผลแบบเต็มจอ (Wide mode)
st.set_page_config(page_title="Rainfall Multi-Province Dashboard", layout="wide")

st.title("🌧️ ระบบ Dashboard วิเคราะห์ปริมาณน้ำฝนรายจังหวัด")
st.markdown("---")

# ==========================================
# ส่วนที่เพิ่มเข้ามาใหม่: ช่องอัปโหลดไฟล์บนหน้าเว็บ
# ==========================================
st.sidebar.header("📁 นำเข้าข้อมูล")
uploaded_file = st.sidebar.file_uploader(
    "อัปโหลดไฟล์ข้อมูลน้ำฝน (.csv)",
    type=["csv"],
    help="รองรับไฟล์ CSV ที่มีคอลัมน์: จังหวัด, ปี, เดือน, อำเภอ, จำนวน"
)


# ฟังก์ชันโหลดและเคลียร์ข้อมูลจากไฟล์ที่อัปโหลด
def process_data(file):
    # ใส่ encoding='cp874' เพื่อรองรับภาษาไทยจาก Excel CSV
    df = pd.read_csv(file, encoding='cp874')

    # ลบแถวที่ไม่มีข้อมูลในคอลัมน์สำคัญ
    df = df.dropna(subset=['ปี', 'เดือน', 'จำนวน'])
    df['จำนวน'] = pd.to_numeric(df['จำนวน'], errors='coerce')
    df = df.dropna(subset=['จำนวน'])

    # เรียงลำดับเดือนให้ถูกต้อง
    month_map = {
        'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4,
        'พฤษภาคม': 5, 'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8,
        'กันยายน': 9, 'ตุลาคม': 10, 'พฤศจิกายน': 11, 'ธันวาคม': 12
    }
    df['Month_Num'] = df['เดือน'].map(month_map)
    return df


# ตรวจสอบว่ามีการอัปโหลดไฟล์เข้ามาหรือไม่
if uploaded_file is not None:
    try:
        # ประมวลผลไฟล์ที่ผู้ใช้อัปโหลดเข้ามาสดๆ
        df = process_data(uploaded_file)

        # ดึงชื่อจังหวัดจากในไฟล์มาแสดงพาดหัวอัตโนมัติ
        province_name = df['จังหวัด'].iloc[0] if 'จังหวัด' in df.columns else "ระบุจังหวัดไม่ได้"
        st.header(f"📊 ข้อมูลสรุปปริมาณน้ำฝน: จังหวัด{province_name}")

        # ==========================================
        # ตัวกรองข้อมูล: ปุ่มเลือกอำเภอ (Selectbox)
        # ==========================================
        st.subheader("🔍 ตัวกรองข้อมูล")
        district_list = ["ทั้งหมด"] + sorted(df['อำเภอ'].unique().tolist())
        selected_district = st.selectbox("เลือกอำเภอที่ต้องการดูข้อมูล:", district_list)

        # กรองข้อมูลตามอำเภอที่เลือก
        if selected_district == "ทั้งหมด":
            filtered_df = df
            title_suffix = "ทุกอำเภอรวมกัน"
        else:
            filtered_df = df[df['อำเภอ'] == selected_district]
            title_suffix = f"อำเภอ {selected_district}"

        st.markdown("---")

        # ---- คำนวณข้อมูลสถิติ ----
        yearly_rain = filtered_df.groupby('ปี')['จำนวน'].sum().reset_index()
        avg_yearly = yearly_rain['จำนวน'].mean() if not yearly_rain.empty else 0
        max_yearly = yearly_rain['จำนวน'].max() if not yearly_rain.empty else 0

        district_rain = df.groupby('อำเภอ')['จำนวน'].mean().reset_index().sort_values(by='จำนวน', ascending=False)
        top_district = district_rain.iloc[0]['อำเภอ'] if not district_rain.empty else "-"

        monthly_rain = filtered_df.groupby(['Month_Num', 'เดือน'])['จำนวน'].mean().reset_index().sort_values(
            by='Month_Num')

        # ---- ส่วนที่ 1: KPI Cards ----
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label=f"🌧️ ปริมาณน้ำฝนเฉลี่ยต่อปี ({selected_district})", value=f"{avg_yearly:,.1f} มม.")
        with col2:
            st.metric(label=f"🚀 ปริมาณน้ำฝนรวมสูงสุดรายปี ({selected_district})", value=f"{max_yearly:,.1f} มม.")
        with col3:
            st.metric(label="📍 พื้นที่ที่มีฝนตกชุกที่สุด (ภาพรวมจังหวัด)", value=top_district)

        st.markdown("---")

        # ---- ส่วนที่ 2: กราฟและตาราง ----
        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader(f"📅 แนวโน้มรายเดือน: {title_suffix}")
            if not monthly_rain.empty:
                fig_line = px.line(monthly_rain, x='เดือน', y='จำนวน',
                                   labels={'จำนวน': 'ปริมาณน้ำฝนเฉลี่ย (มม.)', 'เดือน': 'เดือน'},
                                   markers=True)
                st.plotly_chart(fig_line, use_container_width=True)
                st.dataframe(monthly_rain[['เดือน', 'จำนวน']].rename(columns={'จำนวน': 'ปริมาณน้ำฝนเฉลี่ย (มม.)'}),
                             hide_index=True)
            else:
                st.info("ไม่มีข้อมูลรายเดือนสำหรับตัวเลือกนี้")

        with right_col:
            st.subheader("📊 การเปรียบเทียบปริมาณน้ำฝนเฉลี่ยรายอำเภอ (ภาพรวม)")
            if not district_rain.empty:
                fig_bar = px.bar(district_rain, x='อำเภอ', y='จำนวน',
                                 labels={'จำนวน': 'ปริมาณน้ำฝนเฉลี่ย (มม.)', 'อำเภอ': 'อำเภอ'},
                                 color='จำนวน', color_continuous_scale='Blues')
                st.plotly_chart(fig_bar, use_container_width=True)
                st.dataframe(district_rain.rename(columns={'จำนวน': 'ปริมาณน้ำฝนเฉลี่ย (มม.)'}), hide_index=True)
            else:
                st.info("ไม่มีข้อมูลรายอำเภอ")

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")
        st.info("โปรดตรวจสอบว่าไฟล์ CSV ของคุณใช้โครงสร้างและชื่อคอลัมน์ที่ถูกต้อง (ปี, เดือน, อำเภอ, จำนวน)")

else:
    # ข้อความแสดงเมื่อหน้าเว็บเปิดขึ้นมาครั้งแรก และยังไม่มีการอัปโหลดไฟล์
    st.info("👈 ยินดีต้อนรับ! กรุณาอัปโหลดไฟล์ข้อมูลน้ำฝน (.csv) ที่แถบเมนูด้านซ้ายเพื่อเริ่มใช้งานระบบ Dashboard")

    # แนะนำหน้าตาไฟล์ตัวอย่างให้ผู้ใช้ทราบ
    st.markdown("""
    ### 📋 รูปแบบไฟล์ที่ระบบรองรับ (ตัวอย่างโครงสร้างคอลัมน์):
    | จังหวัด | ปี | เดือน | อำเภอ | จำนวน | หน่วย |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | นราธิวาส | 2568 | มกราคม | เมืองนราธิวาส | 415.0 | มิลลิเมตร |
    | เชียงใหม่ | 2568 | สิงหาคม | แม่ริม | 180.5 | มิลลิเมตร |
    """)