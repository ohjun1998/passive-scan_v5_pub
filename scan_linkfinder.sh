#!/bin/bash
mkdir -p results
GROUP_SUFFIX=$1

split -d -n l/20 targets.txt targets_group
TARGET_FILE="targets_group${GROUP_SUFFIX}"

scan_jsluice() {
    local raw_domain=$(echo "$1" | xargs)
    [[ -z "$raw_domain" || "$raw_domain" =~ ^# ]] && return

    # 와일드카드 매핑 파일명 식별
    local safe_domain="$raw_domain"
    if [[ "$raw_domain" == \** ]]; then
        safe_domain="wild_${raw_domain#\*.}"
    fi

    local download_dir="results/${safe_domain}_js_files"

    if [ -d "$download_dir" ] && [ "$(ls -A "$download_dir" 2>/dev/null)" ]; then
        echo "[+] [${raw_domain}] [2단계: jsluice] 확보된 파일에서 숨겨진 API 경로를 뜯어냅니다..."
        
        rm -f "results/${safe_domain}_jsluice_raw.txt"
        touch "results/${safe_domain}_jsluice_raw.txt"

        for js_file in "$download_dir"/*.js; do
            [ -f "$js_file" ] || continue
            local fname=$(basename "$js_file")
            
            jsluice urls "$js_file" 2>/dev/null | jq -r --arg f "$fname" '.url | "\($f)\t\(.)"' >> "results/${safe_domain}_jsluice_raw.txt" || true
        done

        if [ -s "results/${safe_domain}_jsluice_raw.txt" ]; then
            sort -u "results/${safe_domain}_jsluice_raw.txt" > "results/${safe_domain}_linkfinder.txt"
            rm -f "results/${safe_domain}_jsluice_raw.txt"
            echo "  -> [추출 완료] 소스코드 내부에서 숨겨진 주소 $(wc -l < "results/${safe_domain}_linkfinder.txt") 개를 찾아냈습니다."
        else
            echo "  -> [알림] 숨겨진 경로가 발견되지 않았습니다."
            echo "" > "results/${safe_domain}_linkfinder.txt"
        fi
    else
        echo "  -> [패스] 오프라인 분석을 진행할 실물 파일이 존재하지 않습니다."
        echo "" > "results/${safe_domain}_linkfinder.txt"
    fi
}

export -f scan_jsluice
echo "[*] 오프라인 jsluice 분석 매트릭스를 가동합니다..."
xargs -P 10 -n 1 -a "$TARGET_FILE" -I {} bash -c 'scan_jsluice "{}"'

rm -f targets_group*
