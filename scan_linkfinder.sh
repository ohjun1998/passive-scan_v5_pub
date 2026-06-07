#!/bin/bash
mkdir -p results
GROUP_SUFFIX=$1

split -d -n l/4 targets.txt targets_group
TARGET_FILE="targets_group${GROUP_SUFFIX}"

scan_jsluice() {
    local domain=$(echo "$1" | xargs)
    [[ -z "$domain" || "$domain" =~ ^# ]] && return

    # 1단계에서 고스란히 상속받은 마스터 JS 주소록 로드
    local master_list="results/${domain}_js_master_list.txt"

    if [ -s "$master_list" ]; then
        echo "[+] [$domain] [Stage 2: jsluice Worker] Analyzing streaming JS data (0% Duplicate Recon)..."
        head -n 100 "$master_list" > "results/${domain}_js_temp.txt"

        while read -r url; do
            # 아카이브 호출 없이, 주소록에 적힌 JS 소스코드를 즉시 파이프로 엮어 메모리 스캔
            curl -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "$url" 2>/dev/null | jsluice urls 2>/dev/null >> "results/${domain}_jsluice_raw.json"
            sleep 0.5
        } < "results/${domain}_js_temp.txt"

        if [ -s "results/${domain}_jsluice_raw.json" ]; then
            # 기존 엑셀 리포터 호환을 위해 파일명을 _linkfinder.txt 로 복원 사출
            cat "results/${domain}_jsluice_raw.json" | jq -r '.url' 2>/dev/null | sort -u > "results/${domain}_linkfinder.txt"
            rm -f "results/${domain}_jsluice_raw.json"
        fi
        rm -f "results/${domain}_js_temp.txt"
    else
        echo "  -> [$domain] No JS assets found from Stage 1 Index."
    fi
}

export -f scan_jsluice
echo "[*] Launching Stage 2 jsluice (LinkFinder) Analyzer Matrix for $TARGET_FILE..."
xargs -P 5 -n 1 -a "$TARGET_FILE" -I {} bash -c 'scan_jsluice "{}"'

rm -f targets_group*
