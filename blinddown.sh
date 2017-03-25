echo "ON"
echo "This is flag Switch ON" > ~/script.flag
echo '1-1' |sudo python control.py -t 00:00:00:00:00:00 -c move_down
