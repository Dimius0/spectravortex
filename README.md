# 🌀 SpectraVortex

Programming language for photonic computing. Write light-based programs!

## ✨ Features
- Declarative syntax for optical systems
- Physical correctness by design
- Compiles to simulations & hardware layouts
- Open source (MIT License)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Dimius0/spectravortex.git
cd spectravortex

# Run a simple example
python examples/hello_photon.py
📖 Example Program
spectravortex
photon laser = {
    frequency: 193.414e12,  # 1550 nm
    amplitude: 0.8,
    phase: 0.0
}

program hello() {
    print("Programming with light!")
}
🔧 Installation
bash
pip install numpy  # Dependencies
🧪 Quick Test
bash
python main.py --test
python main.py --simulate
python main.py --interactive
📁 Project Structure
text
spectravortex/
├── compiler/           # Language compiler
│   ├── lexer.py       # Tokenizer
│   ├── parser.py      # Parser
├── simulator/         # Optical simulation
│   ├── field.py       # Optical fields
│   ├── elements.py    # Optical elements
├── examples/          # Example programs
├── main.py           # Main entry point
├── README.md         # This file
└── LICENSE           # MIT License
🚀 Usage Examples
Compile a program:
bash
python main.py --compile examples/hello_photon.svx
Run in interactive mode:
bash
python main.py --interactive
Run simulation:
bash
python main.py --simulate
🤝 Contributing
Contributions welcome!

Fork the repository

Create a feature branch

Make your changes

Submit a Pull Request

📄 License
MIT License - see LICENSE for details.
