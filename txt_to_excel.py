#!/usr/bin/env python3
import os
import glob
import urllib.parse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

def build_advanced_excel_report():
    print("[+] Initializing Intelligent Excel Reporter Engine...", flush=True)
    
    # 1. 마스터 타깃 목록 로드 (탭 분할 기준점)
    if not os.path.exists('targets.txt'):
        print("[-] Error: targets.txt missing.", flush=True)
        return
        
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f if line.strip()]

    # 도메인별 데이터 구조화
    matrix_data = {domain: set() for domain in targets}

    # 2. 12대 가상머신 데이터 전수조사
    txt_files = glob.glob('results/**/*.*', recursive=True) + glob.glob('results/*.*')
    txt_files = [f for f in txt_files if os.path.isfile(f)]

    if not txt_files:
        print("[-] Warning: No decrypted text files found in results/ folder.", flush=True)
        return

    print(f"[+] Processing {len(txt_files)} data source files...", flush=True)
    
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
                    
                    for domain in targets:
                        if domain in url:
                            matrix_data[domain].add((url, source_tool))
                            break
        except Exception as e:
            print(f"[-] Error reading {filename}: {e}", flush=True)

    # 3. 고속 초경량 엑셀 빌더 스테이지
    print("[+] Compiling pure grid data into Excel sheets...", flush=True)
    wb = Workbook()
    default_sheet = wb.active

    # 상단 헤더 전용 스타일 (시트당 딱 1번만 실행되므로 부하 0%)
    font_header = Font(name='Malgun Gothic', size=11, bold=True, color='FFFFFF')
    fill_header = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    align_center = Alignment(horizontal='center', vertical='center')

    sheets_created = 0

    for domain, dataset in matrix_data.items():
        if not dataset:
            continue  
            
        safe_tab_name = domain[:30]
        ws = wb.create_sheet(title=safe_tab_name)
        sheets_created += 1

        # 타이틀 디자인 빌드 (딱 1번만 수행)
        headers = ["No", "Target URL / Endpoint (수집된 자산 주소)", "Source Tool (발견 도구)"]
        ws.append(headers)
        ws.row_dimensions[1].height = 26
        for col_num in range(1, 4):
            cell = ws.cell(row=1, column=col_num)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_center

        # 본문 데이터 고속 사출 (★초고속 치트키: 개별 셀 폰트/스타일/행높이 세팅 코드를 완벽히 삭제★)
        sorted_dataset = sorted(list(dataset), key=lambda x: (x[1], x[0]))
        for idx, (url, tool) in enumerate(sorted_dataset, 1):
            if idx > 1048500: 
                break
            ws.append([idx, url, tool]) # 메모리 연산 없이 리스트 그대로 고속 직송

        # 고정 레이아웃 가로폭 지정 (시트당 마지막에 딱 1번만 적용하므로 부하 0%)
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 85
        ws.column_dimensions['C'].width = 18

    # 4. 파일 세이빙 마무리
    if sheets_created > 0:
        wb.remove(default_sheet) 
        os.makedirs('reports', exist_ok=True)
        report_path = 'reports/passive_recon_report_v1.xlsx'
        wb.save(report_path)
        print(f"[+] [SUCCESS] Clean lightweight report generated at: {report_path}", flush=True)
    else:
        print("[-] Error: Scan results were empty. Excel file not created.", flush=True)

if __name__ == '__main__':
    build_advanced_excel_report()
