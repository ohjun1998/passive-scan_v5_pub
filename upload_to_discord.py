#!/usr/bin/env python3
import os
import glob
import zipfile
import requests

def upload_report_safe_engine():
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("[-] Error: DISCORD_WEBHOOK_URL variable is missing.")
        return

    # 1. 최신 엑셀 보고서 탐색
    files = glob.glob('reports/passive_recon_report_v*.xlsx')
    if not files:
        print("[-] Error: No excel report found in reports/ folder.")
        return
    
    latest_file = max(files, key=os.path.getmtime)
    file_name = os.path.basename(latest_file)
    
    # 2. 고강도 ZIP 압축 실행 (용량 다이어트)
    zip_file_name = file_name.replace('.xlsx', '.zip')
    zip_file_path = os.path.join('reports', zip_file_name)
    
    print(f"[+] Compressing {file_name} with maximum ZIP efficiency...")
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(latest_file, arcname=file_name)
        
    compressed_size = os.path.getsize(zip_file_path)
    print(f"[+] Compression complete: {compressed_size / 1024 / 1024:.2f} MB")

    DISCORD_LIMIT = 9.5 * 1024 * 1024 # 안전 전송 마지노선 (9.5MB)

    # -----------------------------------------------------------------
    # [Case 1] 압축 결과가 9.5MB 이하인 경우 -> 통째로 단일 파일 직송
    # -----------------------------------------------------------------
    if compressed_size <= DISCORD_LIMIT:
        print("[+] Compressed file is within Discord limits. Transmitting natively...")
        with open(zip_file_path, 'rb') as f:
            payload = {
                'content': f"🚀 **[정찰 완료 - 마스터 보고서]**\n🔒 보안 압축 파일이 안전하게 직송되었습니다.\n📅 원본 파일명: `{file_name}`"
            }
            files_payload = {'file': (zip_file_name, f, 'application/zip')}
            response = requests.post(webhook_url, data=payload, files=files_payload)
            
        if response.status_code in [200, 204]:
            print("[+] [SUCCESS] Native Discord transmission complete!")
        else:
            print(f"[-] Discord error: {response.status_code}, {response.text}")

    # -----------------------------------------------------------------
    # [🔥Case 2 개조] 9.5MB 초과 시 -> 안내 가이드 선발송 후 파일 조각만 낱개 사출
    # -----------------------------------------------------------------
    else:
        print("[!] Warning: Compressed size exceeds limit. Activating Split-by-Instruction mode...")
        
        # 명령어 양식 본문 정의
        cmd_win = f"copy /b {zip_file_name}.part* {zip_file_name}"
        cmd_mac = f"cat {zip_file_name}.part* > {zip_file_name}"
        
        # 1단계: 사용법 및 안내 양식 메시지를 디스코드방에 '딱 1번' 먼저 발송
        guide_payload = {
            'content': (
                f"📦 **[대용량 분할 사출] 마스터 보고서 안내 가이드라인**\n"
                f"⚠️ 최종 엑셀 리포트 용량이 너무 커서 조각 파일들로 분할되어 들어옵니다.\n\n"
                f"🛠️ **병합 및 복원 방법:**\n"
                f"뒤이어 전송되는 모든 파트 파일(`.part1` ~ `.partN`)을 **동일한 단일 폴더에 전부 다운로드**한 뒤, 터미널(콘솔)을 열어 아래 명령어를 복사·붙여넣기 하세요.\n"
                f"```cmd\n"
                f"※ Windows (CMD 환경):\n{cmd_win}\n\n"
                f"※ Mac / Linux (터미널 환경):\n{cmd_mac}\n"
                f"```"
            )
        }
        
        print("[+] Sending integration guide header message first...", flush=True)
        requests.post(webhook_url, data=guide_payload)
        
        # 2단계: 파일 조각들을 루프 돌며 '순수 첨부파일'만 낱개 메시지로 후속 사출
        part_num = 1
        with open(zip_file_path, 'rb') as f:
            while True:
                chunk = f.read(int(DISCORD_LIMIT))
                if not chunk:
                    break
                
                chunk_name = f"{zip_file_name}.part{part_num}"
                print(f"[+] Launching segment asset file: {chunk_name}", flush=True)
                
                # 본문 메시지는 파일명만 나오게 최소화하여 총 페이로드 용량을 9.5MB 선으로 통제
                file_payload = {
                    'content': f"📎 **마스터 보고서 파일 조각 ➔ Part {part_num}**"
                }
                files_payload = {'file': (chunk_name, chunk, 'application/octet-stream')}
                
                # 개별 전송 (각각 독립된 메시지이므로 25MB 한계에 절대 걸리지 않음)
                requests.post(webhook_url, data=file_payload, files=files_payload)
                part_num += 1
                
        print("[+] [SUCCESS] Split transmission complete without 413 payload error!", flush=True)

if __name__ == '__main__':
    upload_report_safe_engine()
