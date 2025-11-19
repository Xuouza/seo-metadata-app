import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
import io
import os

# --- 1. ตัวแปรและฟังก์ชันจัดการ Metadata ---

# Tag ID ที่ใช้ใน EXIF (หลักๆ ที่ Pillow จัดการได้)
USER_COMMENT_ID = 37510 # ใช้สำหรับ Description/คำอธิบายภาพ (Alt Text)
IMAGE_DESCRIPTION_ID = 270 # ใช้สำหรับ Title/ชื่อภาพ

def create_seo_metadata_packet(title_input, description_input, keywords_list):
    """
    สร้างแพ็คเก็ตข้อมูล Metadata สำหรับ SEO โดยมีข้อจำกัดคีย์เวิร์ดสูงสุด 50 คำ
    """
    
    # การจัดการ Keywords (สูงสุด 50 คำ)
    validated_keywords = keywords_list[:50]
    
    # การจัดการ Title (ชื่อภาพ)
    title = title_input
    
    # การจัดการ Description (คำอธิบายภาพ/Alt Text)
    description = description_input
    
    return {
        "Title": title,
        "Description": description,  
        "Keywords": validated_keywords, 
    }

def update_image_metadata(image_file, metadata):
    """
    อัปเดต Metadata เข้าไปในไฟล์ภาพที่อัปโหลด (ในรูปแบบ Bytes)
    """
    try:
        # เปิดไฟล์ภาพจาก Streamlit File Upload
        image = Image.open(image_file)
        
        # คัดลอก EXIF เดิม
        exif_dict = image.getexif()

        # บันทึก Description/Alt Text (UserComment)
        encoded_description = bytes(metadata["Description"], 'utf-8')
        exif_dict[USER_COMMENT_ID] = encoded_description

        # บันทึก Title (ImageDescription)
        encoded_title = bytes(metadata["Title"], 'utf-8')
        exif_dict[IMAGE_DESCRIPTION_ID] = encoded_title

        # Note: Keywords ถูกจัดเก็บเป็นส่วนหนึ่งของระบบ/ไฟล์ IPTC/XMP ซึ่ง Pillow ไม่รองรับโดยตรง
        # เราใช้ Title/Description ใน EXIF แทน ซึ่งเป็นข้อมูลหลักที่จำเป็นสำหรับ SEO 

        # สร้าง Stream สำหรับบันทึกไฟล์ผลลัพธ์
        output_io = io.BytesIO()
        # บันทึกโดยใส่ EXIF Dictionary เข้าไป
        image.save(output_io, format="jpeg", exif=exif_dict)
        output_io.seek(0)
        
        return output_io

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการอัปเดตไฟล์: {e}")
        return None

# --- 2. ส่วนติดต่อผู้ใช้ (UI) ด้วย Streamlit ---

st.set_page_config(page_title="SEO Image Metadata Tool", layout="wide")
st.title("🖼️ แอปพลิเคชันใส่ Metadata SEO (Title, Description, 50 Keywords)")
st.caption("อัปโหลดภาพ, กรอกข้อมูล SEO, และดาวน์โหลดไฟล์ใหม่ที่อัปเดตแล้ว")

# อัปโหลดไฟล์ภาพ
uploaded_file = st.file_uploader("1. เลือกไฟล์ภาพ (JPG, JPEG) เพื่ออัปโหลด:", type=["jpg", "jpeg"])

if uploaded_file is not None:
    # แสดงตัวอย่างภาพ
    st.image(uploaded_file, caption='ภาพตัวอย่างที่เลือก', use_column_width=True)
    
    st.subheader("2. 📝 กรอกข้อมูล Metadata ที่ผ่านการทำ SEO แล้ว")
    
    with st.form("metadata_form"):
        # 1. ชื่อภาพ
        input_title = st.text_input("ชื่อภาพ (Title):", placeholder="ควรสั้น กระชับ และมีคีย์เวิร์ดหลัก")
        
        # 2. คำอธิบายภาพ
        input_description = st.text_area("คำอธิบายภาพ (Alt Text/Description):", 
                                          placeholder="อธิบายภาพอย่างละเอียด ใส่คีย์เวิร์ดที่เกี่ยวข้องอย่างเป็นธรรมชาติ (แนะนำ 100-150 อักขระ)",
                                          max_chars=300)
        
        # 3. คีย์เวิร์ด 50 คำ
        input_keywords_raw = st.text_area("คีย์เวิร์ดหลัก (Keywords):", 
                                          placeholder="พิมพ์คีย์เวิร์ดสูงสุด 50 คำ คั่นด้วย , หรือขึ้นบรรทัดใหม่",
                                          height=150)
        
        submitted = st.form_submit_button("3. 💾 บันทึกและดาวน์โหลดไฟล์ภาพที่อัปเดต")
        
        if submitted:
            if not input_title or not input_description or not input_keywords_raw:
                 st.error("กรุณากรอกข้อมูล ชื่อภาพ คำอธิบาย และคีย์เวิร์ดให้ครบถ้วนก่อนบันทึก")
            else:
                # แปลงคีย์เวิร์ดดิบให้เป็น List และจำกัดจำนวน
                keywords_list = [k.strip() for k in input_keywords_raw.replace('\n', ',').split(',') if k.strip()]
                
                # จำกัดที่ 50 คำ
                if len(keywords_list) > 50:
                    keywords_list = keywords_list[:50]
                    st.warning(f"⚠️ ตรวจพบมากกว่า 50 คำ. ระบบใช้เพียง 50 คำแรกแล้ว")
                
                # สร้างแพ็คเก็ต
                metadata_packet = create_seo_metadata_packet(
                    input_title,
                    input_description,
                    keywords_list
                )
                
                # อัปเดต Metadata ลงในไฟล์
                updated_file_io = update_image_metadata(uploaded_file, metadata_packet)
                
                if updated_file_io:
                    # แสดงผลสำเร็จและปุ่มดาวน์โหลด
                    st.success("บันทึก Metadata สำเร็จแล้ว! ไฟล์พร้อมให้ดาวน์โหลด")
                    
                    st.download_button(
                        label="📥 ดาวน์โหลดไฟล์ภาพที่อัปเดต",
                        data=updated_file_io,
                        file_name=f"seo-meta-{uploaded_file.name}",
                        mime="image/jpeg"
                    )
                    st.info(f"✅ คีย์เวิร์ดที่ใช้: {', '.join(keywords_list)}")

