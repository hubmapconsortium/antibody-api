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

    downloadData = () => {
        // The last query...
        let query = JSON.parse(JSON.stringify(this.searchkit.currentSearchRequest.query));

        // Total results returned from the last query, and not the paged size results...
        query.size = parseInt(JSON.stringify(this.searchkit.results.hits.total.value));

        // Only the columns that the user is viewing, and not all of the columns...
        var _source = [];
        csv_column_order.forEach((key) => {
            if (display[key] == 'table-cell') _source.push(key);
        })
        query._source = _source

        //console.info('query string for .csv file data: ', JSON.stringify(query))

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

                lines.push(_source.join(','));

                data.hits.hits.forEach(item => {
                    var line = []
                    _source.forEach((key) => {
                        line.push(item._source[key])
                    })
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
                console.error('Error fetching antibodies:', error)
            });
    }

    render() {
        return (
            <div id="downloadfile">
                <button onClick={this.downloadData}>Download Selected AVR Information as CSV</button>
                <p/>
            </div>
        )
    }
}

export default DownloadFile;
