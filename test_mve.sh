#!/bin/bash
# Test script for MVE Benchmark Runner
# This script demonstrates the different ways to use the MVE benchmark runner

echo "🧪 MVE Benchmark Runner Test Suite"
echo "==================================="

echo ""
echo "📋 1. Testing help output..."
python mve_benchmark.py --help | head -10

echo ""
echo "🔍 2. Testing dependency check..."
python mve_benchmark.py --check-deps

echo ""
echo "⚙️ 3. Testing argument validation (should show error)..."
python mve_benchmark.py --verbose 2>&1 | head -2

echo ""
echo "🎮 4. Example Luanti command (dry run):"
echo "python mve_benchmark.py luanti --nodes 2 --bots-per-node 50 --duration 90"

echo ""
echo "⛏️ 5. Example PaperMC command (dry run):"
echo "python mve_benchmark.py papermc --nodes 2 --bots-per-node 10 --duration 60"

echo ""
echo "🏗️ 6. Example Blockbot command (dry run):"
echo "python mve_benchmark.py luanti --bot-type blockbot --movement-mode tower --duration 120"

echo ""
echo "✅ Test suite completed!"
echo ""
echo "📝 To run actual benchmarks, you need:"
echo "   - DAS cluster access"
echo "   - Proper yardstick_benchmark configuration" 
echo "   - Node reservation permissions"
echo ""
echo "💡 Example production commands:"
echo "   python mve_benchmark.py luanti --bots-per-node 100 --duration 300"
echo "   python mve_benchmark.py papermc --nodes 3 --bots-per-node 25 --duration 180"
