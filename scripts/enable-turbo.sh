#!/usr/bin/env bash
# Some laptops ship with Intel turbo boost disabled in the kernel tunable.
# This makes Roblox noticeably smoother, but raises temperatures. Temporary:
# the value resets after reboot. Run with sudo.
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "Run with sudo: sudo $0"; exit 1; }

if [[ ! -e /sys/devices/system/cpu/intel_pstate/no_turbo ]]; then
  echo "intel_pstate/no_turbo not present on this CPU (AMD or no intel_pstate)."
  exit 0
fi

before=$(cat /sys/devices/system/cpu/intel_pstate/no_turbo)
echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo
after=$(cat /sys/devices/system/cpu/intel_pstate/no_turbo)
max=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq 2>/dev/null || echo "?")
echo "no_turbo: $before -> $after, max freq: $max kHz"
echo "Resets on reboot. To undo now: echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo"
