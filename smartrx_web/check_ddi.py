import streamlit as st
import json
import os

from smartrx_web.utils import *

if not os.path.exists(json_drug_check_path):
    with open(json_drug_check_path, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

st.markdown("Hãy nhập và các loại thuốc bạn còn lo ngại và muốn kiểm tra, **SmartRx** sẽ giúp bạn kiểm tra tương tác không chỉ giữa những loại thuốc đó với nhau mà còn với cả những thuốc bạn đã có trong danh sách của bản thân!")
drug_name_input = st.text_input("Nhập tên thuốc:", "VD: Ibuprofen")

if st.button("Thêm thuốc"):
    if drug_name_input:
        name, drug_info = get_drug_info(drug_name_input)
        drug_name_input = name.strip()
        if drug_info:
            with open(json_drug_check_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data[drug_name_input] = drug_info
            
            with open(json_drug_check_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            st.success(f"Đã thêm {drug_name_input}.")
        else:
            st.error("Không lấy được dữ liệu từ API.")
    else:
        st.error("Vui lòng nhập lại tên thuốc.")

with open(json_drug_check_path, "r", encoding="utf-8") as f:
    drugs_data = json.load(f)
with open(json_drug_list_path, "r", encoding="utf-8") as f:
    drugs_list_data = json.load(f)

if drugs_data:
    for drug_name, info in drugs_data.items():
        check = "Chưa có trong danh sách thuốc"
        if drug_name in drugs_list_data.keys():
            check = "Đã có trong danh sách thuốc"
        with st.expander(drug_name):
            st.markdown(f"**Tên thuốc:** {info.get('drug_name', drug_name)}")
            st.markdown(f"**Mục đích sử dụng:** {info.get('purpose', 'Chưa cập nhật')}")
            st.markdown(f"**Hướng dẫn sử dụng:** {info.get('general_usage', 'Chưa cập nhật')}")
            st.markdown(f"**Chú ý:** {check}")

            if check == "Đã có trong danh sách thuốc":
                if st.button(f"Xoá", key=f"delete_{drug_name}"):
                    drugs_data.pop(drug_name)

                    with open(json_drug_check_path, "w", encoding="utf-8") as f:
                        json.dump(drugs_data, f, ensure_ascii=False, indent=4)

                    st.rerun()
            elif check == "Chưa có trong danh sách thuốc":
                col1, col2, _ = st.columns([25, 70, 120]) 

                with col1:
                    if st.button("Xoá", key=f"delete_{drug_name}"):
                        drugs_data.pop(drug_name)
                        with open(json_drug_check_path, "w", encoding="utf-8") as f:
                            json.dump(drugs_data, f, ensure_ascii=False, indent=4)
                        st.rerun()

                with col2:
                    if st.button("Thêm vào danh sách thuốc", key=f"add_{drug_name}"):
                        drugs_list_data[drug_name] = info
                        with open(json_drug_list_path, "w", encoding="utf-8") as f:
                            json.dump(drugs_list_data, f, ensure_ascii=False, indent=4)
                        st.success(f"Đã thêm {drug_name} vào danh sách thuốc chính.")
                        check = "Đã có trong danh sách thuốc"
                        st.rerun()
else:
    st.info("Chưa có thông tin thuốc nào được thêm vào.")

if st.button("Kiểm tra tương tác"):
    get_drug_input()

    results = processing_result(input_file="data/Result/final_result.csv")
    for res in results:
        r = get_result_text(res)
        if len(r.keys()) == 0:
            continue
        
        with st.expander(r['drugs']):
            st.markdown(f"**Tương tác bất lợi**: {r['sentence1']}")
            st.markdown(f"**Nội dung bất lợi**: {r['sentence2']}")
            st.markdown(f"**Tác dụng phụ**: {r['side_effect']}")
            st.markdown(f"**Độ chính xác dự đoán**: {r['score']}")


hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
