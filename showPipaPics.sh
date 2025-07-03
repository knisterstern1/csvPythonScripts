#!/bin/bash
#start:special option edit {{{1
##--edit: special option edit
if [[ `echo $@ | grep '[-][-]edit'` != "" ]];then
   vi -s ~/bin/bin.vim $0
   exit $?
fi
##--log: special option log
if [[ `echo $@ | grep '[-][-]log'` != ""  ]];then
   if [[ -e ${0/sh/log} ]];then
      tail ${0/sh/log}
   else
      echo "File ${0/sh/log} is empty!"
   fi
   exit 0
fi
#end:special option edit 1}}}
logFile=${0/sh/log}
function printLog () { #{{{1
   echo "$(date)  % $@" >> $logFile
} #1}}}
function usage () { #{{{1
   echo "Usage: `basename $0` csvFile" 
   grep '^##[-]' $0
   exit $1
} 
##--help,-h: show help
if [[ `echo $@ | grep '\(^[-]h$\|[-][-]help\)'` != "" ]];then
      usage 0
fi
#1}}}
function processLineFirst () { #{{{1
   i=$1
   if [[ $i -gt 1 ]];then
         pipaId=$(sed -n ''"$i"' p' < $file | awk -F"," '{ print $1 }')
         picName=$(sed -n ''"$i"' p' < $file | awk -F"," '{ print $2 }')
         category=$(sed -n ''"$i"' p' < $file | awk -F"," '{ print $3 }')
         id=$(sed -n ''"$i"' p' < $file | awk -F"," '{ print $4 }')
         url="https://kumu.picturepark.com/contents/mediaLibrary?filters=%5B%7B%22aggregationName%22:%22objectInformation.objects.objectId%22,%22filter%22:%7B%22path%22:%22objectInformation.objects%22,%22filter%22:%7B%22field%22:%22objectInformation.objects.objectId%22,%22term%22:%22${id}%22,%22kind%22:%22TermFilter%22%7D,%22kind%22:%22NestedFilter%22%7D,%22kind%22:%22AggregationFilter%22%7D%5D&sort=%5B%7B%22field%22:%22basicInformation.creationDate%22,%22direction%22:%22Asc%22%7D%5D&searchMode=and&searchType=MetadataAndFullText&view=thumbnail-medium&fields=" 
         firefox $url &
         read -p "Is ${picName} a detail? [y/N/?]" answer
         if [[ "$answer" ]];then
            if [[ "$answer" == "y" ]];then
               sed -n ''"$i"' p' < $file >> $output
            else 
               echo "$pipaId,$picName,$answer,$id" >> $output
            fi
         else
            newPicName=$(echo $picName | sed 's/\([a-z]\)\(2\)\(.*\)/\11\3/')
            newCategory=1
            echo "$pipaId,$newPicName,$newCategory,$id" >> $output
         fi
      fi
} #1}}}
function processLine () { #{{{1
   i=$1
   if [[ $i -gt 1 ]];then
         pipaId=$(sed -n ''"$i"' p' < $file | awk -F"," '{ print $1 }')
         picName=$(sed -n ''"$i"' p' < $file | awk -F"," '{ print $2 }')
         category=$(sed -n ''"$i"' p' < $file | awk -F"," '{ print $3 }')
         id=$(sed -n ''"$i"' p' < $file | awk -F"," '{ print $4 }')
         url="https://kumu.picturepark.com/contents/mediaLibrary/${pipaId}/metadata" 
         firefox $url &
         read -p "Is ${picName} change Auflicht (VIS) to [s/d/u/i/r/m/p/x/?]" answer
         if [[ "$answer" ]];then
            if [[ "$answer" == "?" ]];then
               sed -n ''"$i"' p' < $file >> $unsure
            else 
               newPicName=$(echo $picName | sed 's/\(kw1\)\(a\)\(.*\)/\1'"${answer}"'\3/')
               echo "$pipaId,$newPicName,$category,$id" >> $output
            fi
         else
            sed -n ''"$i"' p' < $file >> $output
         fi
      fi
} #1}}}
file=$1
output="Processed_${file}"
unsure="Unsure_${file}"
if [[ -e $output ]];then
   lastLine=$(sed -n '=' < $output | tail -1) 
   if [[ "$lastLine" ]];then
      startIndex=$(($lastLine + 1))
      for i in $(sed -n ''"$startIndex"', $ =' < $file);do
         processLine $i
      done
   fi
else 
   head -1 $file > $output
   for i in $(sed -n '=' < $file);do
      processLine $i 
   done
fi
