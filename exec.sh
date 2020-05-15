#!/bin/bash
set -e
parser="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/parse_fork_report.py"
f=$(mktemp)
f1=$(mktemp)
f3=$(mktemp)
echo '#!/bin/bash -x' > $f
echo "$@" >> $f
chmod +x $f
cmd="command extrace -o $f1 -fltdu $f"

eval $cmd 2>$f3

cmd="$parser $f1"
>&2 echo $cmd
eval $cmd

[[ "$KEEP_TMP_FILES" ]] || unlink $f $f1 $f3
