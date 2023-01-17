#!/bin/bash

singleTargetFile=$1

files=`cat ipynb_FILES`

cat << EOF > __preprocess.py
from nbconvert.preprocessors import Preprocessor

class RemoveCellsWithNoTags(Preprocessor):

    def preprocess(self, notebook, resources):

        final_cells = []

        for cell in notebook.cells:

            loc = False
            if cell.metadata.get('tags'):
                ntop = None
                nbottom = None
                for tag in cell.metadata.get('tags'):
                    if tag.startswith('cut_output='):
                        loc = True
                        (ntop,nbottom) = map( int, tag.replace('cut_output=','').split('_') )

            if loc:
                for item in cell['outputs']:
                    if item['name'] == 'stdout':
                        final_text = ""

                        lines = item['text'].splitlines()
                        for i,line in enumerate(lines):
                            if i<ntop or i>=len(lines)-nbottom:
                                final_text += line+'\n'
                            if i==ntop:
                                final_text += '\n...\n\n'

                        item['text'] = final_text[:-1]

            final_cells.append(cell)

        notebook.cells = final_cells
        return notebook, resources
EOF

for file in $files
do
    fileName=${file##.*/}
    filePath=`echo $file | sed 's/\/'$fileName'//g'`

    [ -n "$singleTargetFile" -a "$fileName" != "$singleTargetFile" ] && continue

    # Converts the .ipynb to .py in its own directory
    $AMSBIN/amspython -m nbconvert --to script --no-prompt "${filePath}/${fileName}"
    sed -i '1,2d' "${filePath}/${fileName%.ipynb}".py
    sed -i '1s/^/# File automatically generated from '${fileName}'\n/' "${filePath}/${fileName%.ipynb}".py

    cp "${filePath}/${fileName}" .

    # Converts the .ipynb to rst in this directory
    $AMSBIN/amspython -m nbconvert --Exporter.preprocessors="__preprocess.RemoveCellsWithNoTags" --to rst ${fileName}
    mv ${fileName%.ipynb}.rst ${fileName%.ipynb}.rst.include
    sed -i 's#/.*/pyzacros/#/home/user/pyzacros/#g' "${fileName%.ipynb}.rst.include"

    rm ${fileName}
done

rm __preprocess.py
