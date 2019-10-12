#!/bin/bash

#
# PARAMS
#
if [[ $# -lt 3 ]] ; then
    echo 'Usage: ./wd-lite.sh recipe input output'
    exit 1
fi

recipe="$1"
inputfile="$2"
outputfile="$3"


#
# CONFIG
#
echo "Reading configuration"

greplabelstring="/entity/Q[0-9]+> <http://schema.org/name>.*@"
grepdescriptionstring="/entity/Q[0-9]+> <http://schema.org/description>.*@"
grepaddprop="<http://www.wikidata.org/prop/direct/"
declare -a GREP_ARGS

# label
GREP_ARGS[${#GREP_ARGS[@]}]=$(yq r $recipe label | (while read p; do
    lang=$(echo $p | awk -F  " " '{print $3}')
    optional=$(echo $p | awk -F  " " '{print $4}')
done && echo "$greplabelstring$lang" ))

# description
GREP_ARGS[${#GREP_ARGS[@]}]=$(yq r $recipe description | (while read p; do
    lang=$(echo $p | awk -F  " " '{print $3}')
    optional=$(echo $p | awk -F  " " '{print $4}')
done && echo "$grepdescriptionstring$lang" ))

# predicate
GREP_ARGS[${#GREP_ARGS[@]}]=$(yq r $recipe predicate | (while read p; do
    operation=$(echo $p | awk -F  " " '{print $2}')
    prop=$(echo $p | awk -F  " " '{print $3}')
    optional=$(echo $p | awk -F  " " '{print $4}')
done && \
if [ "$operation" == "add" ]; then
    echo "${grepaddprop}${prop}>"
fi ))

# predicate-object
GREP_ARGS[${#GREP_ARGS[@]}]=$(yq r $recipe predicate-object | (while read p; do
    operation=$(echo $p | awk -F  " " '{print $2}')
    prop=$(echo $p | awk -F  " " '{print $3}')
    obj=$(echo $p | awk -F  " " '{print $4}')
    optional=$(echo $p | awk -F  " " '{print $5}')
done && \
if [ "$operation" == "add" ]; then
    echo "${grepaddprop}${prop}>"
fi ))

# TODO remove empty instructions

GREP_ARGS_FULL="grep -E "$(printf -- "-e \"%s\" " "${GREP_ARGS[@]}" | sort -u) #XXX uniq seems working in part
echo "$GREP_ARGS_FULL"

#
# FILTER
#
echo "Finding data"
time pigz -dc $inputfile | eval "$GREP_ARGS_FULL" | sort -S1G --parallel=8 -u > /tmp/utemp.nt


#
# CLEAN
#
echo "Cleaning"
findq='^<http:\/\/www.wikidata.org\/entity\/(Q[0-9]+)'
findname=' <http://schema.org/name> '
findP31=' <http://www.wikidata.org/prop/direct/P31> '
currentq=''
currentdata=''
haslabel=false
hasP31=false

while read p; do
    #find current Q
    #XXX can be done better with string split
    #thisq="$(echo $p | perl -pe 's|(.*)(Q[0-9]+)> <(.*)|\2|')" #sed -E  's/(.*)(Q[0-9]+)> <(.*)/\2/'
    if [[ $p =~ $findq ]]; then
        #check if new Q
        if [[ $currentq != ${BASH_REMATCH[1]} ]]; then
            #set new Q
            currentq=${BASH_REMATCH[1]};
            #echo $currentq

            #print previous if necessary
            if [ $haslabel == true ] && [ $hasP31 == true ]; then
                echo -e $currentdata >> $outputfile
            fi

            #clean vars
    		  	currentdata=''
    			  haslabel=false
    			  hasP31=false
        fi

    		#get property switch case
    		if [[ $p == *$findname* ]]; then
    		  	haslabel=true
    		elif [[ $p == *$findP31* ]]; then
    		  	hasP31=true
    		fi

    		#save data
    		currentdata="$currentdata$p\n"
    fi
done < /tmp/utemp.nt

rm /tmp/utemp.nt
