#!/usr/bin/env python3
import os
import glob
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_advanced_excel_report():
    print("[+] Initializing Modern Premium Excel Dashboard Engine...", flush=True)
    if not os.path.exists('targets.txt'):
        print("[-] Error: targets.txt missing.", flush=True)
        return
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f if line.strip()]

    matrix_data = {domain: {} for domain in targets}
    txt_files = glob.glob('results/**/*.*', recursive=True) + glob.glob('results/*.*')
    txt_files = [f for f in txt_files if os.path.isfile(f)]

    if not txt_files:
        print("[-] Warning: No decrypted text files found in results/ folder. Generating empty dashboard entries.", flush=True)

    # 1. 원천 데이터 파싱 및 매트릭스 구성
    for file_path in txt_files:
        filename = os.path.basename(file_path).lower()
        if 'linkfinder' in filename or 'jsluice' in filename: source_tool = 'LinkFinder'
        elif 'trufflehog' in filename: source_tool = 'TruffleHog'
        elif 'waybackurls' in filename: source_tool = 'Waybackurls'
        elif 'gau' in filename: source_tool = 'GAU'
        else: continue

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    url = line.strip()
                    if not url or url.startswith('#'): continue
                    
                    # openpyxl IllegalCharacterError 방지를 위한 XML 제어 문자 제거
                    url = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', url)
                    if not url: continue
                    
                    for domain in targets:
                        if domain in url or domain in filename:
                            if url not in matrix_data[domain]:
                                matrix_data[domain][url] = set()
                            matrix_data[domain][url].add(source_tool)
                            break
        except Exception as e:
            print(f"[-] Error reading {filename}: {e}", flush=True)

    # 2. 엑셀 워크북 생성 및 스타일 정의
    wb = Workbook()
    
    # 스타일 공통 정의
    font_header = Font(name='Malgun Gothic', size=11, bold=True, color='FFFFFF')
    fill_header = PatternFill(start_color='2F3542', end_color='2F3542', fill_type='solid') # 딥 차콜네이비
    fill_zebra = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')  # 연한 지브라 그레이
    fill_summary = PatternFill(start_color='E9ECEF', end_color='E9ECEF', fill_type='solid') # 하단 합계 음영
    
    font_data = Font(name='Malgun Gothic', size=10, color='333333')
    font_summary = Font(name='Malgun Gothic', size=11, bold=True, color='000000')
    
    align_center = Alignment(horizontal='center', vertical='center')
    align_left = Alignment(horizontal='left', vertical='center')
    align_right = Alignment(horizontal='right', vertical='center')
    
    # 격자 테두리선 설정
    thin_side = Side(border_style="thin", color="E0E0E0")
    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    
    double_bottom_side = Side(border_style="double", color="2F3542")
    summary_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=double_bottom_side)

    # ==========================================
    # 3. Summary Dashboard 시트 설계
    # ==========================================
    ws_dash = wb.active
    ws_dash.title = "Summary Dashboard"
    
    dash_headers = ["No", "Target Domain", "Total URLs (Wayback/GAU)", "jsluice 추출 개수", "TruffleHog 탐지 개수"]
    ws_dash.append(dash_headers)
    ws_dash.row_dimensions[1].height = 28
    
    for col_num, header in enumerate(dash_headers, 1):
        cell = ws_dash.cell(row=1, column=col_num)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = thin_border

    # ==========================================
    # 4. High Risk Targets 시트 설계 (Source Tool 위치 변경)
    # ==========================================
    ws_high = wb.create_sheet(title="High Risk Targets")
    high_headers = ["No", "Source Tool", "Domain", "High Risk URL / Endpoint", "Risk Reason"] # Source Tool을 2번째로 이동
    ws_high.append(high_headers)
    ws_high.row_dimensions[1].height = 28
    
    for col_num, header in enumerate(high_headers, 1):
        cell = ws_high.cell(row=1, column=col_num)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = thin_border

    high_risk_keywords = ['config', '.env', 'xml', 'json', 'secret', 'api/v', 'token', 'admin', 'password', 'key', 'credential', 'mysql']
    dash_idx = high_risk_idx = 2  
    sheets_created = 0

    # 데이터 채우기 루프
    for domain, url_map in matrix_data.items():
        if not url_map:
            passive_url_count = 0
            jsluice_count = 0
            trufflehog_count = 0
        else:
            passive_url_count = sum(1 for url, tools in url_map.items() if 'Waybackurls' in tools or 'GAU' in tools)
            jsluice_count = sum(1 for url, tools in url_map.items() if 'LinkFinder' in tools)
            trufflehog_count = sum(1 for url, tools in url_map.items() if 'TruffleHog' in tools)
        
        # 대시보드 행 삽입
        ws_dash.append([dash_idx - 1, domain, passive_url_count, jsluice_count, trufflehog_count])
        ws_dash.row_dimensions[dash_idx].height = 22
        
        # 대시보드 셀 스타일링 및 하이퍼링크 구현
        for col_num in range(1, 6):
            cell = ws_dash.cell(row=dash_idx, column=col_num)
            cell.font = font_data
            cell.border = thin_border
            if (dash_idx % 2) == 1: cell.fill = fill_zebra
            
            if col_num in [1, 2]:
                cell.alignment = align_center if col_num == 1 else align_left
                # [요구사항 반영] 데이터가 존재하는 도메인만 상세 시트로 바로가기 링크 생성
                if col_num == 2 and url_map:
                    cell.hyperlink = f"#'{domain[:30]}'!A1"
                    cell.font = Font(name='Malgun Gothic', size=10, color='0056B3', underline='single') # 고급형 블루 링크 포맷
            else:
                cell.alignment = align_right
                cell.number_format = '#,##0'
                
        dash_idx += 1

        if not url_map: continue

        # 개별 도메인 탭 추가 및 정밀 내역 수립 (Source Tool 위치 변경)
        ws = wb.create_sheet(title=domain[:30])
        sheets_created += 1
        ws.append(["No", "Source Tool", "Target URL / Endpoint"]) # Source Tool을 2번째로 이동
        ws.row_dimensions[1].height = 28
        for col_num in range(1, 4):
            cell = ws.cell(row=1, column=col_num)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_center
            cell.border = thin_border

        for sub_idx, (url, tools) in enumerate(sorted(url_map.items()), 1):
            if sub_idx > 1048500: break
            tools_str = ", ".join(sorted(list(tools)))
            ws.append([sub_idx, tools_str, url]) # 데이터 삽입 순서 조정
            
            row_num = sub_idx + 1
            ws.row_dimensions[row_num].height = 20
            for c in range(1, 4):
                cell = ws.cell(row=row_num, column=c)
                cell.font = font_data
                cell.border = thin_border
                if (row_num % 2) == 1: cell.fill = fill_zebra
                cell.alignment = align_center if c != 3 else align_left # URL 열만 좌측 정렬

            # 하이 리스크 필터링 가동
            is_high_risk = False
            reason = ""
            if 'TruffleHog' in tools:
                is_high_risk = True
                reason = "TruffleHog 검증 완료 핵심 민감 키(Secret) 유출 징후"
            else:
                matched_keys = [key for key in high_risk_keywords if key in url.lower()]
                if matched_keys:
                    is_high_risk = True
                    reason = f"민감 키워드 파라미터 감지 ({', '.join(matched_keys)})"
                    
            if is_high_risk:
                ws_high.append([high_risk_idx - 1, tools_str, domain, url, reason]) # 데이터 삽입 순서 조정
                ws_high.row_dimensions[high_risk_idx].height = 22
                for c in range(1, 6):
                    cell = ws_high.cell(row=high_risk_idx, column=c)
                    cell.font = font_data
                    cell.border = thin_border
                    if (high_risk_idx % 2) == 1: cell.fill = fill_zebra
                    cell.alignment = align_left if c in [3, 4, 5] else align_center # 가독성에 최적화된 맞춤 정렬
                high_risk_idx += 1

    # ==========================================
    # 5. Dashboard 최하단 자동 Total(합계) 행 연산부
    # ==========================================
    if dash_idx > 2:
        ws_dash.append([
            "Total", 
            f"{dash_idx - 2} 개 도메인 스캔 완료", 
            f"=SUM(C2:C{dash_idx-1})", 
            f"=SUM(D2:D{dash_idx-1})", 
            f"=SUM(E2:E{dash_idx-1})"
        ])
        ws_dash.row_dimensions[dash_idx].height = 26
        for col_num in range(1, 6):
            cell = ws_dash.cell(row=dash_idx, column=col_num)
            cell.font = font_summary
            cell.fill = fill_summary
            cell.border = summary_border
            if col_num in [1, 2]:
                cell.alignment = align_center if col_num == 1 else align_left
            else:
                cell.alignment = align_right
                cell.number_format = '#,##0'

    # ==========================================
    # 6. 전 시트 자동 열 너비(Width) 맞춤 최적화 알고리즘
    # ==========================================
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value:
                    val_str = str(cell.value)
                    if not val_str.startswith('='):
                        cell_len = sum(2 if ord(char) > 128 else 1 for char in val_str)
                        if cell_len > max_len: max_len = cell_len
            sheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # 지정 수치 보정 고정폭 세팅 (가독성 확보)
    ws_dash.column_dimensions['A'].width = 10
    ws_dash.column_dimensions['B'].width = 35
    ws_dash.column_dimensions['C'].width = 26
    ws_dash.column_dimensions['D'].width = 22
    ws_dash.column_dimensions['E'].width = 22

    # 결과 디렉토리 생성 및 파일 저장
    os.makedirs('reports', exist_ok=True)
    wb.save('reports/passive_recon_report_v1.xlsx')
    print("[+] [SUCCESS] Premium Multi-Tab Excel Document Successfully Constructed.", flush=True)

if __name__ == '__main__':
    build_advanced_excel_report()
