import csv
import requests
import os
import re  # Додали бібліотеку для пошуку цифр у назві файлу

# --- НАЛАШТУВАННЯ ---
INPUT_DIR = 'input'
OUTPUT_DIR = 'output'

def find_column_by_keyword(fieldnames, keywords):
    """Шукає колонку за ключовими словами (git, repo і т.д.)"""
    if not fieldnames: 
        return None
    for col in fieldnames:
        clean_col = str(col).lower().strip()
        for kw in keywords:
            if kw.lower() in clean_col:
                return col
    return None

def extract_group_from_filename(filename):
    """Витягує перше знайдене число з назви файлу (groups_401.csv -> 401)"""
    match = re.search(r'\d+', filename)
    if match:
        return match.group()
    return None

def check_repo(username, repo_name):
    if not username or not repo_name:
        # якщо немає імені користувача або назви репозиторію — статус порожній
        return "EMPTY"

    username, repo_name = username.strip(), repo_name.strip()
    url = f"https://github.com/{username}/{repo_name}"

    try:
        # перевіряємо, чи існує сам репозиторій на GitHub
        response = check_url(url)
        if response == 'FAIL':
            return "ERROR1 Repo Not Found"

        # перевіряємо доступ до вмісту репозиторію через API
        api_url = f"https://api.github.com/repos/{username}/{repo_name}/contents"

        api_response = check_url(api_url)
        if api_response == 'FAIL':
            return "ERROR1 Repo Not Found"

        files = api_response.json()

        # шукаємо файл README.md серед вмісту репозиторію
        RMmdCheck = any(item.get("type") == "file" and item.get("name", "").lower() == "readme.md" for item in files)
        if not RMmdCheck:
            return "ERROR2 No README.md"                

        return "OK"
    except:
        # будь-яка інша помилка (мережа, API, парсинг) — загальна помилка
        return "ERROR"
    
def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response
        else:
            return 'FAIL'
    except:
        return 'FAIL'
    
def main():
    if not os.path.exists(OUTPUT_DIR): 
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(INPUT_DIR): 
        print("Folder 'input' not found yet.")
        return

    csv_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.csv')]
    
    for filename in csv_files:
        print(f"\n📄 Processing: {filename}")
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        with open(input_path, mode='r', encoding='utf-8') as infile:
            clean_lines = (line.replace('\0','') for line in infile)
            reader = csv.DictReader(clean_lines)
            fieldnames = reader.fieldnames
            
           # 1. Шукаємо колонку Git Name (як і раніше) 
            git_col = find_column_by_keyword(fieldnames, ['git name', 'git', 'github'])
            
           # 2. НОВА ЛОГІКА: Шукаємо колонку Групи на основі назви файлу
            group_number = extract_group_from_filename(filename)
            repo_col = None
            
            if group_number and group_number in fieldnames:
               # Ідеальний варіант: знайшли "401" у назві файлу і така колонка є
                repo_col = group_number
                print(f"   ✅ Знайшов групу {group_number} з назви файлу!")
            else:
                 # Запасний варіант: якщо файл названий криво, шукаємо слово 'repo'
                print(f"   ⚠️ Не знайшов колонку '{group_number}'. Шукаю за ключовими словами...")
                repo_col = find_column_by_keyword(fieldnames, ['repo', 'repository'])

            print(f"   🎯 Target Columns -> Git: '{git_col}' | Repo: '{repo_col}'")
            
            if not repo_col: 
                print("   ❌ Колонка з репозиторієм не знайдена. Пропускаю файл.")
                continue
              # Додаємо статус
            new_fieldnames = fieldnames + ['Status']
            rows_to_write = []
            
            for row in reader:
                git_user = str(row.get(git_col, '') or '').strip()
                repo_name = str(row.get(repo_col, '') or '').strip()
                
                status = "EMPTY"
                if len(git_user) > 1 and len(repo_name) > 1:
                    status = check_repo(git_user, repo_name)
                    print(f"   👉 {git_user}/{repo_name} -> {status}")
                
                row['Status'] = status
                rows_to_write.append(row)

        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(rows_to_write)
main()
 
