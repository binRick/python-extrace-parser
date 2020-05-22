#!/bin/bash
set +e
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
f="$1"
extrace_pid="$(./GET_EXTRACE_PID.sh "$f")"

cmd="./parse_fork_report.py '$f' '$extrace_pid'"
eval $cmd
