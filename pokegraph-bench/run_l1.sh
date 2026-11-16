#!/bin/zsh
cd ${0:a:h}
./ladder_l1.sh qwen3.5:4b-mtp-q4_K_M-64k
./ladder_l1.sh mimo-v2.6:9b-48k
echo ALL DONE
