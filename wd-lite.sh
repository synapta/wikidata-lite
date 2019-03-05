#!/bin/bash

# scarica https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.nt.gz
# trova label it
# trova description it
# trova P31
# filtra Q giuste

echo "Finding data"
time pigz -dc wd-nt.gz | grep -E -e "entity/Q[0-9]+> <http://schema.org/name>.*@it" \
                                 -e "Q[0-9]+> <http://schema.org/description>.*@it" \
                                 -e "<http://www.wikidata.org/prop/direct/P31>" >> temp.nt

echo "Sorting"
time sort -u temp.nt > utemp.nt

echo "Cleaning"
findq='^<http:\/\/www.wikidata.org\/entity\/(Q[0-9]+)'
findname=' <http:\/\/schema.org\/name> '
findP31=' <http:\/\/www.wikidata.org\/prop\/direct\/P31> '
currentq=''
currentdata=''
haslabel=false
hasP31=false


while read p; do
    #find current Q
    if [[ $p =~ $findq ]]; then #XXX can be done better with string split
        #check if new Q
        if [[ $currentq != ${BASH_REMATCH[1]} ]]; then
            #set new Q
            currentq=${BASH_REMATCH[1]};
            #echo $currentq
            
            #print previous if necessary
            if [ $haslabel == true ] && [ $hasP31 == true ]; then 
                echo -e $currentdata >> output.nt
            fi
            
            #clean vars
			currentdata=''
			haslabel=false
			hasP31=false
        fi
        
		#get property switch case
		if [[ $p =~ $findname ]]; then
			haslabel=true
		elif [[ $p =~ $findP31 ]]; then
			hasP31=true
		fi

		#save data
		currentdata="$currentdata$p\n"
    fi
done < utemp.nt

rm temp.nt
rm utemp.nt


#<http://www.wikidata.org/entity/Q12746> <http://schema.org/name> "Canton San Gallo"@it .
#<http://www.wikidata.org/entity/Q12746> <http://schema.org/description> "cantone svizzero"@it .
#<http://www.wikidata.org/entity/Q12756> <http://www.wikidata.org/prop/direct/P31> <http://www.wikidata.org/entity/Q5> .
