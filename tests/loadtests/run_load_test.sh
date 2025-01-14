#!/bin/bash

# Install vegeta if not already installed
# For MacOS: brew install vegeta
# For Linux: wget https://github.com/tsenart/vegeta/releases/download/v12.8.4/vegeta_12.8.4_linux_amd64.tar.gz

# Test 1: Constant rate - 10 requests per second for 30 seconds
echo "Running constant load test - 10 RPS for 30s..."
vegeta attack -rate=10 -duration=30s -targets=target.json | \
    tee results_constant.bin | \
    vegeta report

# Test 2: Step load - increasing from 1 to 20 RPS
echo "Running step load test..."
for rate in 1 5 10 15 20; do
    echo "Rate: $rate requests per second"
    vegeta attack -rate=$rate -duration=10s -targets=target.json | \
        tee results_step_${rate}.bin | \
        vegeta report
    sleep 2
done

# Test 3: Spike test - sudden burst of traffic
echo "Running spike test - 50 RPS for 5s..."
vegeta attack -rate=50 -duration=5s -targets=target.json | \
    tee results_spike.bin | \
    vegeta report

# Generate HTML report for all tests
echo "Generating HTML report..."
vegeta plot results_constant.bin > constant_load_plot.html
vegeta plot results_spike.bin > spike_test_plot.html

# Clean up binary files
rm *.bin

echo "Load test complete. Check the HTML reports for detailed analysis."