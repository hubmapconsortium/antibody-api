import React from 'react';

// https://roytuts.com/download-file-from-server-using-react/
class DownloadFile extends React.Component {

    constructor(props) {
        super(props);
    }

    downloadFilename = 'avr.csv';

    downloadData = () => {
        console.info('display: ', display);
        // https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch
        fetch('/antibodies')
            .then(response => response.json())
            .then(data => {
                //console.log('data.antibodies: ', data.antibodies)
                var lines = [];

                var columnsToSave = [];
                const keys = Object.keys(display);
                keys.forEach((k, i) => {
                    if (display[k] == 'table-cell') {
                        columnsToSave.push(k);
                    }
                })
                var headerString = columnsToSave.join(',');
                lines.push(headerString);
                console.log('csv header: ', headerString);

                data.antibodies.forEach(item => {
                    //console.log('item: ', item);
                    var line = [];
                    columnsToSave.forEach(function (key, index) {
                        line.push(item[key]);
                    });
                    var lineString = line.join(',');
                    console.log('item line: ', lineString);
                    lines.push(lineString);
                })
                var linesString = lines.join("\n") + "\n";
                console.log('lines: ', linesString);

                var csv = new Blob([linesString], {type: 'text/plain'});
                let url = window.URL.createObjectURL(csv);
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
