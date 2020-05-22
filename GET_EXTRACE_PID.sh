lsof $1  |tr -s ' '|cut -d' ' -f2|grep '^[0-9]'|xargs -n 2 -I % echo -e "ps -oppid= -p % | xargs -I {} ps -ocomm= -p {} |grep -q '^extrace$' && echo %"|bash
