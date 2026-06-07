#!/bin/bash
mkdir -p results
GROUP_SUFFIX=$1

split -d -n l/4 targets.txt targets_group
TARGET_FILE="targets_group${GROUP_SUFFIX}"

collect_master() {
    local domain=$(echo "$1" | xargs)
    [[ -z "$domain" || "$domain" =~ ^# ]] && return

    echo "[+] [$domain] [Stage 1: Collector] Fetching passive URLs from APIs..."
    
    # 1. 아카이브 API 원천 징수 및 원본 백업 (엑셀 리포터 분석용)
    echo "$domain" | gau > "results/${domain}_gau.txt" 2>/dev/null
    sort -u "results/${domain}_gau.txt" -o "results/${domain}_gau.txt"

    echo "$domain" | waybackurls > "results/${domain}_waybackurls.txt" 2>/dev/null
    sort -u "results/${domain}_waybackurls.txt" -o "results/${domain}_waybackurls.txt"

    # 2. 두 파일에서 중복 없는 깨끗한 순수 .js 목록만 추출하여 마스터 주소록 생성 (2단계 전송용)
    cat "results/${domain}_gau.txt" "results/${domain}_waybackurls.txt" 2>/dev/null | grep -E '\.js($|\?)' 2>/dev/null | sort -u > "results/${domain}_js_master_list.txt"
    
    echo "  -> [$domain] Successfully indexed $(wc -l < "results/${domain}_js_master_list.txt") unique JS targets."
}

export -f collect_master
echo "[*] Launching Stage 1 Master URL Collector Matrix for $TARGET_FILE..."
xargs -P 10 -n 1 -a "$TARGET_FILE" -I {} bash -c 'collect_master "{}"'

rm -f targets_group*
