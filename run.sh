#!/usr/bin/env bash
# Run one wildcard-attack experiment: ./run.sh fifo|priority|evict
set -e
MODE=${1:-priority}
DIR=$(cd "$(dirname "$0")" && pwd)

python3 "$DIR/fake_auth.py" --qps 100 --ttl 1 > /dev/null &
AUTH=$!
python3 "$DIR/resolver.py" --mode "$MODE" --client-window 10 --log > "$DIR/resolver_$MODE.log" &
RES=$!
trap 'kill $AUTH $RES 2>/dev/null' EXIT
sleep 1

echo "mode=$MODE"
python3 "$DIR/load.py" --clients 5 --client-qps 10 --bots 4 --bot-qps 100 \
    --warmup 15 --attack 20
