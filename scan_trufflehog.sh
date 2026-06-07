#!/bin/bash
mkdir -p results
GROUP_SUFFIX=$1

split -d -n l/4 targets.txt targets_group
TARGET_FILE="targets_group${GROUP_SUFFIX}"

scan_truffle() {
    local domain=$(echo "$1" | xargs)
    [[ -z "$domain" || "$domain" =~ ^# ]] && return

    local download_dir="results/${domain}_js_files"

    # 선행 다운로드된 로컬 소스코드가 있을 때만 보안 스캔 진행
    if [ -d "$download_dir" ] && [ "$(ls -A "$download_dir" 2>/dev/null)" ]; then
        echo "[+] [$domain] [Stage 2: TruffleHog Offline Worker] Scanning verified secrets on $(ls "$download_dir" | wc -l) files..."
        trufflehog filesystem "$download_dir" --only-verified --plain 2>/dev/null > "results/${domain}_trufflehog.txt" || true
    else
        echo "  -> [$domain] No local JS assets available for TruffleHog scanning."
        echo "" > "results/${domain}_trufflehog.txt"
    fi
}

export -f scan_truffle
echo "[*] Launching Stage 2 Offline TruffleHog Analyzer Matrix for $TARGET_FILE..."
xargs -P 10 -n 1 -a "$TARGET_FILE" -I {} bash -c 'scan_truffle "{}"'

rm -f targets_group*
