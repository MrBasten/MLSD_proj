#!/usr/bin/env bash
#   Use this script to test if a given TCP host/port are available
#
#   Source: https://github.com/vishnubob/wait-for-it

set -e

TIMEOUT=15
QUIET=0
HOST=""
PORT=""
CMD=()

usage()
{
    echo "Usage: wait-for-it.sh host:port [-s] [-t timeout] -- command args..."
    echo "  -s | --silent                       Do not output any status messages"
    echo "  -t TIMEOUT | --timeout=TIMEOUT      Timeout in seconds, default is 15"
    echo "  -- COMMAND ARGS                     Execute command with args after the test finishes"
    exit 1
}

wait_for()
{
    local host=$1
    local port=$2
    local timeout=$3

    local start_ts=$(date +%s)
    while :
    do
        if nc -z "$host" "$port"; then
            if [ $QUIET -ne 1 ]; then
                echo "Service is available - $host:$port"
            fi
            break
        fi

        sleep 1
        local now=$(date +%s)
        local elapsed=$(( now - start_ts ))
        if [ $elapsed -ge $timeout ]; then
            echo "Timeout after waiting $timeout seconds for $host:$port"
            exit 1
        fi
    done
}

# Parse arguments
while [[ $# -gt 0 ]]
do
    case $1 in
        *:* )
            HOST=$(echo $1 | cut -d: -f1)
            PORT=$(echo $1 | cut -d: -f2)
            shift
            ;;
        -s | --silent )
            QUIET=1
            shift
            ;;
        -t )
            TIMEOUT="$2"
            shift 2
            ;;
        --timeout=* )
            TIMEOUT="${1#*=}"
            shift
            ;;
        -- )
            shift
            CMD=("$@")
            break
            ;;
        * )
            echo "Unknown argument: $1"
            usage
            ;;
    esac
done

if [[ -z "$HOST" || -z "$PORT" ]]; then
    echo "Error: you need to specify a host and port to test."
    usage
fi

# Wait for the host and port
wait_for "$HOST" "$PORT" "$TIMEOUT"

# Execute command if provided
if [[ ${#CMD[@]} -gt 0 ]]; then
    exec "${CMD[@]}"
fi
