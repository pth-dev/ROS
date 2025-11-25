"""
Script để thêm items mới từ Excel vào Supabase (Append mode)
Giữ nguyên data cũ, chỉ thêm items mới
"""

import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase connection string from .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file!")
    exit(1)

def append_excel_to_db(excel_file_path, table_name='ro_items'):
    """
    Thêm items từ Excel vào database (không xóa data cũ)
    
    Args:
        excel_file_path: Đường dẫn đến file Excel
        table_name: Tên bảng trong database
    """
    try:
        # Đọc file Excel
        print(f"Đọc file Excel: {excel_file_path}")
        df = pd.read_excel(excel_file_path, header=1)
        
        # Xử lý tương tự như upload_excel_to_db
        item_col = None
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'item' in col_lower and 'code' in col_lower:
                item_col = col
                break
            elif 'item' in col_lower:
                item_col = col
        
        avg_col = None
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'avg' in col_lower and 'consume' in col_lower:
                avg_col = col
                break
            elif 'consume' in col_lower:
                avg_col = col
        
        if not item_col or not avg_col:
            print(f"❌ Không tìm thấy cột cần thiết!")
            return
        
        df_filtered = df[[item_col, avg_col]].copy()
        df_filtered.columns = ['item_code', 'avg_consume']
        df_filtered = df_filtered.dropna()
        df_filtered = df_filtered.drop_duplicates(subset=['item_code'], keep='first')
        df_filtered['item_code'] = df_filtered['item_code'].astype(str)
        df_filtered['avg_consume'] = pd.to_numeric(df_filtered['avg_consume'], errors='coerce')
        df_filtered = df_filtered.dropna(subset=['avg_consume'])
        
        print(f"✓ Đã xử lý: {len(df_filtered)} items")
        
        # Kết nối database
        print("Đang kết nối Supabase...")
        engine = create_engine(DATABASE_URL)
        
        # Append vào database (giữ data cũ, thêm data mới)
        print(f"Đang thêm vào bảng '{table_name}'...")
        df_filtered.to_sql(
            table_name, 
            engine, 
            if_exists='append',  # Thêm vào data cũ
            index=False
        )
        
        print(f"✅ Đã thêm {len(df_filtered)} items vào Supabase!")
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")

if __name__ == "__main__":
    data_folder = "data"
    
    if not os.path.exists(data_folder):
        print(f"❌ Folder '{data_folder}' không tồn tại!")
    else:
        excel_files = [f for f in os.listdir(data_folder) if f.endswith(('.xlsx', '.xls'))]
        
        if len(excel_files) == 0:
            print(f"❌ Không tìm thấy file Excel trong folder '{data_folder}'")
        else:
            excel_file = os.path.join(data_folder, excel_files[0])
            print(f"🔍 File Excel: {excel_files[0]}")
            append_excel_to_db(excel_file)
