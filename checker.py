import csv
import requests
import os
import re  # Додали бібліотеку для пошуку цифр у назві файлу
import logging 
import base64

logging.basicConfig(
    level=logging.DEBUG,  
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def log_block(title):
    logging.info("")
    logging.info("=" * 60)
    logging.info(f"🔷 {title}")
    logging.info("=" * 60)

def log_subblock(title):
    logging.info("-" * 40)
    logging.info(f"➡️ {title}")
    logging.info("-" * 40)

# --- НАЛАШТУВАННЯ ---
INPUT_DIR = 'input'
OUTPUT_DIR = 'output'



def find_column_by_keyword(fieldnames, keywords):
    logging.debug(f"Searching column by keywords: {keywords}")
    """Шукає колонку за ключовими словами (git, repo і т.д.)"""
    if not fieldnames:
        logging.warning("No fieldnames provided")
        return None

    for col in fieldnames:
        clean_col = str(col).lower().strip()
        for kw in keywords:
            if kw.lower() in clean_col:
                logging.info(f"Matched column '{col}' for keyword '{kw}'")
                return col

    logging.warning(f"No column found for keywords: {keywords}")
    return None

def extract_group_from_filename(filename):
    logging.debug(f"Extracting group from filename: {filename}")
    """Витягує перше знайдене число з назви файлу (groups_401.csv -> 401)"""
    match = re.search(r'\d+', filename)
    if match:
        group = match.group()
        logging.info(f"Extracted group: {group}")
        return group

    logging.warning("No group number found in filename")
    return None

def check_repo(username, repo_name, student_name, group):
    if not username or not repo_name:        #checking empty name and repo
        logging.warning("Empty username or repo name")
        return "EMPTY"

    username, repo_name = username.strip(), repo_name.strip()
    url = f"https://github.com/{username}/{repo_name}"

    try:
        log_block(f"CHECK REPO: {username}/{repo_name}")

        response = check_url(url)            #checking repo
        if response == 'FAIL':
            logging.error(f"Repository not found: {url}")
            return "ERROR1 Repo Not Found"

        api_url = f"https://api.github.com/repos/{username}/{repo_name}/contents"
        logging.info(f"Checking repository contents: {api_url}")

        api_response = check_url(api_url)
        if api_response == 'FAIL':
            logging.error("GitHub API request failed")
            return "ERROR1 Repo Not Found"

        files = api_response.json()
        logging.debug(f"Repository files: {[f.get('name') for f in files]}")

        RMmdCheck = any(
            item.get("type") == "file" and item.get("name", "").lower() == "readme.md"
            for item in files
        )

        if not RMmdCheck:
            logging.warning("README.md not found")
            return "ERROR2 No README.md"
                #getting readme

        logging.info("Fetching README.md content")

        readme_file = next(
            (item for item in files if item.get("name", "").lower() == "readme.md"),
            None
        )

        if not readme_file:
            logging.error("README object not found (unexpected)")
            return "ERROR2 No README.md"
        
        readme_url = readme_file.get("url")
        
        readme_response = check_url(readme_url)
        
        if readme_response == 'FAIL':
            logging.error("Failed to fetch README content")
            return "ERROR"
        #decoding readme
        readme_data = readme_response.json()

        content_base64 = readme_data.get("content", "")
        
        try:
            decoded_content = base64.b64decode(content_base64).decode('utf-8')
            logging.info("README decoded successfully")
        except Exception as e:
            logging.error(f"README decode error: {e}")
            return "ERROR"
            
        # ===============================
        #         README VALIDATION
        # ===============================
        logging.info("Advanced validation of README")

        content_lower = decoded_content.lower()

        # --- 1. ОБРОБКА ПІП ---
        logging.info("Checking student name")
        
        if not student_name or student_name.strip() == "":
            logging.warning("Student name is empty")
            return "ERROR3 Name missing"
        name_parts = [p.strip().lower() for p in student_name.split() if p.strip()]
        
        found_parts = []
        for part in name_parts:
            if part in content_lower:
                found_parts.append(part)
                
        logging.debug(f"Name parts from table: {name_parts}")
        logging.info(f"Name parts found: {found_parts}")

        # всі слова повинні бути
        logging.debug(f"found_parts = {found_parts}")
        logging.debug(f"name_parts = {name_parts}")
        if len(found_parts) != len(name_parts):
            logging.warning(f"Not all name parts found: {student_name}")
            return "ERROR3 Name mismatch"

        logging.info("Student name matched")

        # --- 2. ОБРОБКА ГРУПИ ---
        logging.info("Checking group")

        # Витягуємо тільки цифри з групи 
        group_digits_match = re.search(r'\d+', str(group))
        group_digits = group_digits_match.group() if group_digits_match else None

        if not group_digits:
            logging.warning(f"Could not extract digits from group: {group}")
        else:
            logging.info(f"Extracted group digits: {group_digits}")

        # Шукаємо номер групи 
        group_found = False
        
        if group_digits and re.search(rf"\D?{group_digits}\b", content_lower):
            group_found = True
            logging.info(f"Group matched via regex: {group_digits}")

        if not group_found:
            logging.warning(f"Group not found in README: {group}")
            return "ERROR4 Group mismatch"

        # --- УСПІХ ---
        logging.info("Repository check passed")
        return "OK"
    except Exception as e:
        logging.exception(f"Unexpected error while checking repo: {e}")
        return "ERROR"
    
def check_url(url):
    logging.debug(f"Sending request to: {url}")

    try:
        response = requests.get(url, timeout=5)
        logging.debug(f"Response status: {response.status_code}")

        if response.status_code == 200:
            return response
        else:
            logging.warning(f"Non-200 status code: {response.status_code} for {url}")
            return 'FAIL'

    except Exception as e:
        logging.error(f"Request failed for {url}: {e}")
        return 'FAIL'
    
def main():
    log_block("START CHECKER")

    log_subblock("Checking directories")
    
    if not os.path.exists(OUTPUT_DIR):
        logging.info("[ACTION] Creating output directory")
        os.makedirs(OUTPUT_DIR)
    
    if not os.path.exists(INPUT_DIR):
        logging.error("Input directory not found")
        return
    
    logging.info("Directories ready")

    log_subblock("Searching CSV files")
    
    csv_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.csv')]
    
    logging.info(f"Found {len(csv_files)} CSV files")
    
    for filename in csv_files:
        log_block(f"PROCESSING FILE: {filename}")
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        with open(input_path, mode='r', encoding='utf-8') as infile:
            logging.debug(f"Opening file: {input_path}")

            clean_lines = (line.replace('\0','') for line in infile)
            reader = csv.DictReader(clean_lines)
            fieldnames = reader.fieldnames

            logging.info(f"Columns detected: {fieldnames}")
      

    
               
                     
            git_col = find_column_by_keyword(fieldnames, ['git name', 'git', 'github'])
           # 1. Шукаємо колонку Git Name (як і раніше) 
            group_number = extract_group_from_filename(filename)
            repo_col = None
           # 2. НОВА ЛОГІКА: Шукаємо колонку Групи на основі назви файлу  
            if group_number and group_number in fieldnames:
                repo_col = group_number
                logging.info(f"Using group column: {group_number}")
                # Ідеальний варіант: знайшли "401" у назві файлу і така колонка є
            else:
                logging.warning(f"Group column '{group_number}' not found. Trying fallback...")
                repo_col = find_column_by_keyword(fieldnames, ['repo', 'repository'])
                  # Запасний варіант: якщо файл названий криво, шукаємо слово 'repo'  
            logging.info(f"Selected columns -> Git: {git_col}, Repo: {repo_col}")
            
            if not repo_col:
                logging.error("Repository column not found. Skipping file.")
                continue
              # Додаємо статус
            new_fieldnames = fieldnames + ['Status']
            rows_to_write = []

            group_col = find_column_by_keyword(fieldnames, ['group', 'груп'])
            logging.info(f"Selected group column: {group_col}")
            
            for i, row in enumerate(reader, start=2):
                git_user = str(row.get(git_col, '') or '').strip()
                repo_name = str(row.get(repo_col, '') or '').strip()
            
                surname = str(row.get("Прізвище", "") or "").strip()
                name = str(row.get("Ім'я", "") or "").strip()
                father = str(row.get("По-батькові", "") or "").strip()
                student_name = f"{surname} {name} {father}".strip()
            
                group = str(row.get(group_col, "") or "").strip() if group_col else ""


                
                if not student_name:
                    logging.warning(f"This students name is EMPTY on row: {i}")
                else:
                    logging.info("") 
                    logging.info(f"Student: {student_name}")
                    if not group:
                        logging.warning("Group is empty for this student")
                    else:
                        logging.info(f"Group: {group}")
                    
                    if not git_user:
                        logging.warning(f"Empty Git username for this student")
                    else:
                        logging.info(f"Username: {git_user}")
                    
                    if not repo_name:
                        logging.warning(f"Empty repository for this student")
                    else:
                        logging.info(f"Repository: {repo_name}")
                        
                
                if len(git_user) > 1 and len(repo_name) > 1:
                    status = check_repo(git_user, repo_name, student_name, group)
                    logging.info(f"STATUS: {git_user}/{repo_name} -> {status}")
                    logging.info("")
                else:
                    status = "EMPTY"
                
                


                
                row['Status'] = status
                rows_to_write.append(row)

        logging.info(f"Writing results to: {output_path}")

        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(rows_to_write)

        log_block(f"FINISHED FILE: {filename}")
    log_block("END CHECKER")
main()
    
 
