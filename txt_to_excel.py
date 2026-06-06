#!/usr/bin/env python3
import os
import datetime
import re 
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from urllib.parse import urlparse, parse_qsl, quote
from collections import defaultdict

# 6대 탐지 지표 기반 가중치 스코어링 엔진
def calculate_url_risk(url):
    score = 0
    categories = []

    noise_patterns = [
        r'/node_modules/', r'/wp-includes/', r'/assets/vendor/', 
        r'jquery', r'bootstrap', r'/fonts/', r'/licenses/', 
        r'cdnjs\.cloudflare', r'/react/static/', r'debug\.[a-f0-9]+\.js'
    ]
    if any(re.search(p, url, re.I) for p in noise_patterns):
        return 0, []

    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parsed.query.lower()
    netloc = parsed.netloc.lower()

    critical_subdomains = ['api', 'auth', 'login', 'admin', 'gw', 'vpn', 'master', 'manager', 'console']
    subdomain = netloc.split('.')[0]
    if subdomain in critical_subdomains:
        score += 3
        categories.append("Critical Asset")

    if any(k in path or k in query for k in ['admin', 'manage', 'master', 'system', 'sys', 'dashboard', 'console', 'control', 'root', 'wp-admin']):
        score += 4
        categories.append("Admin/Control")
    if any(k in path or k in query for k in ['cmd', 'exec', 'run', 'ping', 'execute']):
        score += 5
        categories.append("Command Exec")

    if any(k in path or k in query for k in ['upload', 'fileupload', 'write', 'attach', 'attachment']):
        score += 4
        categories.append("File Upload")
    if any(k in path or k in query for k in ['file', 'path', 'download', 'doc', 'document', 'filepath']):
        score += 3
        categories.append("File Download")
    if any(k in path for k in ['api', 'v1', 'v2', 'v3', 'rest', 'graphql']):
        score += 2
        categories.append("API Endpoint")
    if any(k in path or k in query for k in ['delete', 'update', 'modify', 'remove', 'change-password', 'reset-password']):
        score += 4
        categories.append("Destructive Action")

    if any(k in path or k in query or url.endswith(k) for k in ['.bak', '.old', '.sql', '.log', '.env', '.git', 'config', 'setup', 'phpinfo', 'debug', 'test']):
        score += 5
        categories.append("Config/Leak")

    if any(k in query for k in ['url=', 'uri=', 'redirect=', 'next=', 'return=', 'callback=', 'host=', 'dest=']):
        score += 4
        categories.append("SSRF/Redirect")

    params = parse_qsl(parsed.query)
    param_count = len(params)
    if param_count > 0:
        score += 2
        if param_count >= 4:
            score += 2
            categories.append("Complex Logic")

        for k, v in params:
            if v.isdigit():
                score += 2
                if "IDOR/SQLi Suspect" not in categories:
                    categories.append("IDOR/SQLi Suspect")
            if v.startswith('http://') or v.startswith('https://') or 'www.' in v:
                score += 3
                if "SSRF Suspect" not in categories:
                    categories.append("SSRF Suspect")
            if len(v) >= 32 and re.match(r'^[a-f0-9]+$', v, re.I):
                score += 1
                if "Token/Session Suspect" not in categories:
                    categories.append("Token/Session Suspect")

    return score, list(set(categories))

def create_excel_report():
    wb = openpyxl.Workbook()
    font_family = "Segoe UI"
    header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
    title_font = Font(name=font_family, size=16, bold=True, color="1F497D")
    section_font = Font(name=font_family, size=12, bold=True, color="2B4C7E")
    body_font = Font(name=font_family, size=10, color="000000")
    bold_body_font = Font(name=font_family, size=10, bold=True, color="000000")
    link_font = Font(name=font_family, size=10, color="0563C1", underline="single")
    back_link_font = Font(name=font_family, size=10, color="0563C1", underline="single", bold=True)
    red_body_font = Font(name=font_family, size=10, color="C00000", bold=True)
    green_bold_font = Font(name=font_family, size=10, color="008000", bold=True)
    child_body_font = Font(name=font_family, size=10, color="7F7F7F", italic=True)
    hr_title_font = Font(name=font_family, size=16, bold=True, color="9C0006")
    hr_header_fill = PatternFill(start_color="9C0006", end_color="9C0006", fill_type="solid")
    hr_link_font = Font(name=font_family, size=10, color="9C0006", underline="single")
    header_fill = PatternFill(start_color="2B4C7E", end_color="2B4C7E", fill_type="solid")
    tab_hdr_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    zebra_fill = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")
    thin_border = Border(left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
                         top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9'))
    double_bottom_border = Border(top=Side(style='thin', color='D9D9D9'), bottom=Side(style='double', color='000000'))

    ws_summary = wb.active
    ws_summary.title = "Summary Dashboard"
    ws_summary.views.sheetView[0].showGridLines = True
    ws_summary["B2"] = "Passive Reconnaissance Scan Report"
    ws_summary["B2"].font = title_font
    ws_summary["B3"] = f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws_summary["B3"].font = Font(name=font_family, size=10, italic=True, color="595959")
    
    headers_summary = ["No", "Target Domain", "Total Unique URLs", "Newly Added", "Status"]
    for col_idx, text in enumerate(headers_summary, start=2):
        cell = ws_summary.cell(row=5, column=col_idx, value=text)
        cell.font = header_font; cell.fill = header_fill; cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_summary.row_dimensions[5].height = 25

    ws_high_risk = wb.create_sheet(title="High-Risk Targets", index=1)
    ws_high_risk.views.sheetView[0].showGridLines = True
    ws_high_risk["B2"] = "🔥 High-Risk Vulnerability Suspect Targets (Scored)"
    ws_high_risk["B2"].font = hr_title_font
    ws_high_risk["B3"] = "3중 초병렬 분산 스캔 데이터를 완벽 취합 및 점수화하여 정렬한 리스트입니다."
    ws_high_risk["B3"].font = Font(name=font_family, size=10, italic=True, color="595959")
    
    headers_hr = ["No", "Target Domain", "Identified High-Risk URL", "Risk Score", "Suspect Categories", "Source Tools"]
    for col_idx, text in enumerate(headers_hr, start=2):
        cell = ws_high_risk.cell(row=5, column=col_idx, value=text)
        cell.font = header_font; cell.fill = hr_header_fill; cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_high_risk.row_dimensions[5].height = 25

    targets_file = "targets.txt"
    target_dir = "results"
    output_dir = "reports"
    base_name = "passive_recon_report"
    extension = ".xlsx"
    
    if not os.path.exists(targets_file): return

    domains = []
    with open(targets_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip().replace('\r', '')
            if line and not line.startswith('#'): domains.append(line)

    def get_root_domain(dom):
        parts = dom.lower().split('.')
        if len(parts) >= 3 and parts[-2] in ['co', 'or', 're', 'pe', 'go', 'ne', 'ac', 'kyonggi']:
            return '.'.join(parts[-3:])
        return '.'.join(parts[-2:])

    sorted_domains = sorted(domains, key=lambda x: (get_root_domain(x), x), reverse=True)

    counter = 1
    test_filename = os.path.join(output_dir, f"{base_name}_v{counter}{extension}")
    while os.path.exists(test_filename):
        counter += 1
        test_filename = os.path.join(output_dir, f"{base_name}_v{counter}{extension}")

    prev_counts = {}
    if counter > 1:
        prev_version_file = os.path.join(output_dir, f"{base_name}_v{counter-1}{extension}")
        if os.path.exists(prev_version_file):
            try:
                prev_wb = openpyxl.load_workbook(prev_version_file, data_only=True)
                if "Summary Dashboard" in prev_wb.sheetnames:
                    prev_ws = prev_wb["Summary Dashboard"]
                    for r in range(6, prev_ws.max_row + 1):
                        dom_val = prev_ws.cell(row=r, column=3).value
                        cnt_val = prev_ws.cell(row=r, column=4).value
                        if dom_val and cnt_val is not None: prev_counts[str(dom_val).strip()] = int(cnt_val)
            except Exception as e: print(f"[!] 이전 실적 분석 스킵: {e}")

    row_num = 6
    idx = 1
    global_high_risk_list = []
    
    for domain in sorted_domains:
        # 지정 에러 완벽 해결 변수 배치
        sheet_title = domain[:30]
        
        gau_path = os.path.join(target_dir, f"{domain}_gau.txt")
        wb_path = os.path.join(target_dir, f"{domain}_waybackurls.txt")
        sf_path = os.path.join(target_dir, f"{domain}_secretfinder.txt")
        
        raw_urls = []
        if os.path.exists(gau_path):
            with open(gau_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_urls.extend([line.strip() for line in f if line.strip()])
        if os.path.exists(wb_path):
            with open(wb_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_urls.extend([line.strip() for line in f if line.strip()])
        if os.path.exists(sf_path):
            with open(sf_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_urls.extend([line.strip() for line in f if line.strip()])
        
        raw_urls = list(set(raw_urls))
        has_data = len(raw_urls) > 0
        
        if has_data:
            structure_groups = defaultdict(list)
            for url in raw_urls:
                try:
                    parsed = urlparse(url)
                    path_cleaned = parsed.path
                    path_cleaned = re.sub(r'/[a-f0-9]{8,}', '/{hash}', path_cleaned, flags=re.I)
                    path_cleaned = re.sub(r'([._\-])[a-f0-9]{8,}\.', r'\1{hash}.', path_cleaned, flags=re.I)
                    path_cleaned = re.sub(r'/[0-9]+', '/{num}', path_cleaned)

                    param_keys = tuple(sorted([k for k, _ in parse_qsl(parsed.query)]))
                    structure_key = (parsed.scheme, parsed.netloc, path_cleaned, param_keys)
                    if url not in structure_groups[structure_key]: structure_groups[structure_key].append(url)
                except Exception:
                    if url not in structure_groups[('error', '', url, ())]: structure_groups[('error', '', url, ())].append(url)
            
            url_count = len(structure_groups)
            status_text = "Completed"
        else:
            structure_groups = {}
            url_count = 0
            status_text = "No Data"

        past_count = prev_counts.get(domain, 0)
        newly_added = url_count - past_count
        if newly_added < 0: newly_added = 0

        c_no = ws_summary.cell(row=row_num, column=2, value=idx)
        c_dom = ws_summary.cell(row=row_num, column=3, value=domain)
        c_cnt = ws_summary.cell(row=row_num, column=4, value=url_count)
        c_add = ws_summary.cell(row=row_num, column=5, value=newly_added)
        c_stat = ws_summary.cell(row=row_num, column=6, value=status_text)
        
        c_no.alignment = Alignment(horizontal="center")
        c_cnt.number_format = '#,##0'; c_cnt.alignment = Alignment(horizontal="right")
        c_add.number_format = '#,##0'; c_add.alignment = Alignment(horizontal="right")
        c_stat.alignment = Alignment(horizontal="center")
        
        for c in [c_no, c_dom, c_cnt, c_add, c_stat]:
            c.border = thin_border
            if idx % 2 == 0: c.fill = zebra_fill

        if has_data:
            c_dom.hyperlink = f"#'{sheet_title}'!A1"; c_dom.font = link_font
            c_cnt.font = body_font; c_stat.font = body_font
            c_add.font = green_bold_font if newly_added > 0 else body_font
            
            ws_domain = wb.create_sheet(title=sheet_title)
            ws_domain.views.sheetView[0].showGridLines = True
            ws_domain.sheet_properties.outlinePr.summaryBelow = False
            ws_domain["A1"] = f"Extracted Structural Accordion URLs for: {domain}"
            ws_domain["A1"].font = section_font
            
            c_back = ws_domain.cell(row=1, column=3, value="🏠 대시보드로 이동")
            c_back.hyperlink = "#'Summary Dashboard'!B2"; c_back.font = back_link_font
            c_back.alignment = Alignment(horizontal="center", vertical="center")
            
            headers_domain = ["Index", "Extracted URL / Full Path", "Source Tools"]
            for col_idx, text in enumerate(headers_domain, start=1):
                cell = ws_domain.cell(row=3, column=col_idx, value=text)
                cell.font = header_font; cell.fill = tab_hdr_fill; cell.border = thin_border
                cell.alignment = Alignment(horizontal="center" if col_idx in [1,3] else "left", vertical="center")
            ws_domain.row_dimensions[3].height = 24
            
            current_u_row = 4
            u_idx = 1
            
            for struct_key, url_list in structure_groups.items():
                rep_url = url_list[0]
                risk_score, categories = calculate_url_risk(rep_url)
                if risk_score >= 5: global_high_risk_list.append((risk_score, domain, rep_url, categories))
                
                cell_i = ws_domain.cell(row=current_u_row, column=1, value=u_idx)
                cell_u = ws_domain.cell(row=current_u_row, column=2, value=rep_url)
                cell_s = ws_domain.cell(row=current_u_row, column=3, value="gau, waybackurls, secretfinder")
                
                cell_i.alignment = Alignment(horizontal="center"); cell_s.alignment = Alignment(horizontal="center")
                
                for cell in [cell_i, cell_u, cell_s]:
                    cell.font = body_font; cell.border = thin_border
                    if u_idx % 2 == 0: cell.fill = zebra_fill
                
                if len(url_list) > 1:
                    child_start_row = current_u_row + 1
                    for child_url in url_list[1:6]:
                        current_u_row += 1
                        cell_ci = ws_domain.cell(row=current_u_row, column=1, value="  -")
                        cell_cu = ws_domain.cell(row=current_u_row, column=2, value=child_url)
                        cell_cs = ws_domain.cell(row=current_u_row, column=3, value="gau, waybackurls, secretfinder")
                        
                        cell_ci.alignment = Alignment(horizontal="center")
                        cell_cs.alignment = Alignment(horizontal="center")
                        for cell in [cell_ci, cell_cu, cell_cs]:
                            cell.font = child_body_font; cell.border = thin_border
                            if u_idx % 2 == 0: cell.fill = zebra_fill
                    
                    child_end_row = current_u_row
                    ws_domain.row_dimensions.group(child_start_row, child_end_row, hidden=True)
                
                current_u_row += 1
                u_idx += 1
                        
            for col in ws_domain.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                ws_domain.column_dimensions[get_column_letter(col[0].column)].width = max(max_len + 3, 12)
        else:
            c_dom.font = body_font; c_cnt.font = body_font; c_add.font = body_font; c_stat.font = red_body_font

        row_num += 1
        idx += 1

    for col_idx in range(2, 7): ws_summary.cell(row=row_num, column=col_idx).border = double_bottom_border
    ws_summary.cell(row=row_num, column=3, value="Total Unique URLs Across Targets").font = bold_body_font
    ws_summary.cell(row=row_num, column=4, value=f"=SUM(D6:D{row_num-1})").font = bold_body_font
    ws_summary.cell(row=row_num, column=4).alignment = Alignment(horizontal="right")
    ws_summary.cell(row=row_num, column=4).number_format = '#,##0'
    ws_summary.cell(row=row_num, column=5, value=f"=SUM(E6:E{row_num-1})").font = bold_body_font
    ws_summary.cell(row=row_num, column=5).alignment = Alignment(horizontal="right")
    ws_summary.cell(row=row_num, column=5).number_format = '#,##0'

    for col in ws_summary.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws_summary.column_dimensions[get_column_letter(col[0].column)].width = max(max_len + 4, 12)

    global_high_risk_list.sort(key=lambda x: x[0], reverse=True)
    hr_row_num = 6
    for hr_idx, (score, dom, hr_url, categories) in enumerate(global_high_risk_list, start=1):
        hc_no = ws_high_risk.cell(row=hr_row_num, column=2, value=hr_idx)
        hc_dom = ws_high_risk.cell(row=hr_row_num, column=3, value=dom)
        hc_url = ws_high_risk.cell(row=hr_row_num, column=4, value=hr_url)
        hc_score = ws_high_risk.cell(row=hr_row_num, column=5, value=score)
        hc_cat = ws_high_risk.cell(row=hr_row_num, column=6, value=", ".join(categories) if categories else "General Param")
        hc_src = ws_high_risk.cell(row=hr_row_num, column=7, value="gau, waybackurls, secretfinder")
        
        hc_no.alignment = Alignment(horizontal="center")
        hc_score.alignment = Alignment(horizontal="center")
        hc_cat.alignment = Alignment(horizontal="left")
        hc_src.alignment = Alignment(horizontal="center")
        hc_score.font = red_body_font if score >= 10 else bold_body_font

        try:
            safe_url = quote(hr_url, safe=':/?&=#~+,-;*@()[]')
            if len(safe_url) <= 2000:
                hc_url.hyperlink = safe_url; hc_url.font = hr_link_font
            else: hc_url.font = body_font
        except Exception: hc_url.font = body_font
        
        hc_dom.hyperlink = f"#'{dom[:30]}'!A1"; hc_dom.font = link_font
        
        for c in [hc_no, hc_dom, hc_url, hc_score, hc_cat, hc_src]:
            c.border = thin_border
            if hr_idx % 2 == 0: c.fill = zebra_fill
            if c != hc_dom and c != hc_url and c != hc_score: c.font = body_font
        hr_row_num += 1

    if hr_row_num > 6: ws_high_risk.auto_filter.ref = f"B5:G{hr_row_num-1}"

    for col in ws_high_risk.columns:
        if col[0].column >= 2 and col[0].column <= 7:
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws_high_risk.column_dimensions[get_column_letter(col[0].column)].width = max(max_len + 4, 12)

    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"{base_name}_v{counter}{extension}")
    wb.save(output_filename)
    print(f"\n[+] 3중 분산 취합 보고서 사출 완료: {output_filename}")

if __name__ == "__main__":
    create_excel_report()
