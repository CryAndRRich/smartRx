import csv
from typing import Tuple, Dict
import streamlit as st
import requests
import tomllib 
import json

with open(".streamlit/api_config.toml", "rb") as f:
    config = tomllib.load(f)

api_key = config["google"]["google_gemini_api"]
json_drug_list_path = "smartrx_web/json/drug_list_info.json"
json_drug_check_path = "smartrx_web/json/drug_check_info.json"
json_food_check_path = "smartrx_web/json/food_check_info.json"

url_api = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
def get_drug_info(drug_name: str) -> Tuple[str, Dict]:
    headers = {
        "Content-Type": "application/json",
    }
    
    prompt = (
        f"Vui lòng cung cấp thông tin sơ lược ngắn gọn nhất có thể cho thuốc có tên '{drug_name}'(Nếu không tìm được thuốc tên như vậy thì tự động thay bằng tên thuốc gần giống nhất, không cần thông báo lại về thay đổi). "
        "Trả về 3 đoạn văn, mỗi đoạn đánh số như sau, không yêu cầu tiêu đề:"
        "1. (Chỉ trả về cấu trúc 'drug name|chỉ English (generic) name không gồm drug name')"
        "2. (Mục đích sử dụng chỉ dùng tiếng Việt)"
        "3. (Hướng dẫn sử dụng chỉ dùng tiếng Việt)"
        "Vui lòng đảm bảo các thông tin rõ ràng và chính xác. Chỉ chả về chính xác 3 đoạn văn, không trả về thêm bất cứ text ngoại lệ nào khác ngoài 3 đoạn văn trên"
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url_api, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json["candidates"]
            if candidates:
                candidate = candidates[0]
                parts_list = candidate["content"]["parts"]
                if not parts_list:
                    st.error("Phần 'parts' không có dữ liệu.")
                    return {}
                full_text = parts_list[0]["text"].strip()
                
                parts = full_text.split("2.")
                drug_name_text = parts[0].strip()[2:]
                
                parts = parts[1].split("3.")
                purpose = parts[0].strip()
                general_usage = parts[1].strip() if len(parts) > 1 else ""
                
                result = {
                    "drug_name": drug_name_text,
                    "purpose": purpose,
                    "general_usage": general_usage
                }
                return drug_name_text, result
            else:
                st.error("API không trả về kết quả hợp lệ.")
                return {}
        else:
            st.error(f"Lỗi từ API: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        st.error(f"Exception khi gọi API Gemini: {str(e)}")
        return {}
    
def get_food_info(food_name: str) -> Tuple[str, Dict]:
    headers = {
        "Content-Type": "application/json",
    }
    
    prompt = (
        f"Vui lòng cung cấp thông tin sơ lược ngắn gọn nhất có thể cho loại thực phẩm có tên '{food_name}'(Nếu không tìm được thuốc tên như vậy thì tự động thay bằng tên thực phẩm gần giống nhất). "
        "Trả về 2 đoạn văn, mỗi đoạn đánh số như sau, không yêu cầu tiêu đề:"
        "1. (Chỉ có tên loại thực phẩm)"
        "2. (Các chất có trong loại thực phẩm đó, yêu cầu có đủ tên chất)"
        "Vui lòng đảm bảo các thông tin rõ ràng và chính xác. Chỉ chả về chính xác 2 đoạn văn, không trả về thêm bất cứ text ngoại lệ nào khác"
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url_api, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json["candidates"]
            if candidates:
                candidate = candidates[0]
                parts_list = candidate["content"]["parts"]
                if not parts_list:
                    st.error("Phần 'parts' không có dữ liệu.")
                    return {}
                full_text = parts_list[0]["text"].strip()
                
                parts = full_text.split("2.")
                drug_name_text = parts[0].strip()[2:]
                
                food_information = parts[1].strip() if len(parts) > 1 else ""
                
                result = {
                    "drug_name": drug_name_text,
                    "food_information": food_information
                }
                return drug_name_text, result
            else:
                st.error("API không trả về kết quả hợp lệ.")
                return {}
        else:
            st.error(f"Lỗi từ API: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        st.error(f"Exception khi gọi API Gemini: {str(e)}")
        return {}
    
def get_drug_input() -> None:
    with open(json_drug_check_path,'r', encoding="utf-8") as f:
        data = json.load(f)
    drug_check_list = list(data.keys())
    with open(json_drug_list_path, 'r', encoding="utf-8") as f:
        data = json.load(f)
    drug_list_list = list(data.keys())
    with open("data/Dataset/Input_txt/combined_drug_lists.txt", "w") as f:
        f.write("\t".join(drug_check_list) + "\n")
        f.write("\t".join(drug_list_list) + "\n")

def processing_result(input_file):
    results = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    num_pairs = len(rows) // 2
    
    for i in range(num_pairs):
        row1 = rows[2 * i]
        row2 = rows[2 * i + 1]
        
        try:
            score1 = float(row1["Score"])
        except ValueError:
            score1 = 0.0
        try:
            score2 = float(row2["Score"])
        except ValueError:
            score2 = 0.0
        
        if score1 >= score2:
            selected = row1
        else:
            selected = row2

        drug_pair = selected["Drug_pair"]
        drugs = drug_pair.split("_")
        if len(drugs) != 2:
            drugs = [drug_pair, ""]

        sentence = selected["Sentence"]

        score_val = float(selected["Score"])
        score_str = f"{score_val:.4f}"

        side_effect1 = selected.get("Side_effects (left)", "")
        side_effect2 = selected.get("Side_effects (right)", "")
        side_effect = f"{side_effect1} {side_effect2}".strip()

        result_item = drugs + [sentence, score_str, side_effect]

        results.append(result_item)
    
    return results

def get_result_text(result):
    drug1, drug2, sentence, score, _ = result
    drug1 = drug1.capitalize()
    drug2 = drug2.capitalize()
    headers = {
        "Content-Type": "application/json",
    }
    
    prompt = (
        f"Vui lòng cung cấp thông tin sơ lược ngắn gọn về tương tác hai loại thuốc {drug1} và {drug2} biết rằng đã có nội dung tương tác là {sentence}, chỉ cần bổ sung và làm rõ nội dung của tương tác. "
        "Nội dung là tương tác bất lợi thì trả về 4 đoạn văn được ngăn cách bởi 1 dấu gạch dọc ('|') trong đó nội dung từng đoạn như sau:"
        f"Đoạn 1: Chỉ có cấu trúc '{drug1} <-> {drug2}|{score}'"
        "Đoạn 2: Dịch nội dung tương tác đã cho ban đầu thành tiếng việt"
        "Đoạn 3: Bổ sung, giải thích nội dung cụ thể tương tác của đoạn 2, viết bằng tiếng việt và tránh dùng thuật ngữ"
        f"Đoạn 4: Liệt kê các tác dụng phụ (ít nhất 5 và không cần đánh số) tách bởi dấu phẩy và trả về bằng tiếng việt"
        "Vui lòng đảm bảo các thông tin rõ ràng và chính xác. Chỉ chả về chính xác 4 đoạn văn liền nhau chỉ cách bởi '|', không trả về thêm bất cứ text ngoại lệ nào khác ngoài 4 đoạn văn trên. Lưu ý các đoạn văn là 1 hoặc nhiều câu viết liền nhau, không xuống dòng"
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url_api, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
        
            candidates = res_json["candidates"]
            if candidates:
                candidate = candidates[0]
                parts_list = candidate["content"]["parts"]
                if not parts_list:
                    st.error("Phần 'parts' không có dữ liệu.")
                    return {}
                
                full_text = parts_list[0]["text"].strip()
                if full_text == "Không":
                    return {}
                
                parts = full_text.split("|")
                result = {
                    "drugs": parts[0],
                    "score": parts[1],
                    "sentence1": parts[2],
                    "sentence2": parts[3],
                    "side_effect": parts[4]
                }
                return result
            else:
                st.error("API không trả về kết quả hợp lệ.")
                return {}
        else:
            st.error(f"Lỗi từ API: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        st.error(f"Exception khi gọi API Gemini: {str(e)}")
        return {}
