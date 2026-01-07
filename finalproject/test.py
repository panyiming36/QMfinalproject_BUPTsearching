import pandas as pd
import os

# 1. 首先检查数据读取
print("=== 数据读取测试 ===")
file_path = "bupt.xls"

try:
    # 尝试不同的引擎读取Excel
    engines = ['openpyxl', 'xlrd', 'odf']
    
    for engine in engines:
        try:
            print(f"\n尝试使用引擎: {engine}")
            df = pd.read_excel(file_path, engine=engine)
            print(f"✅ 成功使用 {engine} 引擎读取Excel文件")
            print(f"   总行数: {len(df)}")
            print(f"   总列数: {len(df.columns)}")
            
            # 显示列名
            print("\n列名:")
            for i, col in enumerate(df.columns):
                print(f"{i+1:2d}. '{col}'")
            
            # 显示前2行数据
            print("\n前2行数据:")
            for i in range(min(2, len(df))):
                print(f"\n行 {i+1}:")
                row = df.iloc[i]
                for col in df.columns:
                    value = row[col]
                    if pd.notna(value):
                        print(f"  {col}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                    else:
                        print(f"  {col}: [空]")
            
            break  # 成功就跳出循环
            
        except Exception as e:
            print(f"❌ 引擎 {engine} 失败: {e}")
            continue
            
except Exception as e:
    print(f"\n❌ 所有引擎都失败了: {e}")
    
    # 尝试其他方法
    print("\n=== 尝试其他方法 ===")
    
    # 方法1: 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
    else:
        print(f"文件存在，大小: {os.path.getsize(file_path)} 字节")
    
    # 方法2: 尝试读取HTML
    try:
        print("\n尝试作为HTML读取...")
        dfs = pd.read_html(file_path)
        print(f"✅ 成功读取HTML，找到 {len(dfs)} 个表格")
        df = dfs[0]
        print(f"表格形状: {df.shape}")
        print("\n列名:")
        for i, col in enumerate(df.columns):
            print(f"{i+1:2d}. '{col}'")
    except Exception as html_err:
        print(f"❌ 读取HTML失败: {html_err}")
    
    # 方法3: 显示文件前几行内容
    print(f"\n=== 文件前100字节 ===")
    try:
        with open(file_path, 'rb') as f:
            first_bytes = f.read(100)
            print(f"文件开头: {first_bytes}")
            
            # 检查文件签名
            if first_bytes.startswith(b'PK'):  # ZIP/Excel格式
                print("文件签名: PK (ZIP/Excel格式)")
            elif b'<html' in first_bytes.lower():
                print("文件签名: HTML格式")
            elif b'<table' in first_bytes.lower():
                print("文件签名: 包含table标签的HTML")
            else:
                print("文件签名: 未知格式")
    except Exception as file_err:
        print(f"读取文件字节失败: {file_err}")