const { SerialPort } = require('serialport');
const { ReadlineParser } = require('@serialport/parser-readline');

class ScaleReader {
    constructor(portPath = '/dev/ttyUSB0', baudRate = 9600) {
        this.portPath = portPath;
        this.baudRate = baudRate;
        this.port = null;
        this.parser = null;
        this.isReading = false;
    }

    async openSerial() {
        try {
            this.port = new SerialPort({
                path: this.portPath,
                baudRate: this.baudRate,
                dataBits: 7,
                parity: 'even',
                stopBits: 1,
                autoOpen: false
            });

            // Create a readline parser to handle CR/LF terminated responses
            this.parser = this.port.pipe(new ReadlineParser({ delimiter: '\r\n' }));
            
            return new Promise((resolve, reject) => {
                this.port.open((err) => {
                    if (err) {
                        reject(err);
                    } else {
                        console.log('Serial port opened.');
                        resolve();
                    }
                });
            });
        } catch (error) {
            throw new Error(`Failed to open serial port: ${error.message}`);
        }
    }

    sendCommand(command) {
        return new Promise((resolve, reject) => {
            if (!this.port || !this.port.isOpen) {
                reject(new Error('Serial port is not open'));
                return;
            }

            this.port.write(command + '\r\n', 'ascii', (err) => {
                if (err) {
                    reject(err);
                } else {
                    resolve();
                }
            });
        });
    }

    parseWeightResponse(response) {
        if (!response) {
            return { weight: null, unit: null, status: 'Error' };
        }

        try {
            if (response.startsWith('ST')) {
                const parts = response.split(',');
                const weightPart = parts[1].split(' ');
                const weight = parseFloat(weightPart[0]);
                const unit = weightPart[1];
                return { weight, unit, status: 'stable' };
            } 
            else if (response.startsWith('US')) {
                const parts = response.split(',');
                const weightPart = parts[1].split(' ');
                const weight = parseFloat(weightPart[0]);
                const unit = weightPart[1];
                return { weight, unit, status: 'unstable' };
            }
            else if (response.startsWith('I')) {
                console.log('Scale returns I.');
                return { weight: null, unit: null, status: 'unstable' };
            }
            else if (response.startsWith('?')) {
                console.log('Invalid command.');
                return { weight: null, unit: null, status: 'Error' };
            }
            else if (response.startsWith('OL')) {
                console.log('Overload condition.');
                return { weight: null, unit: null, status: 'overload' };
            }
            else {
                console.log('Unknown response:', response);
                return { weight: null, unit: null, status: 'Error' };
            }
        } catch (error) {
            console.log('Parse error:', error.message);
            return { weight: null, unit: null, status: 'Error' };
        }
    }

    async readWeight() {
        try {
            await this.sendCommand('Q');
            
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Timeout waiting for response'));
                }, 2000);

                this.parser.once('data', (data) => {
                    clearTimeout(timeout);
                    const response = data.toString().trim();
                    console.log('Raw response:', JSON.stringify(response));
                    
                    const result = this.parseWeightResponse(response);
                    resolve(result);
                });
            });
        } catch (error) {
            return { weight: null, unit: null, status: 'Error' };
        }
    }

    async startReading(interval = 1000) {
        if (this.isReading) {
            console.log('Already reading...');
            return;
        }

        this.isReading = true;
        console.log('Starting continuous reading...');

        while (this.isReading) {
            try {
                const result = await this.readWeight();
                
                if (result.weight !== null) {
                    console.log(`Weight: ${result.weight} ${result.unit} - Status: ${result.status}`);
                } else {
                    console.log(`Status: ${result.status}`);
                }
            } catch (error) {
                console.log('Read error:', error.message);
            }

            // Wait before next reading
            await new Promise(resolve => setTimeout(resolve, interval));
        }
    }

    stopReading() {
        this.isReading = false;
        console.log('Stopping reading...');
    }

    close() {
        this.stopReading();
        if (this.port && this.port.isOpen) {
            this.port.close((err) => {
                if (err) {
                    console.log('Error closing port:', err.message);
                } else {
                    console.log('Serial port closed.');
                }
            });
        }
    }
}

// Main execution
async function main() {
    const scaleReader = new ScaleReader('/dev/ttyUSB0', 9600);

    try {
        await scaleReader.openSerial();
        
        // Handle graceful shutdown
        process.on('SIGINT', () => {
            console.log('\nExiting...');
            scaleReader.close();
            process.exit(0);
        });

        // Start continuous reading
        await scaleReader.startReading(500); // Read every 500ms

    } catch (error) {
        console.log('Error:', error.message);
        scaleReader.close();
    }
}

if (require.main === module) {
    main();
}

module.exports = ScaleReader;