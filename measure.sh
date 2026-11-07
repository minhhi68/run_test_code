#!/usr/bin/env bash
# Capture traffic on loopback while running one experiment, then print per-5s tables.
# Usage: ./measure.sh fifo|priority|evict
set -u
MODE=${1:?usage: ./measure.sh fifo|priority|evict}
DIR=$(cd "$(dirname "$0")" && pwd)
CAP=$HOME/cap_$MODE.pcap

# ask for the sudo password up front (a background sudo cannot prompt)
sudo -v

[ -d "$DIR/.venv" ] && source "$DIR/.venv/bin/activate"

sudo timeout 50 tcpdump -i lo -n -w "$CAP" 'udp port 5300 or udp port 5301' 2>/dev/null &
sleep 2
"$DIR/run.sh" "$MODE"
wait
ls -lh "$CAP"

for f in 'udp.dstport==5300 && ip.src<127.0.0.101' \
         'udp.dstport==5300 && ip.src>=127.0.0.101' \
         'udp.dstport==5301' \
         'udp.srcport==5301'; do
  echo "== $f"
  tshark -r "$CAP" -q -z "io,stat,5,$f"
done
