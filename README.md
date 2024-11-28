# OCR
Obstacle Race - lap counter

## Environment description
SportIdent(later SI) Reader ( Windows sw ) can be configured to save red items into the file.
It needs SI-reader or SI USB-dongle to read passing card's. The Sortident Active Card ( later SIAC) can be instructed to sent last data by Control point device like SI BaseStations example BS9 or BS11-LA. 

This SW reads file changes from the selected folder. When some file will change, the new added lines will be red from it. This works well for this or an files like log's, where new items will be added to the end of file.

SW start reading that selected folder/file when first change comes. Red lines are handled by software using Reader protocol, it calculate how many times each SIAC has passed through the dedicated number of the Control point. The Control point number or code can be changed from the settings.

The counter and card/competitor name and Stage counter and the lab counter are shown on the table view. The stage counter is like a devider. It is used to calculate how many stage an competor has done and at same when last pass of stage has done it reset the counter start from 1.

The cardName txt file is needed to combine competitor name to the card. If name can't be found from the file, the cardnumber with unknown text will be show on the countter table.
The last read item will be added/moved on the top of tableview for easier to found out.
The display to show the counters for running competitors should be big enough, example TV. The text size can be change by pressin Alt + or Alt -

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

