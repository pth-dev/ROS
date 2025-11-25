"""
Script để merge data thông minh (Upsert mode)
- Nếu item_code đã tồn tại -> UPDATE avg_consume
- Nếu item_code chưa có -> INSERT mới
"""

import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase connection string from .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file!")
    exit(1)

def upsert_excel_to_db(excel_file_path, table_name='ro_items'):
    """
    Upsert items từ Excel vào database
    - Update nếu item_code đã tồn tại
    - Insert nếu item_code chưa có
    
    Args:
        excel_file_path: Đường dẫn đến file Excel
        table_name: Tên bảng trong database
    """
    try:
        # Đọc file Excel
        print(f"Đọc file Excel: {excel_file_path}")
        df = pd.read_excel(excel_file_path, header=1)
        
        # Xử lý data
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
        
        # Tạo bảng tạm
        temp_table = f"{table_name}_temp"
        print(f"Tạo bảng tạm: {temp_table}")
        df_filtered.to_sql(temp_table, engine, if_exists='replace', index=False)
        
        # Thực hiện UPSERT bằng SQL
        print("Đang thực hiện UPSERT...")
        with engine.connect() as conn:
            # Tạo bảng chính nếu chưa có
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                item_code TEXT PRIMARY KEY,
                avg_consume NUMERIC
            );
            """
            conn.execute(text(create_table_sql))
            conn.commit()
            
            # UPSERT: INSERT ... ON CONFLICT DO UPDATE
            upsert_sql = f"""
            INSERT INTO {table_name} (item_code, avg_consume)
            SELECT item_code, avg_consume FROM {temp_table}
            ON CONFLICT (item_code) 
            DO UPDATE SET avg_consume = EXCLUDED.avg_consume;
            """
            result = conn.execute(text(upsert_sql))
            conn.commit()
            
            # Xóa bảng tạm
            conn.execute(text(f"DROP TABLE {temp_table}"))
            conn.commit()
        
        print(f"✅ Upsert thành công {len(df_filtered)} items!")
        print("   - Items mới: đã INSERT")
        print("   - Items cũ: đã UPDATE avg_consume")
        
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
            upsert_excel_to_db(excel_file)
