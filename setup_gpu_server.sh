#!/bin/bash
# GPU Server Setup Script for KURE v1 API Gateway

echo "🚀 Setting up KURE v1 API Gateway on GPU Server"
echo "================================================"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  Running as root detected"
   echo "   Proceeding with root privileges (use with caution)"
   ROOT_USER=true
else
   ROOT_USER=false
fi

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 successful"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Check GPU availability
echo ""
echo "🔧 Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
    check_success "GPU detection"
else
    echo "⚠️  nvidia-smi not found. Please install NVIDIA drivers first."
    echo "   Visit: https://developer.nvidia.com/cuda-downloads"
fi

# Check Python version
echo ""
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "✅ Python version is compatible"
else
    echo "❌ Python 3.8+ required"
    exit 1
fi

# Check if conda is available
echo ""
echo "🔧 Checking Conda environment..."
if command -v conda &> /dev/null; then
    echo "✅ Conda is available"

    # Initialize conda for root if needed
    if [[ $ROOT_USER == true ]]; then
        echo "🔧 Initializing conda for root user..."
        conda init bash 2>/dev/null || true
        source ~/.bashrc 2>/dev/null || true
    fi

    # Create conda environment if it doesn't exist
    if conda env list | grep -q "ragnaforge"; then
        echo "✅ ragnaforge environment already exists"
        echo "🔄 Removing existing environment to ensure clean setup..."
        conda env remove -n ragnaforge -y
        echo "📦 Creating fresh ragnaforge conda environment..."
        conda create -n ragnaforge python=3.11 -y
        check_success "Conda environment creation"
    else
        echo "📦 Creating ragnaforge conda environment..."
        conda create -n ragnaforge python=3.11 -y
        check_success "Conda environment creation"
    fi

    echo "🔄 Activating ragnaforge environment..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate ragnaforge
    check_success "Environment activation"

else
    echo "⚠️  Conda not found. Using system Python with venv..."

    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        if [[ $ROOT_USER == true ]]; then
            python3 -m venv venv --system-site-packages
        else
            python3 -m venv venv
        fi
        check_success "Virtual environment creation"
    fi

    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
    check_success "Virtual environment activation"
fi

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
if [[ $ROOT_USER == true ]]; then
    pip install --upgrade pip --break-system-packages 2>/dev/null || pip install --upgrade pip
else
    pip install --upgrade pip
fi
check_success "Pip upgrade"

# Install PyTorch with CUDA support
echo ""
echo "🔥 Installing PyTorch with CUDA support..."
echo "   This may take a few minutes..."

# Detect CUDA version
if command -v nvcc &> /dev/null; then
    cuda_version=$(nvcc --version | grep "release" | sed 's/.*release \([0-9]\+\.[0-9]\+\).*/\1/')
    echo "   Detected CUDA version: $cuda_version"

    if [[ "$cuda_version" == "12."* ]]; then
        if [[ $ROOT_USER == true ]]; then
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --break-system-packages 2>/dev/null || pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        else
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        fi
    elif [[ "$cuda_version" == "11."* ]]; then
        if [[ $ROOT_USER == true ]]; then
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --break-system-packages 2>/dev/null || pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        else
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        fi
    else
        echo "⚠️  Unsupported CUDA version, installing CPU version"
        if [[ $ROOT_USER == true ]]; then
            pip install torch torchvision torchaudio --break-system-packages 2>/dev/null || pip install torch torchvision torchaudio
        else
            pip install torch torchvision torchaudio
        fi
    fi
else
    echo "⚠️  NVCC not found, installing CPU version"
    if [[ $ROOT_USER == true ]]; then
        pip install torch torchvision torchaudio --break-system-packages 2>/dev/null || pip install torch torchvision torchaudio
    else
        pip install torch torchvision torchaudio
    fi
fi
check_success "PyTorch installation"

# Install other requirements
echo ""
echo "📦 Installing other requirements..."
if [[ $ROOT_USER == true ]]; then
    pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt
else
    pip install -r requirements.txt
fi
check_success "Requirements installation"

# Verify PyTorch CUDA
echo ""
echo "🔍 Verifying PyTorch CUDA setup..."
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
else:
    print('⚠️  CUDA not available in PyTorch')
"

# Test sentence-transformers with GPU
echo ""
echo "🧪 Testing sentence-transformers GPU support..."
python3 -c "
try:
    from sentence_transformers import SentenceTransformer
    import torch

    if torch.cuda.is_available():
        print('✅ Testing GPU model loading...')
        # Test with a small model first
        model = SentenceTransformer('all-MiniLM-L6-v2')
        device = torch.device('cuda')
        model = model.to(device)

        # Test encoding
        test_text = ['GPU test sentence']
        embeddings = model.encode(test_text, device=device)
        print(f'✅ GPU encoding successful: {embeddings.shape}')
        print('✅ sentence-transformers GPU support verified')
    else:
        print('⚠️  CUDA not available for sentence-transformers')

except Exception as e:
    print(f'❌ sentence-transformers GPU test failed: {e}')
"

# Create optimized .env for GPU
echo ""
echo "⚙️  Creating GPU-optimized configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || echo "⚠️  .env.example not found"
fi

# Update .env with GPU-optimized settings
cat >> .env << EOF

# GPU Optimization Settings
MAX_BATCH_SIZE=64
OPTIMAL_BATCH_SIZE=64
GPU_MEMORY_FRACTION=0.8
CUDA_VISIBLE_DEVICES=0

# Performance Settings
WORKERS=1
MAX_SEQUENCE_LENGTH=512
TORCH_CUDNN_BENCHMARK=true
EOF

echo "✅ GPU-optimized configuration added to .env"

# Create GPU monitoring script
echo ""
echo "📊 Creating GPU monitoring script..."
cat > monitor_gpu.sh << 'EOF'
#!/bin/bash
# GPU Monitoring Script

echo "🖥️  GPU Monitoring for KURE v1 API"
echo "=================================="

while true; do
    clear
    echo "🖥️  GPU Monitoring - $(date)"
    echo "=================================="

    # GPU utilization
    nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | \
    while IFS=, read -r name util mem_used mem_total temp; do
        echo "GPU: $name"
        echo "  Utilization: ${util}%"
        echo "  Memory: ${mem_used}MB / ${mem_total}MB ($(( mem_used * 100 / mem_total ))%)"
        echo "  Temperature: ${temp}°C"
        echo ""
    done

    # Process information
    echo "🔄 GPU Processes:"
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader,nounits | \
    while IFS=, read -r pid name memory; do
        echo "  PID: $pid, Process: $name, Memory: ${memory}MB"
    done

    echo ""
    echo "Press Ctrl+C to stop monitoring"
    sleep 2
done
EOF

chmod +x monitor_gpu.sh
echo "✅ GPU monitoring script created (./monitor_gpu.sh)"

# Create performance test runner
echo ""
echo "🧪 Creating performance test runner..."
cat > run_gpu_test.sh << 'EOF'
#!/bin/bash
# GPU Performance Test Runner

echo "🚀 Running GPU Performance Test"
echo "==============================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Running as root - proceeding with caution"
    ROOT_USER=true
else
    ROOT_USER=false
fi

# Activate environment
if command -v conda &> /dev/null && conda env list | grep -q "ragnaforge"; then
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate ragnaforge
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "⚠️  KURE API server not running. Starting server..."
    python main.py &
    SERVER_PID=$!
    echo "🔄 Waiting for server to start..."
    sleep 10

    # Check again
    if ! curl -s http://localhost:8000/health > /dev/null; then
        echo "❌ Failed to start server"
        exit 1
    fi
    echo "✅ Server started successfully"
else
    echo "✅ Server is already running"
    SERVER_PID=""
fi

# Run GPU performance test
echo ""
echo "🧪 Running comprehensive GPU performance test..."
python tests/test_gpu_performance.py

# Cleanup
if [ ! -z "$SERVER_PID" ]; then
    echo ""
    echo "🔄 Stopping test server..."
    kill $SERVER_PID 2>/dev/null
fi

echo ""
echo "🎉 GPU Performance Test Completed!"
EOF

chmod +x run_gpu_test.sh
echo "✅ Performance test runner created (./run_gpu_test.sh)"

# Final instructions
echo ""
echo "🎉 GPU Server Setup Complete!"
echo "============================="
echo ""

if [[ $ROOT_USER == true ]]; then
    echo "⚠️  Root User Notice:"
    echo "- Running as root completed successfully"
    echo "- Consider creating a non-root user for production"
    echo "- Ensure proper file permissions for security"
    echo ""
fi

echo "📋 Next Steps:"
if [[ $ROOT_USER == true ]]; then
    echo "1. Activate environment:"
    if command -v conda &> /dev/null; then
        echo "   source $(conda info --base)/etc/profile.d/conda.sh"
        echo "   conda activate ragnaforge"
    else
        echo "   source venv/bin/activate"
    fi
    echo ""
fi

echo "1. Start the KURE API server:"
echo "   python main.py"
echo ""
echo "2. Run GPU performance test:"
echo "   ./run_gpu_test.sh"
echo ""
echo "3. Monitor GPU usage:"
echo "   ./monitor_gpu.sh"
echo ""
echo "4. Manual performance test:"
echo "   python tests/test_gpu_performance.py"
echo ""
echo "💡 Tips:"
echo "- Check GPU memory usage with: nvidia-smi"
echo "- Adjust batch size in .env for optimal performance"
echo "- Monitor temperature during heavy loads"
if [[ $ROOT_USER == true ]]; then
    echo "- Consider running API server as non-root user in production"
fi
echo ""
echo "🔧 Configuration files:"
echo "- .env: API and GPU settings"
echo "- requirements.txt: Python dependencies"
echo ""
echo "Happy testing! 🚀"
