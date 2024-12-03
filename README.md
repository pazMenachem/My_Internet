# My_Internet 🌐

A powerful network filtering solution that combines kernel-level packet inspection with user-friendly controls for managing internet access and content filtering.

## 🌟 Features

- **Ad Blocking**: Advanced ad filtering at the network level
- **Adult Content Filtering**: Family-friendly internet browsing
- **Domain Management**: Easy-to-use interface for managing blocked domains
- **Kernel-Level Filtering**: High-performance packet inspection
- **Real-Time Updates**: Instant application of filtering rules
- **User-Friendly GUI**: Simple interface for managing all features

## 🔧 Upcoming Features

- **Site Block Notifications** 🔔: 
  - Real-time Telegram notifications when sites are blocked
  - Detailed blocking events with timestamps

## 🔧 System Requirements

- Linux-based operating system
- Python 3.8 or higher
- GCC compiler
- Make build system
- Root/sudo privileges for kernel module operations

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/My_Internet.git
cd My_Internet
```

2. Run the installation script:
```bash
sudo ./scripts/install.sh
```

### Starting the Application

1. Activate the system:

```bash
sudo ./scripts/activate.sh
```

2. The GUI will automatically launch and you can start managing your internet filtering settings.

### Stopping the Application

```bash
sudo ./scripts/deactivate.sh
```

## 🏗️ Architecture

The system consists of three main components:

1. **Kernel Module**: 
   - Handles packet inspection
   - Implements domain filtering
   - Manages DNS request interception

2. **Server**: 
   - Manages filtering rules
   - Handles domain list updates
   - Coordinates between GUI and kernel module

3. **Client GUI**: 
   - User interface for system control
   - Real-time status updates
   - Domain management interface

## 🛠️ Development Setup

1. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install development dependencies:

```bash
pip install -r requirements.txt
```

3. Install the package in development mode:

```bash
pip install -e .
```

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

## 📝 Configuration

The system can be configured through:
- `client/config.json`: Client-side settings
- Kernel module parameters (see documentation)
- Server configuration files

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🔍 Troubleshooting

Common issues and solutions:

1. **Kernel Module Loading Failed**
   - Ensure you have the correct kernel headers installed
   - Check kernel logs: `dmesg | grep Network_Filter`

2. **GUI Not Starting**
   - Verify Python dependencies are installed
   - Check application logs in `client_logs/`

3. **Filtering Not Working**
   - Verify the kernel module is loaded: `lsmod | grep Network_Filter`
   - Check server status and logs

## 🔐 Security

- The system requires root privileges for kernel module operations
- All network traffic is processed locally
- No data is sent to external servers

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Paz Menachem  - [Github](https://github.com/pazmenachem)
- Yoaz Sabag    - [Github](https://github.com/yoaz11)

## 🙏 Acknowledgments

- Linux Kernel Development Community
- Python Networking Libraries Contributors
- Mom and Dad

---

<p align="center">Made with ❤️ for a safer internet</p>