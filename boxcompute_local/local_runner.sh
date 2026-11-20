#!/bin/bash
# Mock BoxCompute Local Runner untuk OpenCode / JARVIS
# Meniru fungsi bxc runner menggunakan Docker tempatan

echo "=========================================="
echo " Starting Local BoxCompute Agent Runner"
echo "=========================================="
echo "Status: Connected to Local Docker Engine"
echo "Waiting for tasks or agent commands..."

while true; do
  docker ps --filter "label=com.boxcompute.sandbox" --format "{{.Names}} - {{.Status}}"
  sleep 10
done
