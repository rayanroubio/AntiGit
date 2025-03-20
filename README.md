# 🚀 Auto GitHub Uploader

A powerful and user-friendly Python script that allows you to upload entire folders to GitHub with a simple drag-and-drop interface. Perfect for quickly creating and populating GitHub repositories without dealing with Git commands.

![Auto GitHub Uploader](https://img.shields.io/badge/Auto-GitHub%20Uploader-blue?style=for-the-badge&logo=github)

## ✨ Features

- 🎯 **Simple Drag & Drop** - Just drag your folder onto the script to upload
- 🔐 **Secure Token Storage** - GitHub tokens are stored securely using system keyring
- ⚙️ **Configurable Settings** - Customize repository visibility, logging, and ignore patterns
- 📊 **Progress Tracking** - Real-time progress bar and detailed upload logs
- 🚫 **Smart Ignoring** - Supports .gitignore patterns and custom ignore rules
- 🔄 **Auto Retry** - Automatically retries failed uploads with exponential backoff
- 📁 **Directory Structure** - Automatically creates and maintains folder structure
- 💡 **User-Friendly Interface** - Beautiful ASCII art and emoji-rich console output

## 🛠️ Requirements

- Python 3.6 or higher
- Required packages:
  ```
  requests
  keyring
  tkinter (usually comes with Python)
  ```

## 📥 Installation

1. Clone or download this repository
2. Install required packages:
   ```bash
   pip install requests keyring
   ```
3. Run the script once to set up your GitHub token:
   ```bash
   python main.py
   ```

## 🔑 GitHub Token Setup

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate New Token"
3. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Optional: if you plan to use GitHub Actions)
4. Copy the generated token
5. Run the script and paste your token when prompted

## 📚 Usage

### Method 1: Drag and Drop
1. Simply drag a folder onto the `main.py` script
2. The script will create a new repository and upload all files

### Method 2: Command Line
```bash
python main.py "path/to/your/folder"
```

### Configuration Menu
Run without arguments to access the configuration menu:
```bash
python main.py
```

## ⚙️ Configuration Options

### Repository Settings
- Default visibility (public/private)
- Auto-use default visibility

### Logging Settings
- Detailed logs
- Progress bar display

### Ignore Settings
- node_modules ignoring
- .gitignore support
- Custom ignore patterns

## 🚫 Default Ignored Files
- .env files
- .DS_Store
- __pycache__
- *.pyc files
- node_modules (configurable)
- Custom patterns (configurable)

## ⚠️ Limitations

- Maximum file size: 50MB (GitHub API limitation)
- Rate limiting: The script handles GitHub API rate limits automatically
- Binary files: Some binary files might not upload correctly

## 🔒 Security

- Tokens are stored securely using the system's keyring
- No sensitive data is logged or stored in plain text
- All GitHub API communications use HTTPS

## 🐛 Troubleshooting

### Common Issues:
1. **Token Invalid**: Re-run the script without arguments to update your token
2. **Upload Failed**: Check file sizes and network connection
3. **Rate Limit**: The script will automatically wait for rate limits to reset

### Error Messages:
- ❌ "No GitHub token found" - Run the script without arguments to set up token
- ❌ "Repository already exists" - Choose a different folder name
- ⚠️ "File too large" - File exceeds GitHub's 50MB limit

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🌟 Credits

Created by Your Friendly AI Assistant 🤖

---

Made with ❤️ using Python 