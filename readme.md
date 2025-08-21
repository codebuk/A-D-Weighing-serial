# Scale Reader Project Summary

## Project Overview
A web-based digital scale interface with multiple implementation approaches - complete browser-based solutions and Python utilities for serial communication.

### See /docs/SC-SE-IM_02.pdf to set 9600 baud 

## 🌐 **Web Browser Examples**

### **React CDN Version** (webserial-react-cdn.html)
- **Modern React Implementation** - Uses React 18 via CDN with Babel JSX transpilation
- **Component Architecture** - WeightChart component with Canvas visualization
- **Advanced Features** - Cookie-based port memory, auto-reconnection, 300-point data history
- **Smart Connection** - Automatic reconnection to previously used ports

### **Vanilla JavaScript Version** (serial_port_web.html)
- **Single File Solution** - No dependencies, runs entirely in browser
- **Class-based Architecture** - WeightChart and WebScaleReader classes
- **Configuration Presets** - Standard Scale, Alternate, RS232 quick setups

### **Common Features:**
- **📊 Live Weight Display** - 216px font with status colors (Green=Stable, Yellow=Unstable, Red=Error)
- **📈 Real-time Chart** - Canvas-based weight history visualization
- **⚙️ Serial Configuration** - Full control over baud rate, data bits, parity, stop bits
- **🧪 Test Mode** - Hardware-free simulation for development
- **📝 Activity Logging** - Timestamped debug information
- **🔄 Auto-reconnection** - Remembers and reconnects to previously used ports

### **Enhanced React Features:**
- **🍪 Cookie Memory** - Saves last used port for seamless reconnection
- **🔄 getPorts() Integration** - Automatic connection to granted ports
- **📊 300 Data Points** - 3x chart resolution for detailed weight tracking
- **🧹 Port Management** - Clear saved port preferences

### **Supported Scale Protocols:**
- `ST,+150.25 kg` (Stable weight)
- `US,+149.80 kg` (Unstable weight) 
- `I` (Instability/Idle indicator)
- `OL,+99999.99 kg` (Overload condition)
- `?` (Error response)

---

## 🐍 **Python Utilities** (websocket.py)

### **Serial Communication Backend** 
- **Threading Support** - Non-blocking serial data reading
- **Data Parsing** - Scale response format processing
- **Demo Mode** - Simulated scale data for testing

### **Core Functions:**
- `parse_scale_line()` - Converts raw scale responses to structured data
- `serial_reader_thread()` - Background serial port monitoring
- **Demo Data Generator** - Realistic weight fluctuations for testing

### **Note:** *WebSocket functionality has been removed - file now contains only serial utilities*

---

## 🔧 **Usage Scenarios**

### **React CDN Version:**
```bash
# Direct usage - open file in Chrome/Edge
file:///path/to/webserial-react-cdn.html

# Features auto-reconnection and port memory
# First use: Select port via picker
# Subsequent uses: Automatic connection
```

### **Vanilla JavaScript Version:**
```bash
# Direct usage - open file in Chrome/Edge
file:///path/to/serial_port_web.html

# Or serve locally for HTTPS
python -m http.server 8000
# Navigate to: http://localhost:8000/serial_port_web.html
```

### **Quick Start:**
1. **Test First** - Enable Test Mode → Start Reading (no hardware needed)
2. **Connect Scale** - Connect to Scale → Select port → Try presets if needed
3. **Read Data** - Start Reading for continuous weight monitoring
4. **Auto-reconnect** - Next time, connection happens automatically

---

## 📋 **Implementation Comparison**

| Feature | React CDN | Vanilla JS | Python Utilities |
|---------|-----------|------------|------------------|
| **Architecture** | React components | ES6 classes | Python functions |
| **Dependencies** | React 18 CDN | None | Python + serial |
| **Port Memory** | ✅ Cookie-based | ❌ Manual each time | N/A |
| **Auto-reconnect** | ✅ getPorts() | ❌ Manual selection | N/A |
| **Chart Resolution** | 300 points | 100 points | N/A |
| **UI Framework** | React JSX | Vanilla DOM | Backend only |
| **Browser Support** | Modern (Babel) | All modern | N/A |
| **File Size** | ~45KB | ~25KB | ~5KB |

---

## 🎯 **Best Use Cases**

### **React CDN Version:**
- **Production Environments** - Automatic reconnection reduces operator training
- **Kiosk Applications** - Seamless user experience with port memory
- **Quality Control** - High-resolution 300-point weight tracking
- **Lab/Research** - Detailed data collection with enhanced logging

### **Vanilla JavaScript Version:**
- **Legacy Systems** - Maximum browser compatibility
- **Simple Deployments** - No build process or dependencies
- **Educational** - Clear, readable code structure
- **Quick Prototyping** - Fast setup and modification

### **Python Utilities:**
- **Server Integration** - Backend scale communication
- **Data Processing** - Batch weight analysis
- **Custom Applications** - Building blocks for larger systems
- **Industrial Automation** - System integration components

---

## 🚀 **Recent Enhancements**

### **Smart Connection System:**
- **navigator.serial.getPorts()** - Checks for previously granted ports
- **Cookie-based Memory** - Remembers user's preferred scale
- **Graceful Fallbacks** - Shows picker only when needed
- **Port Identification** - Uses USB vendor/product IDs for matching

### **Enhanced Data Visualization:**
- **300-point History** - 3x more detailed weight tracking
- **Real-time Updates** - Sub-second data refresh
- **Status Color Coding** - Instant visual feedback
- **Responsive Design** - Works on desktop and mobile

### **Developer Experience:**
- **Test Mode** - Full simulation without hardware
- **Comprehensive Logging** - Detailed debugging information
- **Error Handling** - Clear troubleshooting messages
- **Configuration Options** - Easy serial parameter adjustment

The React CDN version represents the most advanced implementation with production-ready features, while the vanilla JavaScript version provides maximum compatibility and simplicity.