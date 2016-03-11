#!/bin/bash

function cleanup() {
	tput cnorm
}

function ctrl_c() {
	cleanup
}

trap ctrl_c INT
tput civis
## processes * input folders
while (($# > 0)); do
   folder=$(basename $1)
   shift
   items=$(echo ${folder}/*.end | tr ' ' '\n' | wc -l)
   completed=0
	## stages is percentage bar width in columns
	completed_stages=0
   ## print initial percentage
      printf "\rprocessing '%s' [" ${folder}
      printf "."
		stages=$(( $(tput cols) - 24 - ${#folder} ))
      for i in $(seq $((completed_stages+2)) ${stages}); do
         printf " "
      done
      printf "]"
   ## get initial header out of any .lod file into the temp
      for file in ${folder}/*.end; do
         head -n 1 ${file} > ${folder}.ssv
         break
      done
   for file in $folder/*.end; do
      tail -n1 ${file} >> ${folder}.ssv
      completed=$((completed+1))
		new_completed_stages=$(( 100*${completed}*${stages}/(100*${items}) ))
		if (( $new_completed_stages != $completed_stages )); then
			completed_stages=$new_completed_stages
			## update percentage
			printf "\rprocessing '%s' [" ${folder}
			for i in $(seq 0 ${completed_stages}); do
				printf "."
			done
			for i in $(seq $((completed_stages+1)) ${stages}); do
				printf " "
			done
			printf "] %s%%" $(( 100*${completed}/${items} ))
		fi
   done
   printf "\n"
	zip -9 ${folder}.zip ${folder}.ssv > /dev/null
	rm ${folder}.ssv
done
cleanup
