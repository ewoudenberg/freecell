while read i ; do game=$(echo $i | sed -e 's/.*GAME //g'); echo $game $(./freecell-game.py -p $game 2>/dev/null |  wc );  done < failed.log  >failed_game_by_size.txt
