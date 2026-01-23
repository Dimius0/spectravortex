markdown
# 🌀 SpectraVortex

Programming language for photonic computing. Write light-based programs!

## ✨ Features
- Declarative syntax for optical systems
- Physical correctness by design
- Compiles to simulations & hardware layouts
- Open source (MIT License)

## 🚀 Quick Start

1. Clone the repository:
git clone https://github.com/Dimius0/spectravortex.git
cd spectravortex

text

2. Run a simple example:
python main.py --test

text

## 📖 Example Program

Example `hello.svx` file:
photon laser = {
frequency: 193.414e12,
amplitude: 0.8,
phase: 0.0
}

program hello() {
print("Programming with light!")
}

text

## 🔧 Installation

Install dependencies:
pip install numpy

text

## 🧪 Quick Test

Run tests:
python main.py --test
python main.py --simulate
python main.py --interactive

text

## 📁 Project Structure

- `compiler/` - Language compiler
- `simulator/` - Optical simulation  
- `examples/` - Example programs
- `main.py` - Main entry point

## 🚀 Usage Examples

Compile a program:
python main.py --compile examples/hello_photon.svx

text

Run in interactive mode:
python main.py --interactive

text

## 🤝 Contributing

Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a Pull Request

## 📄 License

MIT License - see LICENSE file for details.
