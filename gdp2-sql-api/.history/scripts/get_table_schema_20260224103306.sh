#!/bin/bash

set -e

DEFAULT_HOST="10.144.26.39"
DEFAULT_PORT="3306"
DEFAULT_USER="root"
DEFAULT_PASS="MhxzKhl@dache"
DEFAULT_DB="yc_union"


usage() {
    echo "Usage: $0 [OPTIONS] <table_name>"
    echo ""
    echo "Extract table schema from MySQL database"
    echo ""
    echo "Options:"
    echo "  -h, --host HOST      Database host (default: $DEFAULT_HOST)"
    echo "  -P, --port PORT      Database port (default: $DEFAULT_PORT)"
    echo "  -u, --user USER      Database user (default: $DEFAULT_USER)"
    echo "  -p, --pass PASS      Database password (default: $DEFAULT_PASS)"
    echo "  -d, --database DB    Database name (default: $DEFAULT_DB)"
    echo "  -o, --output FILE    Output file (default: stdout)"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 base_dict"
    echo "  $0 -h localhost -u root -p password -d mydb my_table"
    echo "  $0 -o schema.json base_dict"
}

HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
USER="$DEFAULT_USER"
PASS="$DEFAULT_PASS"
DATABASE="$DEFAULT_DB"
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -P|--port)
            PORT="$2"
            shift 2
            ;;
        -u|--user)
            USER="$2"
            shift 2
            ;;
        -p|--pass)
            PASS="$2"
            shift 2
            ;;
        -d|--database)
            DATABASE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            TABLE_NAME="$1"
            shift
            ;;
    esac
done

if [ -z "$TABLE_NAME" ]; then
    echo "Error: table_name is required"
    usage
    exit 1
fi

MYSQL_CMD="mysql -h$HOST -P$PORT -u$USER -p$PASS $DATABASE"

echo "Extracting schema for table: $TABLE_NAME"
echo "Database: $DATABASE@$HOST:$PORT"
echo ""

DESCRIBE_OUTPUT=$($MYSQL_CMD -e "DESCRIBE $TABLE_NAME" 2>&1) || {
    echo "Error: Failed to describe table '$TABLE_NAME'"
    echo "$DESCRIBE_OUTPUT"
    exit 1
}

KEYS_OUTPUT=$($MYSQL_CMD -e "
    SELECT COLUMN_NAME, COLUMN_KEY
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = '$DATABASE' AND TABLE_NAME = '$TABLE_NAME'
" 2>&1) || {
    echo "Error: Failed to get keys for table '$TABLE_NAME'"
    echo "$KEYS_OUTPUT"
    exit 1
}

PRIMARY_KEYS=$(echo "$KEYS_OUTPUT" | awk 'NR>1 && $2=="PRI" {print $1}')

generate_json() {
    local table_name="$1"
    local database="$2"

    echo "{"
    echo "  \"table_name\": \"$table_name\","
    echo "  \"database\": \"$database\","
    echo "  \"columns\": ["

    local first=true
    echo "$DESCRIBE_OUTPUT" | tail -n +2 | while IFS=$'\t' read -r field type null key default extra; do
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi

        is_primary="false"
        for pk in $PRIMARY_KEYS; do
            if [ "$field" = "$pk" ]; then
                is_primary="true"
                break
            fi
        done

        nullable="false"
        if [ "$null" = "YES" ]; then
            nullable="true"
        fi

        default_value="null"
        if [ -n "$default" ]; then
            default_value="\"$default\""
        fi

        echo -n "    {"
        echo -n "\"name\": \"$field\", "
        echo -n "\"type\": \"$type\", "
        echo -n "\"nullable\": $nullable, "
        echo -n "\"key\": \"$key\", "
        echo -n "\"default\": $default_value, "
        echo -n "\"extra\": \"$extra\", "
        echo -n "\"is_primary\": $is_primary"
        echo -n "}"
    done

    echo ""
    echo "  ]"
    echo "}"
}

SCHEMA_JSON=$(generate_json "$TABLE_NAME" "$DATABASE")

if [ -n "$OUTPUT" ]; then
    echo "$SCHEMA_JSON" > "$OUTPUT"
    echo "Schema saved to $OUTPUT"
else
    echo "$SCHEMA_JSON"
fi