#!/bin/bash

## processes * input folders
while (($# > 0)); do
   folder=$(basename $1)
   shift
   items=$(echo ${folder}/*.lod | tr ' ' '\n' | wc -l)
   completed=0
	## stages is percentage bar width in columns
	stages=$(( $(tput cols) - 40 ))
	completed_stages=0
   ## print initial percentage
      printf "\rprocessing '%s' [" ${folder}
      printf "."
      for i in $(seq $((completed_stages+2)) ${stages}); do
         printf " "
      done
      printf "]"
   ## get initial header out of any .lod file into the temp
      for lodfile in ${folder}/*.lod; do
         head -n 1 ${lodfile} > ${folder}.lod
         break
      done
   for lodfile in $folder/*.lod; do
      tail -n +2 ${lodfile} | awk 'NR == 1 || NR % 50 == 0' >> ${folder}.lod
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
done
