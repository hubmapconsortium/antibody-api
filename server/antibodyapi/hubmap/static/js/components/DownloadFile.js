import React from 'react';
import { SearchkitComponent } from "searchkit";

// https://roytuts.com/download-file-from-server-using-react/

// https://gitter.im/searchkit/searchkit?at=59768a50329651f46ebc8785
// You can access the searchkit object in anything that extends SearchkitComponent as this.searchkit.
class DownloadFile extends SearchkitComponent {

    constructor(props) {
        super(props);
    }

    downloadFilename = 'avr.csv';
    avr_file_as_url = true;

    downloadData = () => {
        // The last query...
        let query = JSON.parse(JSON.stringify(this.searchkit.currentSearchRequest.query));

        // Total results returned from the last query, and not the paged size results...
        query.size = parseInt(JSON.stringify(this.searchkit.results.hits.total.value));
        query.from = 0;
        console.info('this.searchkit.results: ', JSON.parse(JSON.stringify(this.searchkit.results)));

        // Only the columns that the user is viewing, and not all of the columns...
        var _source = [];
        csv_column_order.forEach((key) => {
            if (display[key] == 'table-cell') _source.push(key);
        })
        query._source = _source;
        if (this.avr_file_as_url && _source.includes('avr_pdf_filename')) {
            query._source = _source.concat('avr_pdf_uuid');
        }

        console.info('query string for .csv file data: ', query);

        //console.info('this.searchkit...', this.searchkit.currentSearchRequest.searchkit.history);
        // https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch
        fetch('_search', {
            method: 'POST',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.5',
                'Cache-Control': 'max-age=0',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(query)
        })
            .then(response => response.json())
            .then(data => {
                var lines = [];

                // header for .csv file...
                lines.push(_source.join(','));

                data.hits.hits.forEach(item => {
                    var line = [];
                    _source.forEach((key) => {
                        let item_source = item._source[key];
                        if (this.avr_file_as_url && key == 'avr_pdf_filename') {
                            item_source = assets_url + '/' + item._source['avr_pdf_uuid'] + '/' + item_source;
                            item_source = item_source.replace(/,/g, '%2C');
                        }
                        // so the right number of commas show up in the .csv file...
                        if (item_source.indexOf(',') > -1) {
                            item_source = '"' + item_source + '"'
                        }
                        line.push(item_source);
                    })
                    // data line for .csv file...
                    lines.push(line.join(','));
                })
                const linesString = lines.join("\n") + "\n";

                console.log('lines: ', linesString);

                const csv = new Blob([linesString], {type: 'text/plain'});
                const url = window.URL.createObjectURL(csv);
	            let a = document.createElement('a');
	            a.href = url;
	            a.download = this.downloadFilename;
	            a.click();
            })
            .catch((error) => {
                console.error('Error fetching antibodies:', error);
            });
    }

    render() {
        return (
            <div id="downloadfile">
                <button onClick={this.downloadData}
                        className={"button-placement"}>
                    Download Selected AVR Information as CSV
                </button>
                <p/>
            </div>
        )
    }
}

export default DownloadFile;
