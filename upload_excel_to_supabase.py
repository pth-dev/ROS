"""
Script để upload file Excel lên Supabase PostgreSQL (Lần đầu tiên)
Thay thế toàn bộ data cũ bằng data mới
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
    print("   Create .env file with: DATABASE_URL=your_connection_string")
    exit(1)

def upload_excel_to_db(excel_file_path, table_name='ro_items'):
    """
    Upload Excel file to Supabase PostgreSQL
    
    Args:
        excel_file_path: Đường dẫn đến file Excel
        table_name: Tên bảng trong database (mặc định: ro_items)
    """
    try:
        # Đọc file Excel (header ở row 2)
        print(f"Đọc file Excel: {excel_file_path}")
        df = pd.read_excel(excel_file_path, header=1)
        
        # Tìm cột Item Code
        item_col = None
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'item' in col_lower and 'code' in col_lower:
                item_col = col
                break
            elif 'item' in col_lower:
                item_col = col
        
        # Tìm cột Avg Consume
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
            print(f"   Item Code column: {item_col}")
            print(f"   Avg Consume column: {avg_col}")
            return
        
        # Chọn và đổi tên cột
        df_filtered = df[[item_col, avg_col]].copy()
        df_filtered.columns = ['item_code', 'avg_consume']
        
        # Loại bỏ dòng trống
        df_filtered = df_filtered.dropna()
        
        # Loại bỏ duplicate (giữ item đầu tiên)
        df_filtered = df_filtered.drop_duplicates(subset=['item_code'], keep='first')
        
        # Chuyển đổi kiểu dữ liệu
        df_filtered['item_code'] = df_filtered['item_code'].astype(str)
        df_filtered['avg_consume'] = pd.to_numeric(df_filtered['avg_consume'], errors='coerce')
        
        # Loại bỏ những dòng avg_consume không hợp lệ
        df_filtered = df_filtered.dropna(subset=['avg_consume'])
        
        print(f"✓ Đã xử lý: {len(df_filtered)} items")
        
        # Kết nối database
        print("Đang kết nối Supabase...")
        engine = create_engine(DATABASE_URL)
        
        # Upload lên database (replace = xóa bảng cũ và tạo mới)
        print(f"Đang upload lên bảng '{table_name}'...")
        df_filtered.to_sql(
            table_name, 
            engine, 
            if_exists='replace',  # Thay thế toàn bộ
            index=False
        )
        
        print(f"✅ Upload thành công {len(df_filtered)} items lên Supabase!")
        print(f"   Bảng: {table_name}")
        
        # Hiển thị sample data
        print("\n📊 Sample data (5 dòng đầu):")
        print(df_filtered.head().to_string(index=False))
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")

if __name__ == "__main__":
    # Tìm file Excel trong folder data
    data_folder = "data"
    
    if not os.path.exists(data_folder):
        print(f"❌ Folder '{data_folder}' không tồn tại!")
    else:
        excel_files = [f for f in os.listdir(data_folder) if f.endswith(('.xlsx', '.xls'))]
        
        if len(excel_files) == 0:
            print(f"❌ Không tìm thấy file Excel trong folder '{data_folder}'")
        else:
            # Lấy file đầu tiên
            excel_file = os.path.join(data_folder, excel_files[0])
            print(f"🔍 File Excel: {excel_files[0]}")
            upload_excel_to_db(excel_file)
