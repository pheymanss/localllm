#!/bin/zsh
cd ${0:a:h}
./ladder.sh qwen3.5:4b-mtp-q4_K_M-64k
./ladder.sh mimo-v2.6:9b-48k
echo ALL DONE
