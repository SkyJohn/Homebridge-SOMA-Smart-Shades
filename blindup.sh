echo "OFF"
rm ~/script.flag
echo '1-1' |sudo python control.py -t 00:00:00:00:00:00 -c move_up
