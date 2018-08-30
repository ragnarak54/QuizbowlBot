#example conversion script
folder=$1
for i in `seq 1 9`
do
	pdftotext $folder/2011CMST_Round0$i.pdf
	rm $folder/2011CMST_Round0$i.pdf
	mv $folder/2011CMST_Round0$i.txt $folder/round$i.txt
	echo pdf $i converted\n
done
