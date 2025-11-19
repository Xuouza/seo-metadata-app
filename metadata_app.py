import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
import io
import os

# --- 1. ตัวแปรและฟังก์ชันจัดการ Metadata ---

# Tag ID ที่ใช้ใน EXIF (สำหรับ JPEG)
USER_COMMENT_ID = 37510 
IMAGE_DESCRIPTION_ID = 270 

def create_seo_metadata_packet(title_input, description_input, keywords_list):
    """
    สร้างแพ็คเก็ตข้อมูล Metadata สำหรับ SEO
    """
    validated_keywords = keywords_list[:50]
    return {
        "Title": title_input,
        "Description": description_input,  
        "Keywords": validated_keywords, 
    }

def update_image_metadata(image_file, metadata):
    """
    อัปเดต Metadata เข้าไปในไฟล์ภาพที่อัปโหลด (รองรับ JPG และ PNG)
    """
    try:
        image = Image.open(image_file)
        file_type = image.format.upper()
        output_io = io.BytesIO()

        if file_type in ['JPEG', 'JPG']:
            # --- สำหรับ JPEG (ใช้ EXIF) ---
            exif_dict = image.getexif()
            
            # บันทึก Description/Alt Text (UserComment)
            encoded_description = bytes(metadata["Description"], 'utf-8')
            exif_dict[USER_COMMENT_ID] = encoded_description

            # บันทึก Title (ImageDescription)
            encoded_title = bytes(metadata["Title"], 'utf-8')
            exif_dict[IMAGE_DESCRIPTION_ID] = encoded_title

            image.save(output_io, format="jpeg", exif=exif_dict)
            st.info(f"💾 ไฟล์ประเภท JPEG ถูกบันทึกพร้อม Metadata (EXIF)")

        elif file_type == 'PNG':
            # --- สำหรับ PNG (ใช้ pnginfo) ---
            
            # คัดลอก info เดิม (ถ้ามี)
            png_info = image.info.copy()
            
            # ใช้ Text Chunk สำหรับ Title และ Description
            png_info['title'] = metadata["Title"]
            png_info['description'] = metadata["Description"]
            
            image.save(output_io, format="png", pnginfo=png_info)
            st.info(f"💾 ไฟล์ประเภท PNG ถูกบันทึกพร้อม Metadata (pnginfo)")

        else:
            st.warning(f"❌ ไม่รองรับการเขียน Metadata สำหรับไฟล์ประเภท {file_type} แต่จะบันทึกไฟล์เดิมกลับไป")
            image.save(output_io, format=file_type.lower())

        output_io.seek(0)
        return output_io

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการอัปเดตไฟล์: {e}")
        return None

# --- 2. ส่วนติดต่อผู้ใช้ (UI) ด้วย Streamlit ---

st.set_page_config(page_title="SEO Image Metadata Tool", layout="wide")
st.title("🖼️ แอปพลิเคชันใส่ Metadata SEO (Title, Description, 50 Keywords)")
st.caption("รองรับไฟล์ภาพ PNG และ JPEG")

# อัปโหลดไฟล์ภาพ
uploaded_file = st.file_uploader("1. เลือกไฟล์ภาพ (JPG, JPEG, PNG) เพื่ออัปโหลด:", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # แสดงตัวอย่างภาพ
    st.image(uploaded_file, caption=f'ภาพตัวอย่างที่เลือก ({uploaded_file.type})', use_column_width=True)
    
    st.subheader("2. 📝 กรอกข้อมูล Metadata ที่ผ่านการทำ SEO แล้ว")
    
    with st.form("metadata_form"):
        # 1. ชื่อภาพ
        input_title = st.text_input("ชื่อภาพ (Title):", placeholder="ควรสั้น กระชับ และมีคีย์เวิร์ดหลัก")
        
        # 2. คำอธิบายภาพ
        input_description = st.text_area("คำอธิบายภาพ (Alt Text/Description):", 
                                          placeholder="อธิบายภาพอย่างละเอียด ใส่คีย์เวิร์ดที่เกี่ยวข้องอย่างเป็นธรรมชาติ",
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
                keywords_list = [k.strip() for k in input_keywords_raw.replace('\n', ',').split(',') if k.strip()]
                
                if len(keywords_list) > 50:
                    keywords_list = keywords_list[:50]
                    st.warning(f"⚠️ ตรวจพบมากกว่า 50 คำ. ระบบใช้เพียง 50 คำแรกแล้ว")
                
                metadata_packet = create_seo_metadata_packet(
                    input_title,
                    input_description,
                    keywords_list
                )
                
                updated_file_io = update_image_metadata(uploaded_file, metadata_packet)
                
                if updated_file_io:
                    st.success("บันทึก Metadata สำเร็จแล้ว! ไฟล์พร้อมให้ดาวน์โหลด")
                    
                    st.download_button(
                        label="📥 ดาวน์โหลดไฟล์ภาพที่อัปเดต",
                        data=updated_file_io,
                        file_name=f"seo-meta-{uploaded_file.name}",
                        mime=uploaded_file.type
                    )
                    st.info(f"✅ คีย์เวิร์ดที่ใช้: {', '.join(keywords_list)}")
