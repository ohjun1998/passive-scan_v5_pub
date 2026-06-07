#!/usr/bin/env python3
import os
import glob
import zipfile
import requests
from openpyxl import load_workbook

def upload_report_safe_engine():
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("[-] Error: DISCORD_WEBHOOK_URL variable is missing.")
        return

    # 최신 생성된 단일 마스터 엑셀 리포트 탐색
    files = glob.glob('reports/passive_recon_report_v*.xlsx')
    if not files:
        print("[-] Error: No Excel report asset found in reports/ folder.")
        return
    
    latest_file = max(files, key=os.path.getmtime)
    file_name = os.path.basename(latest_file)
    
    # [개수 오류 동적 해결] openpyxl을 통해 실제 유효 데이터가 삽입된 상세 시트 수 계산
    try:
        wb = load_workbook(latest_file, read_only=True)
        # 공통 기본 시트(Summary Dashboard, High Risk Targets) 2개를 제외한 순수 활성 도메인 수 연산
        total_sheets = len(wb.sheetnames)
        active_domains_count = total_sheets - 2
        if active_domains_count < 0: active_domains_count = 0
    except Exception as e:
        print(f"[-] Warning: Failed to parse excel sheet count: {e}")
        active_domains_count = "정상"

    # 디스코드 전송 전 ZIP 압축으로 초경량화
    zip_file_name = file_name.replace('.xlsx', '.zip')
    zip_file_path = os.path.join('reports', zip_file_name)
    
    print(f"[+] Compressing {file_name} for maximum transmission efficiency...", flush=True)
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(latest_file, arcname=file_name)
        
    print(f"[+] Transmitting master tabbed workbook packet to Discord...", flush=True)
    with open(zip_file_path, 'rb') as f:
        payload = {
            'content': (
                f"🚀 **[정찰 완료 - 통합 마스터 엑셀 보고서]**\n"
                f"🔒 수집 데이터가 존재하는 **{active_domains_count}개 도메인**이 개별 탭(시트)으로 완벽히 매핑되어 병합되었습니다.\n"
                f"📊 첫 번째 `Dashboard`와 `High Risk Targets` 시트를 통해 기밀 유출 징후를 즉시 파악해 보세요!"
            )
        }
        files_payload = {'file': (zip_file_name, f, 'application/zip')}
        response = requests.post(webhook_url, data=payload, files=files_payload)
        
    if response.status_code in [200, 204]:
        print("[+] [SUCCESS] Native single-packet Discord transmission complete!", flush=True)
    else:
        print(f"[-] Discord error code: {response.status_code}, {response.text}", flush=True)

if __name__ == '__main__':
    upload_report_safe_engine()
