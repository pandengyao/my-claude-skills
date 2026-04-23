#!/usr/bin/env bash
# 最小 token 校验脚本：
# 输入 file:lines 列表 -> check(仅校验) -> 输出问题点(JSON)

set -euo pipefail

DEBUG=0

print_help() {
    cat <<'USAGE'
Usage:
  bash ./cosmic_token_check.sh [--debug|-d] "<file1:line1,line2;file2:line3>"

Notes:
  - 文件列表必须是一个字符串参数，文件之间用分号分隔
  - 每个文件必须带行号：file:line1,line2
  - 不带行号的条目会被忽略
  - 支持样式相关文件：.css .less .scss .sass .styl .san .vue
  - stdout 输出 JSON，debug 日志输出到 stderr
USAGE
}

debug_log() {
    if [[ "$DEBUG" -eq 1 ]]; then
        printf '[cosmic-token-check] %s\n' "$*" >&2
    fi
}

trim_text() {
    local s="$1"
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    printf '%s' "$s"
}

json_escape() {
    local s="$1"
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    s=${s//$'\n'/\\n}
    s=${s//$'\r'/\\r}
    s=${s//$'\t'/\\t}
    printf '%s' "$s"
}

json_string() {
    printf '"%s"' "$(json_escape "$1")"
}

join_json_items() {
    local out=""
    local item=""
    for item in "$@"; do
        [[ -z "$item" ]] && continue
        [[ -n "$out" ]] && out+=","
        out+="$item"
    done
    printf '%s' "$out"
}

is_style_file() {
    local p=""
    p="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
    case "$p" in
        *.css|*.less|*.scss|*.sass|*.styl|*.san|*.vue) return 0 ;;
        *) return 1 ;;
    esac
}

detect_platform() {
    local p=""
    p="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
    case "$p" in
        *.pc.*|*/pc/*|*_pc.*|*-pc.*) printf 'pc'; return 0 ;;
        *.wise.*|*/wise/*|*_wise.*|*-wise.*|*.mobile.*|*/mobile/*|*_mobile.*|*-mobile.*) printf 'mobile'; return 0 ;;
        *) printf 'pc'; return 0 ;;
    esac
}

run_command() {
    local -a cmd=("$@")
    local out_file=""
    local err_file=""
    local ec=0

    out_file="$(mktemp)"
    err_file="$(mktemp)"

    set +e
    "${cmd[@]}" >"$out_file" 2>"$err_file"
    ec=$?
    set -e

    CMD_EXIT="$ec"
    CMD_STDOUT="$(cat "$out_file")"
    CMD_STDERR="$(cat "$err_file")"

    rm -f "$out_file" "$err_file"
}

collect_issue_lines_text() {
    local text="$1"
    printf '%s\n' "$text" | grep -E '^[[:space:]]*\[(error|warn|info)\]' || true
}

lines_text_to_json_array() {
    local text="$1"
    local line=""
    local -a json_items=()

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        json_items+=("$(json_string "$line")")
    done <<< "$text"

    printf '[%s]' "$(join_json_items "${json_items[@]-}")"
}

sanitize_line_nums() {
    local raw="$1"
    local cleaned=""
    cleaned="$(printf '%s' "$raw" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -E '^[0-9]+$' || true)"
    if [[ -z "$cleaned" ]]; then
        printf ''
        return
    fi
    printf '%s\n' "$cleaned" | sort -n -u | paste -sd, -
}

filter_lines_by_changed_lines() {
    local text="$1"
    local changed_nums="$2"
    local line=""
    local line_no=""
    local num=""
    local matched=false
    local out=""
    local -a nums=()

    [[ -z "$changed_nums" ]] && { printf ''; return; }

    IFS=',' read -r -a nums <<< "$changed_nums"
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        line_no="$(printf '%s\n' "$line" | sed -nE 's/.*行号:[[:space:]]*([0-9]+).*/\1/p')"
        [[ -z "$line_no" ]] && continue

        matched=false
        for num in "${nums[@]-}"; do
            num="$(trim_text "$num")"
            [[ -z "$num" ]] && continue
            if [[ "$line_no" == "$num" ]]; then
                matched=true
                break
            fi
        done

        if [[ "$matched" == "true" ]]; then
            out+="$line"$'\n'
        fi
    done <<< "$text"

    printf '%s' "$out"
}

declare -a INPUT_ARGS=()
# 第1步：解析命令行参数。
# 只接受一个被引号包裹的 file:lines 字符串，支持 --debug/-d 输出调试日志。
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            print_help
            exit 0
            ;;
        -d|--debug)
            DEBUG=1
            shift
            ;;
        *)
            INPUT_ARGS+=("$1")
            shift
            ;;
    esac
done

if [[ ${#INPUT_ARGS[@]} -ne 1 ]]; then
    echo '{"status":"error","error":"File list must be one quoted string: file1:1,2;file2:3"}'
    exit 1
fi

FILE_SPEC_LIST="${INPUT_ARGS[0]}"
WORKSPACE="$(pwd)"

# 第2步：确定执行器。
if command -v npx >/dev/null 2>&1; then
    RUNNER_LABEL="npx cosmic"
    RUNNER_PREFIX=("npx" "cosmic")
else
    echo '{"status":"error","error":"npx is not available"}'
    exit 2
fi

debug_log "runner=$RUNNER_LABEL"

declare -a TARGET_FILES=()
declare -a TARGET_LINES=()

# 第3步：解析 file:lines 列表并归一化。
# 规则：
# - 仅处理带行号的条目（不带行号直接忽略）
# - 同一文件多次出现时合并行号
# - 行号做去重排序，便于后续按 diff 行过滤
declare -a specs=()
IFS=';' read -r -a specs <<< "$FILE_SPEC_LIST"

for spec in "${specs[@]-}"; do
    spec="$(trim_text "$spec")"
    [[ -z "$spec" ]] && continue

    if [[ "$spec" != *:* ]]; then
        debug_log "ignore_without_line_spec=$spec"
        continue
    fi

    file_part="$(trim_text "${spec%%:*}")"
    lines_part="$(trim_text "${spec#*:}")"
    [[ -z "$file_part" ]] && continue

    lines_part="$(sanitize_line_nums "$lines_part")"
    if [[ -z "$lines_part" ]]; then
        debug_log "ignore_invalid_lines_spec=$spec"
        continue
    fi

    abs_file="$file_part"
    [[ "$abs_file" != /* ]] && abs_file="$WORKSPACE/$abs_file"

    merged=false
    for i in "${!TARGET_FILES[@]}"; do
        if [[ "${TARGET_FILES[$i]}" == "$abs_file" ]]; then
            TARGET_LINES[$i]="${TARGET_LINES[$i]},$lines_part"
            merged=true
            break
        fi
    done

    if [[ "$merged" == "false" ]]; then
        TARGET_FILES+=("$abs_file")
        TARGET_LINES+=("$lines_part")
    fi
done

if [[ ${#TARGET_FILES[@]} -eq 0 ]]; then
    echo '{"status":"error","error":"No valid file:lines entries. Entries without line numbers are ignored."}'
    exit 1
fi

declare -a RESULTS=()

# 第4步：逐文件执行 token check。
# 先收集问题并按传入行号过滤。
for i in "${!TARGET_FILES[@]}"; do
    file="${TARGET_FILES[$i]}"
    changed_nums="$(sanitize_line_nums "${TARGET_LINES[$i]}")"

    rel_file="${file#$WORKSPACE/}"
    [[ "$rel_file" == "$file" ]] && rel_file="$file"

    platform="$(detect_platform "$file")"

    if [[ ! -f "$file" ]]; then
        RESULTS+=("{\"file\":$(json_string "$rel_file"),\"platform\":$(json_string "$platform"),\"lines\":$(json_string "$changed_nums"),\"issue_points\":[$(json_string "文件不存在")]}")
        continue
    fi

    if ! is_style_file "$file"; then
        RESULTS+=("{\"file\":$(json_string "$rel_file"),\"platform\":$(json_string "$platform"),\"lines\":$(json_string "$changed_nums"),\"issue_points\":[$(json_string "非样式文件，已跳过")]}")
        continue
    fi

    debug_log "check_file=$rel_file platform=$platform changed_nums=$changed_nums"

    check_cmd=("${RUNNER_PREFIX[@]}" "token" "check" "$file" "--platform" "$platform")
    run_command "${check_cmd[@]}"
    check_text="$CMD_STDOUT"$'\n'"$CMD_STDERR"

    if [[ "${CMD_EXIT:-0}" -ne 0 ]]; then
        # Note: non-zero exit can mean "check failed" (expected) OR tool runtime error.
        # Do not pollute `issue_points` with runtime errors; only expose them in debug logs.
        debug_log "check_exit=${CMD_EXIT} file=$rel_file platform=$platform"
        debug_log "stderr_head=$(printf '%s\n' \"$CMD_STDERR\" | head -n 5 | tr '\n' ' ' | sed 's/[[:space:]]\\+/ /g')"
    fi

    issue_lines_text="$(collect_issue_lines_text "$check_text")"
    issue_lines_text="$(filter_lines_by_changed_lines "$issue_lines_text" "$changed_nums")"
    if [[ "${CMD_EXIT:-0}" -ne 0 && -z "$issue_lines_text" ]]; then
        debug_log "no_issue_lines_matched=1 (tool may have crashed; rerun with --debug to inspect stderr)"
    fi
    issue_points_json="$(lines_text_to_json_array "$issue_lines_text")"

    RESULTS+=("{\"file\":$(json_string "$rel_file"),\"platform\":$(json_string "$platform"),\"lines\":$(json_string "$changed_nums"),\"issue_points\":$issue_points_json}")
done

# 第5步：输出最终 JSON。
echo '{'
echo "  \"results\": [$(join_json_items "${RESULTS[@]-}")]"
echo '}'
