#!/usr/bin/env python3
import os
import glob
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

def build_advanced_excel_report():
    print("[+] Initializing Ultra-Fast Regex Excel Reporter Engine...")
    
    if not os.path.exists('targets.txt'):
        print("[-] Error: targets.txt missing.")
        return
        
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f if line.strip()]

    # [★초고속 치트키 1★] 도메인 매칭을 C 라이브러리 정규식 엔진으로 통합 컴파일
    # 글자 수가 긴 도메인이 먼저 매칭되도록 정렬 후 regex 빌드
    targets = sorted(targets, key=len, reverse=True)
    domain_pattern = re.compile('(' + '|'.join(map(re.escape, targets)) + ')')

    matrix_data = {domain: set() for domain in targets}

    txt_files = set(glob.glob('results/**/*', recursive=True))
    txt_files = [f for f in txt_files if os.path.isfile(f)]

    print(f"[+] Scanning {len(txt_files)} decrypted data source files...")
    
    for file_path in txt_files:
        filename = os.path.basename(file_path).lower()
        
        if 'secretfinder' in filename:
            source_tool = 'SecretFinder'
        elif 'waybackurls' in filename:
            source_tool = 'Waybackurls'
        elif 'gau' in filename:
            source_tool = 'GAU'
        else:
            source_tool = 'Combined-Engine'

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    url = line.strip()
                    if not url or url.startswith('#'):
                        continue
                    
                    # [★초고속 치트키 2★] 65번 돌던 파이썬 루프를 단 1번의 정규식 검색으로 단축
                    match = domain_pattern.search(url)
                    if match:
                        matched_domain = match.group(1)
                        matrix_data[matched_domain].add((url, source_tool))
        except Exception as e:
            print(f"[-] Error reading {filename}: {e}")

    # 3. 고품격 엑셀 문서 디자인 빌드
    wb = Workbook()
    default_sheet = wb.active

    font_header = Font(name='Malgun Gothic', size=11, bold=True, color='FFFFFF')
    font_body = Font(name='Malgun Gothic', size=10, bold=False)
    fill_header = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    align_center = Alignment(horizontal='center', vertical='center')
    align_left = Alignment(horizontal='left', vertical='center')

    sheets_created = 0

    print("[+] Injecting data into Excel sheets with real-time optimization...")
    for domain, dataset in matrix_data.items():
        if not dataset:
            continue
            
        safe_tab_name = domain[:30]
        ws = wb.create_sheet(title=safe_tab_name)
        sheets_created += 1

        headers = ["No", "Target URL / Endpoint (수집된 자산 주소)", "Source Tool (발견 도구)"]
        ws.append(headers)

        ws.row_dimensions[1].height = 26
        for col_num, header_text in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_center

        sorted_dataset = sorted(list(dataset), key=lambda x: (x[1], x[0]))
        
        max_len_no = len("No")
        max_len_url = len("Target URL / Endpoint (수집된 자산 주소)")
        max_len_tool = len("Source Tool (발견 도구)")
        
        for idx, (url, tool) in enumerate(sorted_dataset, 1):
            if idx > 1048500: # 엑셀 규격 한계 초과 방지
                break
                
            ws.append([idx, url, tool])
            current_row = ws.max_row
            ws.row_dimensions[current_row].height = 20
            
            ws.cell(row=current_row, column=1).font = font_body
            ws.cell(row=current_row, column=1).alignment = align_center
            ws.cell(row=current_row, column=2).font = font_body
            ws.cell(row=current_row, column=2).alignment = align_left
            ws.cell(row=current_row, column=3).font = font_body
            ws.cell(row=current_row, column=3).alignment = align_center

            max_len_no = max(max_len_no, len(str(idx)))
            max_len_url = max(max_len_url, len(str(url)))
            max_len_tool = max(max_len_tool, len(str(tool)))

        # 자동 필터 영역 적용
        max_row = ws.max_row
        ws.auto_filter.ref = f"A1:C{max_row}"

        ws.column_dimensions['A'].width = max_len_no + 3
        ws.column_dimensions['B'].width = max(min(max_len_url + 3, 90), 10)
        ws.column_dimensions['C'].width = max_len_tool + 3

    if sheets_created > 0:
        wb.remove(default_sheet)
        os.makedirs('reports', exist_ok=True)
        report_path = 'reports/passive_recon_report_v1.xlsx'
        wb.save(report_path)
        print(f"[+] [SUCCESS] Advanced filtered report generated at: {report_path}")
    else:
        print("[-] Error: Scan results were empty. Excel file not created.")

if __name__ == '__main__':
    build_advanced_excel_report()
