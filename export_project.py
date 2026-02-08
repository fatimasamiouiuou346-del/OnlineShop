import os

# --- 配置区域 ---
# 脚本运行后，会在当前目录生成这个文件
OUTPUT_FILE = 'project_code.txt'

# 要忽略的文件夹（非常重要，避免把虚拟环境和Git库打包进去）
IGNORE_DIRS = {
    'venv', '.venv', 'env', '.git', '__pycache__', 'migrations', 
    'node_modules', '.idea', '.vscode'
}

# 要包含的文件后缀
ALLOWED_EXTENSIONS = {
    '.py', '.html', '.css', '.js', '.json', '.xml', '.txt', '.md'
}

# 要忽略的具体文件名
IGNORE_FILES = {
    'db.sqlite3', 'export_project.py', 'package-lock.json', 'yarn.lock'
}

def is_text_file(filename):
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

def export_project():
    # 获取脚本所在的当前目录
    root_dir = os.getcwd()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write(f"=== Django Project Export ===\n")
        outfile.write(f"Root: {root_dir}\n\n")

        # 遍历目录
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # 修改 dirnames 列表，以便就地过滤掉不需要的文件夹
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

            for filename in filenames:
                if filename in IGNORE_FILES:
                    continue
                
                if not is_text_file(filename):
                    continue

                filepath = os.path.join(dirpath, filename)
                # 计算相对路径，方便阅读
                relative_path = os.path.relpath(filepath, root_dir)

                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        
                    # 写入分隔符和文件名
                    outfile.write(f"\n{'='*20} START FILE: {relative_path} {'='*20}\n")
                    outfile.write(content)
                    outfile.write(f"\n{'='*20} END FILE: {relative_path} {'='*20}\n")
                    print(f"已处理: {relative_path}")
                    
                except Exception as e:
                    print(f"跳过文件 {relative_path}: {e}")

    print(f"\n成功！所有代码已导出到: {OUTPUT_FILE}")
    print("请打开这个文件，全选复制发送给我。")

if __name__ == '__main__':
    export_project()