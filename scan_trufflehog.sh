#!/bin/bash
mkdir -p results
GROUP_SUFFIX=$1

split -d -n l/20 targets.txt targets_group
TARGET_FILE="targets_group${GROUP_SUFFIX}"

scan_truffle() {
    local raw_domain=$(echo "$1" | xargs)
    [[ -z "$raw_domain" || "$raw_domain" =~ ^# ]] && return

    # 와일드카드 매핑 파일명 식별
    local safe_domain="$raw_domain"
    if [[ "$raw_domain" == \** ]]; then
        safe_domain="wild_${raw_domain#\*.}"
    fi

    local download_dir="results/${safe_domain}_js_files"

    if [ -d "$download_dir" ] && [ "$(ls -A "$download_dir" 2>/dev/null)" ]; then
        echo "[+] [${raw_domain}] [2단계: TruffleHog] 파일 내부 기밀 정보(Secret) 유출 검사를 시작합니다..."
        
        trufflehog filesystem "$download_dir" --only-verified --json 2>/dev/null > "results/${safe_domain}_trufflehog_raw.json" || true
        
        if [ -s "results/${safe_domain}_trufflehog_raw.json" ]; then
            cat "results/${safe_domain}_trufflehog_raw.json" | jq -r '. | ((.SourceMetadata.Data.Filesystem.file // "unknown.js") | split("/") | last) + "\t[" + (.DetectorName // "Secret") + "] " + ((.Raw // "") | gsub("\n"; " "))' > "results/${safe_domain}_trufflehog.txt" || true
            rm -f "results/${safe_domain}_trufflehog_raw.json"
            echo "  -> [위험 징후 탐지!] 검증된 비밀키 유출 데이터가 텍스트에 매핑되었습니다."
        else
            echo "  -> [안전] 유출된 기밀 정보(API Key 등)가 없습니다."
            echo "" > "results/${safe_domain}_trufflehog.txt"
        fi
    else
        echo "" > "results/${safe_domain}_trufflehog.txt"
    fi
}

export -f scan_truffle
echo "[*] 오프라인 TruffleHog 스캔 매트릭스를 가동합니다..."
xargs -P 10 -n 1 -a "$TARGET_FILE" -I {} bash -c 'scan_truffle "{}"'

rm -f targets_group*
